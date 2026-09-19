import json
import os
import threading
import uuid
from typing import Any, Dict, Optional
import time

import httpx
from dotenv import load_dotenv

from models.referral import ReferralExtraction
from models.tinyfish_state import TinyFishAgentTrace, TinyFishEligibilityState, TinyFishLog
from services.tinyfish_run_store import tinyfish_run_store

load_dotenv()

TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY")
TINYFISH_BASE_URL = os.getenv("TINYFISH_BASE_URL", "https://agent.tinyfish.ai/v1")
MOCK_INSURANCE_URL = os.getenv("MOCK_INSURANCE_URL")
MOCK_ZIPCODES_URL = os.getenv("MOCK_ZIPCODES_URL")
MOCK_NURSES_URL = os.getenv("MOCK_NURSES_URL")
MOCK_PLACEMENT_URL = os.getenv("MOCK_INSURANCE_URL")  # reuse insurance site for now if needed


def _fallback_scheduling(referral: ReferralExtraction) -> dict:
    services = set(referral.services_required or [])
    zip_code = (referral.zip_code or "").strip()

    if "Skilled Nursing" in services or "PT" in services:
        nurse = "Sarah Nguyen, RN"
        slot = "Tomorrow 10:30 AM"
    elif "OT" in services:
        nurse = "Angela Brooks, OT"
        slot = "Tomorrow 9:00 AM"
    elif "ST" in services:
        nurse = "Kevin Ramirez, ST"
        slot = "Friday 10:00 AM"
    else:
        nurse = "Priya Menon, RN"
        slot = "Tomorrow 11:30 AM"

    return {
        "assigned_nurse": nurse,
        "scheduled_slot": slot,
        "call_initialized": True,
        "evidence": f"Fallback scheduling decision from local nurse roster for ZIP {zip_code or 'UNKNOWN'}.",
    }


def _tinyfish_headers() -> Dict[str, str]:
    if not TINYFISH_API_KEY:
        raise ValueError("Missing TINYFISH_API_KEY in environment.")
    return {
        "X-API-Key": TINYFISH_API_KEY,
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }

