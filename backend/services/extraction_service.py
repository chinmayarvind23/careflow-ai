import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from models.referral import ReferralExtraction

load_dotenv()

client = OpenAI(
    base_url=os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1"),
    api_key=os.getenv("FEATHERLESS_API_KEY"),
)


SYSTEM_PROMPT = """
You extract structured home health referral data from OCR/parsing output.

Rules:
- Return only valid JSON.
- Do not include markdown.
- If a field is missing, set it to null or [] as appropriate.
- Do not hallucinate.
- Use only evidence from the provided text.

Return this exact JSON schema:
{
  "patient_name": null,
  "mrn": null,
  "dob": null,
  "phone": null,
  "address": null,
  "zip_code": null,
  "hospital_name": null,
  "insurance_provider": null,
  "member_id": null,
  "services_required": [],
  "primary_care_physician": null,
  "ordering_physician": null,
  "diagnosis": null,
  "discharge_date": null,
  "missing_fields": [],
  "validation_notes": [],
  "field_confidence": {}
}
"""


def extract_referral_fields(parsed_sections: dict, run_id: str) -> ReferralExtraction:
    merged_text = parsed_sections["merged_text"]

    response = client.chat.completions.create(
        model=os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        temperature=0,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract referral fields from this document text:\n\n{merged_text}",
            },
        ],
    )

    content = response.choices[0].message.content.strip()

    data = json.loads(content)
    data["id"] = run_id

    return ReferralExtraction(**data)