import { useEffect, useState } from "react"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import PageShell from "../components/layout/PageShell"
import { getRun } from "../services/api"

function Section({ title, children }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
      <div className="mb-4 text-sm font-medium">{title}</div>
      <div className="grid gap-4 md:grid-cols-2">{children}</div>
    </div>
  )
}

function Field({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-4">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="mt-2 text-sm text-white">{value || "Not available"}</div>
    </div>
  )
}

export default function CompletePage() {
  const { id: runId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const schedulingResult = location.state?.schedulingResult

  const [documentRun, setDocumentRun] = useState(null)

  useEffect(() => {
    async function fetchDocumentRun() {
      const data = await getRun(runId)
      setDocumentRun(data)
    }
    fetchDocumentRun()
  }, [runId])

  return (
    <PageShell
      title="Referral Workflow Complete"
      subtitle="The referral has been extracted, checked, placed, and scheduled successfully."
      actions={
        <button
          onClick={() => navigate("/portal")}
          className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          Back to Portal
        </button>
      }
    >
      <div className="mb-6 rounded-3xl border border-emerald-400/20 bg-emerald-400/10 p-5 text-emerald-200">
        End-to-end workflow complete. Referral accepted and initial visit scheduled.
      </div>

      <div className="space-y-6">
        <Section title="Referral Intake Summary">
          <Field label="Patient Name" value={documentRun?.referral?.patient_name} />
          <Field label="MRN" value={documentRun?.referral?.mrn} />
          <Field label="Hospital" value={documentRun?.referral?.hospital_name} />
          <Field label="Diagnosis" value={documentRun?.referral?.diagnosis} />
        </Section>

        <Section title="Placement & Scheduling Summary">
          <Field label="Assigned Nurse" value={schedulingResult?.assigned_nurse} />
          <Field label="Visit Slot" value={schedulingResult?.scheduled_slot} />
          <Field label="Call Initialized" value={String(schedulingResult?.call_initialized)} />
          <Field label="Services Required" value={documentRun?.referral?.services_required?.join(", ")} />
        </Section>
      </div>
    </PageShell>
  )
}