def _cancel_tinyfish_run(external_run_id: str) -> None:
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            f"{TINYFISH_BASE_URL}/runs/{external_run_id}/cancel",
            headers={
                "X-API-Key": TINYFISH_API_KEY,
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()


def _fallback_insurance_check(insurance_provider: Optional[str]) -> dict:
    accepted = {
        "aetna medicare",
        "humana gold plus",
        "unitedhealthcare medicare",
        "medicare",
        "medicaid",
        "blue cross blue shield ppo",
        "anthem blue cross",
        "anthem senior advantage",
        "wellcare medicare",
        "tricare east",
        "va community care",
        "uhc community plan",
    }
    payer = (insurance_provider or "").strip()
    ok = payer.lower() in accepted
    return {
        "payer_checked": payer or "UNKNOWN",
        "accepted": ok,
        "evidence": "Fallback decision from local accepted insurance dataset."
    }


def _fallback_zip_check(zip_code: Optional[str]) -> dict:
    serviceable = {
        "75001", "75006", "75007", "75019", "75024", "75025", "75034", "75035",
        "75039", "75040", "75041", "75042", "75044", "75048", "75052", "75056",
        "75201", "75202", "75203", "75204", "75205", "75206", "75208", "75209",
        "75211", "75214", "75220", "75224", "75227", "75228", "75229", "75231",
        "75234", "75235", "75238", "75243"
    }
    z = (zip_code or "").strip()
    ok = z in serviceable
    branch = "Dallas Central" if z in {
        "75201", "75202", "75203", "75204", "75205", "75206", "75208", "75209", "75220", "75235"
    } else None
    return {
        "zip_checked": z or "UNKNOWN",
        "serviceable": ok,
        "branch": branch,
        "evidence": "Fallback decision from local ZIP coverage dataset."
    }


def _add_log(state: TinyFishEligibilityState, message: str) -> None:
    state.logs.append(TinyFishLog(message=message))


def _update_agent(
    state: TinyFishEligibilityState,
    agent_id: str,
    *,
    status: Optional[str] = None,
    observation: Optional[str] = None,
    action: Optional[str] = None,
    append_update: Optional[str] = None,
    external_run_id: Optional[str] = None,
    streaming_url: Optional[str] = None,
) -> None:
    for agent in state.agents:
        if agent.id == agent_id:
            if status is not None:
                agent.status = status  # type: ignore
            if observation is not None:
                agent.observation = observation
            if action is not None:
                agent.action = action
            if append_update is not None:
                agent.updates.append(append_update)
            if external_run_id is not None:
                agent.external_run_id = external_run_id
            if streaming_url is not None:
                agent.streaming_url = streaming_url
            break


def _save(state: TinyFishEligibilityState) -> None:
    tinyfish_run_store.update_run(state)


def _normalize_progress_message(data: dict) -> str:
    if not isinstance(data, dict):
        return "TinyFish reported progress."
    return (
        data.get("purpose")
        or data.get("message")
        or data.get("text")
        or "TinyFish reported progress."
    )


def _consume_tinyfish_sse(
    *,
    state: TinyFishEligibilityState,
    agent_id: str,
    url: str,
    goal: str,
    max_seconds: int = 30,
) -> dict:
    started_at = time.time()
    external_run_id = None

    with httpx.Client(timeout=None) as client:
        with client.stream(
            "POST",
            f"{TINYFISH_BASE_URL}/automation/run-sse",
            headers=_tinyfish_headers(),
            json={
                "url": url,
                "goal": goal,
                "browser_profile": "lite",
            },
        ) as response:
            response.raise_for_status()

            current_event = None
            final_payload = None

            for raw_line in response.iter_lines():
                if time.time() - started_at > max_seconds:
                    if external_run_id:
                        _add_log(state, f"{agent_id} exceeded {max_seconds}s; cancelling TinyFish run.")
                        _cancel_tinyfish_run(external_run_id)
                    raise TimeoutError(f"{agent_id} TinyFish run exceeded {max_seconds} seconds.")

                if raw_line is None:
                    continue

                line = raw_line.strip()
                if not line:
                    continue

                if line.startswith("event:"):
                    current_event = line[len("event:"):].strip()
                    continue

                if not line.startswith("data:"):
                    continue

                data_str = line[len("data:"):].strip()

                try:
                    payload = json.loads(data_str)
                except json.JSONDecodeError:
                    payload = {"raw": data_str}

                event_type = current_event or payload.get("type") or "UNKNOWN"

                if event_type == "STARTED":
                    external_run_id = payload.get("run_id")
                    _update_agent(
                        state,
                        agent_id,
                        status="running",
                        action="TinyFish run started.",
                        append_update="Started remote browser automation.",
                        external_run_id=external_run_id,
                    )
                    if external_run_id:
                        _add_log(state, f"{agent_id} TinyFish run started: {external_run_id}")
                    _save(state)

                elif event_type == "STREAMING_URL":
                    streaming_url = payload.get("streaming_url")
                    _update_agent(
                        state,
                        agent_id,
                        append_update="Live browser streaming URL received.",
                        streaming_url=streaming_url,
                    )
                    _save(state)

                elif event_type == "PROGRESS":
                    msg = _normalize_progress_message(payload)
                    _update_agent(
                        state,
                        agent_id,
                        observation=msg,
                        action=msg,
                        append_update=msg,
                    )
                    _add_log(state, msg)
                    _save(state)

                elif event_type == "COMPLETE":
                    final_payload = payload
                    _update_agent(
                        state,
                        agent_id,
                        status="complete",
                        append_update="TinyFish run completed.",
                    )
                    _save(state)

                elif event_type == "HEARTBEAT":
                    continue

            if final_payload is None:
                raise RuntimeError("TinyFish SSE stream ended without COMPLETE event.")

            return final_payload


def _insurance_goal(referral: ReferralExtraction) -> str:
    insurance = referral.insurance_provider or "UNKNOWN"
    return f"""
Find whether payer "{insurance}" is accepted on this page.

Return ONLY valid JSON:
{{
  "payer_checked": "{insurance}",
  "accepted": true,
  "evidence": "short evidence from the page"
}}
""".strip()


def _zip_goal(referral: ReferralExtraction) -> str:
    zip_code = referral.zip_code or "UNKNOWN"
    return f"""
Find whether ZIP "{zip_code}" is serviceable on this page.

Return ONLY valid JSON:
{{
  "zip_checked": "{zip_code}",
  "serviceable": true,
  "branch": "branch name if found",
  "evidence": "short evidence from the page"
}}
""".strip()


def _placement_goal(referral: ReferralExtraction) -> str:
    patient = referral.patient_name or "UNKNOWN PATIENT"
    insurance = referral.insurance_provider or "UNKNOWN INSURANCE"
    zip_code = referral.zip_code or "UNKNOWN ZIP"
    services = ", ".join(referral.services_required or [])
    return f"""
Pretend this page is the referral intake acceptance portal.

Use the visible page and complete a placement-style workflow for:
Patient: {patient}
Insurance: {insurance}
ZIP: {zip_code}
Services: {services}

Return ONLY valid JSON:
{{
  "placement_submitted": true,
  "evidence": "short evidence from the page"
}}
""".strip()


def _scheduling_goal(referral: ReferralExtraction) -> str:
    zip_code = referral.zip_code or "UNKNOWN"
    services = ", ".join(referral.services_required or [])
    return f"""
Find one matching nurse and one available slot for:
ZIP: {zip_code}
Services: {services}

Return ONLY valid JSON:
{{
  "assigned_nurse": "name",
  "scheduled_slot": "slot string",
  "call_initialized": true,
  "evidence": "short evidence from page"
}}
""".strip()


def create_eligibility_run(
    *,
    document_run_id: str,
    referral: ReferralExtraction,
    insurance_provider_override: Optional[str] = None,
    zip_code_override: Optional[str] = None,
) -> TinyFishEligibilityState:
    if not MOCK_INSURANCE_URL or not MOCK_ZIPCODES_URL:
        raise ValueError("Missing MOCK_INSURANCE_URL or MOCK_ZIPCODES_URL in environment.")

    insurance_provider = insurance_provider_override or referral.insurance_provider
    zip_code = zip_code_override or referral.zip_code

    tinyfish_run_id = str(uuid.uuid4())

    state = TinyFishEligibilityState(
        tinyfish_run_id=tinyfish_run_id,
        document_run_id=document_run_id,
        status="queued",
        stage="eligibility",
        insurance_provider=insurance_provider,
        zip_code=zip_code,
        insurance_site=MOCK_INSURANCE_URL,
        zip_site=MOCK_ZIPCODES_URL,
        agents=[
            TinyFishAgentTrace(
                id="insurance",
                name="TinyFish Insurance Agent",
                status="queued",
                site=MOCK_INSURANCE_URL,
                goal="Verify the referral insurance is accepted by the home health agency.",
                observation="Waiting to start insurance lookup.",
                action="Queued.",
            ),
            TinyFishAgentTrace(
                id="zip",
                name="TinyFish ZIP Agent",
                status="queued",
                site=MOCK_ZIPCODES_URL,
                goal="Verify the patient ZIP code is inside the active service area.",
                observation="Waiting to start ZIP lookup.",
                action="Queued.",
            ),
        ],
        logs=[],
    )

    tinyfish_run_store.create_run(state)
    return state


def start_eligibility_run(
    *,
    tinyfish_run_id: str,
    referral: ReferralExtraction,
    insurance_provider_override: Optional[str] = None,
    zip_code_override: Optional[str] = None,
) -> None:
    thread = threading.Thread(
        target=_run_eligibility_workflow,
        args=(tinyfish_run_id, referral, insurance_provider_override, zip_code_override),
        daemon=True,
    )
    thread.start()


def _run_eligibility_workflow(
    tinyfish_run_id: str,
    referral: ReferralExtraction,
    insurance_provider_override: Optional[str],
    zip_code_override: Optional[str],
) -> None:
    state = tinyfish_run_store.get_run(tinyfish_run_id)
    if state is None:
        return

    try:
        state.status = "running"
        _add_log(state, "TinyFish eligibility workflow initialized.")
        _save(state)

        referral_copy = ReferralExtraction(**referral.model_dump())
        if insurance_provider_override:
            referral_copy.insurance_provider = insurance_provider_override
        if zip_code_override:
            referral_copy.zip_code = zip_code_override

        insurance_result_holder = {"payload": None, "error": None}
        zip_result_holder = {"payload": None, "error": None}

        def run_insurance():
            try:
                _update_agent(
                    state,
                    "insurance",
                    status="running",
                    observation=f"Preparing insurance lookup for {referral_copy.insurance_provider or 'UNKNOWN'}.",
                    action="Opening accepted insurance directory.",
                    append_update="Insurance workflow starting.",
                )
                _save(state)

                payload = _consume_tinyfish_sse(
                    state=state,
                    agent_id="insurance",
                    url=state.insurance_site,
                    goal=_insurance_goal(referral_copy),
                    max_seconds=15,
                )
                insurance_result_holder["payload"] = payload
            except TimeoutError:
                fallback = _fallback_insurance_check(referral_copy.insurance_provider)
                insurance_result_holder["payload"] = {
                    "status": "FALLBACK",
                    "result": fallback,
                    "num_of_steps": None,
                }
                _update_agent(
                    state,
                    "insurance",
                    status="complete",
                    observation=fallback["evidence"],
                    action="Applied local fallback insurance decision after timeout.",
                    append_update="Insurance fallback applied.",
                )
                _add_log(state, "Insurance TinyFish run timed out; local fallback used.")
                _save(state)
            except Exception as exc:
                insurance_result_holder["error"] = exc

        def run_zip():
            try:
                _update_agent(
                    state,
                    "zip",
                    status="running",
                    observation=f"Preparing ZIP lookup for {referral_copy.zip_code or 'UNKNOWN'}.",
                    action="Opening ZIP serviceability directory.",
                    append_update="ZIP workflow starting.",
                )
                _save(state)

                payload = _consume_tinyfish_sse(
                    state=state,
                    agent_id="zip",
                    url=state.zip_site,
                    goal=_zip_goal(referral_copy),
                    max_seconds=15,
                )
                zip_result_holder["payload"] = payload
            except TimeoutError:
                fallback = _fallback_zip_check(referral_copy.zip_code)
                zip_result_holder["payload"] = {
                    "status": "FALLBACK",
                    "result": fallback,
                    "num_of_steps": None,
                }
                _update_agent(
                    state,
                    "zip",
                    status="complete",
                    observation=fallback["evidence"],
                    action="Applied local fallback ZIP decision after timeout.",
                    append_update="ZIP fallback applied.",
                )
                _add_log(state, "ZIP TinyFish run timed out; local fallback used.")
                _save(state)
            except Exception as exc:
                zip_result_holder["error"] = exc

        insurance_thread = threading.Thread(target=run_insurance, daemon=True)
        zip_thread = threading.Thread(target=run_zip, daemon=True)

        insurance_thread.start()
        zip_thread.start()

        insurance_thread.join()
        zip_thread.join()

        if insurance_result_holder["error"]:
            raise insurance_result_holder["error"]
        if zip_result_holder["error"]:
            raise zip_result_holder["error"]

        insurance_payload = insurance_result_holder["payload"]
        zip_payload = zip_result_holder["payload"]

        insurance_result = insurance_payload.get("result") or {}
        zip_top_result = zip_payload.get("result") or {}
        if isinstance(zip_top_result.get("result"), dict):
            zip_result = zip_top_result["result"]
        else:
            zip_result = zip_top_result

        state.insurance_run = insurance_payload
        state.zip_run = zip_payload

        state.insurance_accepted = bool(insurance_result.get("accepted", False))
        state.serviceable_zip = bool(zip_result.get("serviceable", False))
        state.matched_branch = zip_result.get("branch")

        _update_agent(
            state,
            "insurance",
            observation=insurance_result.get("evidence", "Insurance lookup complete."),
            action=f"Checked payer {referral_copy.insurance_provider or 'UNKNOWN'} against accepted insurance page.",
            append_update="Insurance verification complete.",
        )

        _update_agent(
            state,
            "zip",
            observation=zip_result.get("evidence", "ZIP lookup complete."),
            action=f"Checked ZIP {referral_copy.zip_code or 'UNKNOWN'} against serviceability page.",
            append_update="ZIP verification complete.",
        )

        _add_log(state, "Insurance verification completed.")
        _add_log(state, "ZIP serviceability verification completed.")

        state.status = "complete"
        _add_log(state, "TinyFish eligibility workflow complete.")
        _save(state)

    except Exception as exc:
        state.status = "failed"
        state.error = str(exc)
        _add_log(state, f"TinyFish workflow failed: {exc}")
        _save(state)


def create_placement_run(
    *,
    document_run_id: str,
    referral: ReferralExtraction,
) -> TinyFishEligibilityState:
    if not MOCK_PLACEMENT_URL:
        raise ValueError("Missing MOCK_PLACEMENT_URL in environment.")

    tinyfish_run_id = str(uuid.uuid4())

    state = TinyFishEligibilityState(
        tinyfish_run_id=tinyfish_run_id,
        document_run_id=document_run_id,
        status="queued",
        stage="placement",
        placement_site=MOCK_PLACEMENT_URL,
        agents=[
            TinyFishAgentTrace(
                id="placement",
                name="TinyFish Placement Agent",
                status="queued",
                site=MOCK_PLACEMENT_URL,
                goal="Place the referral into the intake acceptance workflow.",
                observation="Waiting to start placement workflow.",
                action="Queued.",
            ),
        ],
        logs=[],
    )

    tinyfish_run_store.create_run(state)
    return state


def start_placement_run(
    *,
    tinyfish_run_id: str,
    referral: ReferralExtraction,
) -> None:
    thread = threading.Thread(
        target=_run_placement_workflow,
        args=(tinyfish_run_id, referral),
        daemon=True,
    )
    thread.start()


def _run_placement_workflow(
    tinyfish_run_id: str,
    referral: ReferralExtraction,
) -> None:
    state = tinyfish_run_store.get_run(tinyfish_run_id)
    if state is None:
        return

    try:
        state.status = "running"
        _add_log(state, "TinyFish placement workflow initialized.")
        _save(state)

        _update_agent(
            state,
            "placement",
            status="running",
            observation="Preparing referral placement using structured referral data.",
            action="Opening intake acceptance page.",
            append_update="Placement workflow starting.",
        )
        _save(state)

        placement_payload = _consume_tinyfish_sse(
            state=state,
            agent_id="placement",
            url=state.placement_site,
            goal=_placement_goal(referral),
        )

        placement_result = placement_payload.get("result") or {}
        state.placement_run = placement_payload
        state.placement_submitted = bool(placement_result.get("placement_submitted", False))

        _update_agent(
            state,
            "placement",
            observation=placement_result.get("evidence", "Placement workflow complete."),
            action="Submitted referral placement workflow.",
            append_update="Placement submission complete.",
        )
        _add_log(state, "Placement submission completed.")

        state.status = "complete"
        _add_log(state, "TinyFish placement workflow complete.")
        _save(state)

    except Exception as exc:
        state.status = "failed"
        state.error = str(exc)
        _add_log(state, f"TinyFish placement workflow failed: {exc}")
        _save(state)


def create_scheduling_run(
    *,
    document_run_id: str,
    referral: ReferralExtraction,
) -> TinyFishEligibilityState:
    if not MOCK_NURSES_URL:
        raise ValueError("Missing MOCK_NURSES_URL in environment.")

    tinyfish_run_id = str(uuid.uuid4())

    state = TinyFishEligibilityState(
        tinyfish_run_id=tinyfish_run_id,
        document_run_id=document_run_id,
        status="queued",
        stage="scheduling",
        nurses_site=MOCK_NURSES_URL,
        agents=[
            TinyFishAgentTrace(
                id="schedule",
                name="TinyFish Scheduling Agent",
                status="queued",
                site=MOCK_NURSES_URL,
                goal="Find a matching nurse, choose a slot, and initialize outreach.",
                observation="Waiting to start scheduling workflow.",
                action="Queued.",
            ),
        ],
        logs=[],
    )

    tinyfish_run_store.create_run(state)
    return state


def start_scheduling_run(
    *,
    tinyfish_run_id: str,
    referral: ReferralExtraction,
) -> None:
    thread = threading.Thread(
        target=_run_scheduling_workflow,
        args=(tinyfish_run_id, referral),
        daemon=True,
    )
    thread.start()


def _run_scheduling_workflow(
    tinyfish_run_id: str,
    referral: ReferralExtraction,
) -> None:
    state = tinyfish_run_store.get_run(tinyfish_run_id)
    if state is None:
        return

    try:
        state.status = "running"
        _add_log(state, "TinyFish scheduling workflow initialized.")
        _save(state)

        _update_agent(
            state,
            "schedule",
            status="running",
            observation="Preparing nurse matching and slot search.",
            action="Opening nurse roster page.",
            append_update="Scheduling workflow starting.",
        )
        _save(state)

        try:
            scheduling_payload = _consume_tinyfish_sse(
                state=state,
                agent_id="schedule",
                url=state.nurses_site,
                goal=_scheduling_goal(referral),
                max_seconds=15,
            )
        except TimeoutError:
            fallback = _fallback_scheduling(referral)
            scheduling_payload = {
                "status": "FALLBACK",
                "result": fallback,
                "num_of_steps": None,
            }
            _update_agent(
                state,
                "schedule",
                status="complete",
                observation=fallback["evidence"],
                action="Applied local fallback scheduling decision after timeout.",
                append_update="Scheduling fallback applied.",
            )
            _add_log(state, "Scheduling TinyFish run timed out; local fallback used.")
            _save(state)

        scheduling_result = scheduling_payload.get("result") or {}
        state.scheduling_run = scheduling_payload
        state.assigned_nurse = scheduling_result.get("assigned_nurse")
        state.scheduled_slot = scheduling_result.get("scheduled_slot")
        state.call_initialized = bool(scheduling_result.get("call_initialized", False))

        _update_agent(
            state,
            "schedule",
            observation=scheduling_result.get("evidence", "Scheduling workflow complete."),
            action="Matched nurse, selected slot, and initialized outreach.",
            append_update="Scheduling workflow complete.",
        )
        _add_log(state, "Scheduling workflow completed.")

        state.status = "complete"
        _add_log(state, "TinyFish scheduling workflow complete.")
        _save(state)

    except Exception as exc:
        state.status = "failed"
        state.error = str(exc)
        _add_log(state, f"TinyFish scheduling workflow failed: {exc}")
        _save(state)