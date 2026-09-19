# careflo.ai

Agentic referral intake for home health.

careflo.ai was built for a hackathon to show how home health agencies can move from messy hospital discharge packets to an intake-ready referral. The problem is operational: referrals often arrive as PDFs with missing or inconsistent data, and staff have to manually read the packet, extract patient details, verify payer and service area eligibility, place the referral, and start scheduling. That work is slow, repetitive, and easy to delay when packets are incomplete.

This project turns that process into an agentic workflow. A user can upload or run a sample referral PDF, watch document-processing agents extract and validate the referral, review the structured fields, and then hand the referral to browser agents that check eligibility and scheduling targets.

## What it does

- Ingests a home health referral PDF from the demo portal.
- Classifies the packet as digital, scanned, or mixed.
- Extracts text directly from digital PDFs and falls back to OCR for image-based pages.
- Uses an LLM to convert packet text into structured referral fields.
- Runs deterministic validation for demographics, contact data, ZIP format, and service normalization.
- Uses TinyFish browser agents to verify insurance acceptance and serviceable ZIP coverage.
- Continues into placement and scheduling workflows, including nurse/slot selection and outreach initialization.
- Shows live agent state, observations, actions, event logs, and final workflow outputs in the UI.

## Agentic workflow

The document pipeline is modeled as a set of traceable agents:

1. **OCR Agent** classifies the PDF and extracts page text.
2. **Document Parsing Agent** reconstructs page-aware document context.
3. **LLM Extraction Agent** extracts structured referral JSON.
4. **Demographics Validation Agent** checks identity fields.
5. **Contact Validation Agent** checks phone and ZIP quality.
6. **Clinical Services Agent** normalizes services such as PT, OT, ST, and Skilled Nursing.
7. **Cross-Field Validator** finalizes the referral object for downstream operations.

After document understanding, TinyFish agents run browser-based operational checks:

- **Insurance Agent** checks whether the payer is accepted.
- **ZIP Agent** checks service-area coverage and branch match.
- **Placement Agent** submits or simulates referral placement.
- **Scheduling Agent** matches the patient to a nurse and visit slot.

## Stack

**Frontend**

- React 19
- Vite
- React Router
- Tailwind CSS
- Framer Motion
- Lucide React

**Backend**

- FastAPI
- Uvicorn
- Pydantic
- PyMuPDF for PDF parsing, PDF classification, and OCR fallback
- OpenAI-compatible client pointed at Featherless for LLM extraction
- TinyFish API for browser automation agents
- HTTPX for SSE/browser-agent communication
- python-dotenv for local environment configuration

## Run locally

Start the backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env` with the API keys and local mock-page URLs:

```bash
FEATHERLESS_API_KEY=your_featherless_key
FEATHERLESS_BASE_URL=https://api.featherless.ai/v1
FEATHERLESS_MODEL=Qwen/Qwen2.5-7B-Instruct

TINYFISH_API_KEY=your_tinyfish_key
TINYFISH_BASE_URL=https://agent.tinyfish.ai/v1

MOCK_INSURANCE_URL=http://localhost:8000/mock/insurance.html
MOCK_ZIPCODES_URL=http://localhost:8000/mock/zipcodes.html
MOCK_NURSES_URL=http://localhost:8000/mock/nurses.html
```

Then run:

```bash
uvicorn app:app --reload --port 8000
```

Start the frontend in a second terminal:

```bash
npm install
npm run dev
```

Open the Vite URL, usually:

```text
http://localhost:5173
```

For the fastest demo path, use **Start Demo**, add/select the sample referral, run document processing, review the extracted fields, then continue through eligibility and scheduling.
