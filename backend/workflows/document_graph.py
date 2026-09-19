import threading
import uuid

from models.workflow_state import AgentTrace, DocumentWorkflowState
from services.extraction_service import extract_referral_fields
from services.parser_service import parse_document
from services.pdf_classifier import classify_pdf
from services.pdf_text import extract_pdf_text
from services.run_store import run_store
from services.validation_service import validate_referral
from utils.logging_utils import add_log, update_agent


def build_initial_agents() -> list[AgentTrace]:
    return [
        AgentTrace(
            id="ocr",
            name="OCR Agent",
            status="queued",
            goal="Read the PDF and recover text from digital or scanned pages.",
            current_task="Waiting to inspect PDF type.",
            observation="No OCR/text extraction started yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="parser",
            name="Document Parsing Agent",
            status="queued",
            goal="Reconstruct packet text into structured document context.",
            current_task="Waiting for text extraction.",
            observation="No parsed sections yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="llm",
            name="LLM Extraction Agent",
            status="queued",
            goal="Extract structured referral fields from parsed document text.",
            current_task="Waiting for parsed sections.",
            observation="No extracted schema yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="demographics",
            name="Demographics Validation Agent",
            status="queued",
            goal="Validate patient identity fields.",
            current_task="Waiting for extracted fields.",
            observation="No validation yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="contact",
            name="Contact Validation Agent",
            status="queued",
            goal="Validate phone number and ZIP/address quality.",
            current_task="Waiting for extracted fields.",
            observation="No validation yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="clinical",
            name="Clinical Services Agent",
            status="queued",
            goal="Normalize extracted clinical services.",
            current_task="Waiting for extracted fields.",
            observation="No service normalization yet.",
            action="Queued.",
        ),
        AgentTrace(
            id="validator",
            name="Cross-Field Validator",
            status="queued",
            goal="Finalize a validated referral object.",
            current_task="Waiting for upstream outputs.",
            observation="No final validation yet.",
            action="Queued.",
        ),
    ]


def create_document_run(file_name: str, pdf_path: str) -> DocumentWorkflowState:
    run_id = str(uuid.uuid4())
    state = DocumentWorkflowState(
        run_id=run_id,
        file_name=file_name,
        pdf_path=pdf_path,
        status="queued",
        current_stage="queued",
        progress=0,
        agents=build_initial_agents(),
        logs=[],
    )
    run_store.create_run(state)
    return state


def start_document_workflow(run_id: str) -> None:
    thread = threading.Thread(target=_run_document_workflow, args=(run_id,), daemon=True)
    thread.start()


def _save(state: DocumentWorkflowState) -> None:
    run_store.update_run(state)


def _run_document_workflow(run_id: str) -> None:
    state = run_store.get_run(run_id)
    if state is None:
        return

    try:
        state.status = "running"
        state.current_stage = "classifying_pdf"
        state.progress = 1
        add_log(state, "Referral packet loaded into document processing workspace.")
        add_log(state, "Classifying PDF as digital, scanned, or mixed.")
        _save(state)

        meta = classify_pdf(state.pdf_path)
        state.document_type = meta["document_type"]

        update_agent(
            state,
            "ocr",
            status="running",
            current_task="Extracting text from PDF.",
            observation=f"Document classified as {state.document_type}.",
            action="Running direct extraction or OCR depending on page type.",
            append_update=f"PDF classified as {state.document_type}.",
        )
        add_log(state, f"PDF classified as {state.document_type}.")
        _save(state)

        extracted = extract_pdf_text(state.pdf_path, state.document_type)
        state.raw_text = extracted["merged_text"]

        update_agent(
            state,
            "ocr",
            status="complete",
            current_task="Text extraction complete.",
            observation="Page-wise text extraction finished successfully.",
            action="Publishing extracted text to parser.",
            append_update="Page text extraction complete.",
        )
        state.progress = 2
        state.current_stage = "parsing_document"
        add_log(state, "Text extraction complete. Starting document parsing.")
        _save(state)

        update_agent(
            state,
            "parser",
            status="running",
            current_task="Building parsed document sections.",
            observation="Page text available for parsing.",
            action="Constructing merged and page-aware document context.",
            append_update="Parsing started.",
        )
        parsed = parse_document(extracted)
        state.parsed_sections = parsed

        update_agent(
            state,
            "parser",
            status="complete",
            current_task="Parsing complete.",
            observation="Parsed page-aware document context created.",
            action="Sending parsed sections to extraction model.",
            append_update="Parsing complete.",
        )
        state.progress = 3
        state.current_stage = "llm_extraction"
        add_log(state, "Document parsing complete. Starting LLM extraction.")
        _save(state)

        update_agent(
            state,
            "llm",
            status="running",
            current_task="Extracting structured referral JSON.",
            observation="Parsed document context available.",
            action="Calling extraction model.",
            append_update="LLM extraction started.",
        )
        referral = extract_referral_fields(parsed, state.run_id)
        state.referral = referral

        update_agent(
            state,
            "llm",
            status="complete",
            current_task="Extraction complete.",
            observation="Structured referral JSON returned.",
            action="Publishing extracted fields to validators.",
            append_update="Structured extraction complete.",
        )
        state.current_stage = "field_validation"
        state.progress = 4
        add_log(state, "LLM extraction complete. Starting validation.")
        _save(state)

        for agent_id in ["demographics", "contact", "clinical"]:
            update_agent(
                state,
                agent_id,
                status="running",
                current_task="Validating extracted referral fields.",
                observation="Structured referral object available.",
                action="Applying deterministic validation rules.",
                append_update="Validation started.",
            )

        state.referral = validate_referral(state.referral)

        update_agent(
            state,
            "demographics",
            status="complete",
            current_task="Demographic validation complete.",
            observation="Identity fields checked for presence and consistency.",
            action="Marked demographic validation complete.",
            append_update="Demographic validation finished.",
        )
        update_agent(
            state,
            "contact",
            status="complete",
            current_task="Contact validation complete.",
            observation="Phone and ZIP structure checks completed.",
            action="Marked contact validation complete.",
            append_update="Contact validation finished.",
        )
        update_agent(
            state,
            "clinical",
            status="complete",
            current_task="Clinical normalization complete.",
            observation="Services normalized into canonical categories.",
            action="Marked clinical normalization complete.",
            append_update="Clinical normalization finished.",
        )

        update_agent(
            state,
            "validator",
            status="running",
            current_task="Running final cross-field validation.",
            observation="All upstream validation outputs available.",
            action="Finalizing referral object.",
            append_update="Cross-field validation started.",
        )
        update_agent(
            state,
            "validator",
            status="complete",
            current_task="Cross-field validation complete.",
            observation="Referral object finalized for downstream checks.",
            action="Marked document understanding complete.",
            append_update="Final validation complete.",
        )

        state.progress = 5
        state.current_stage = "document_understanding_complete"
        state.status = "complete"
        add_log(state, "Document understanding complete. Structured referral ready for operational checks.")
        _save(state)

    except Exception as exc:
        state.status = "failed"
        state.error = str(exc)
        add_log(state, f"Workflow failed: {exc}")
        _save(state)