import { useNavigate, useParams } from "react-router-dom"
import PageShell from "../components/layout/PageShell"

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
      <div className="mt-2 text-sm text-white">{value}</div>
    </div>
  )
}

export default function ResultPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  return (
    <PageShell
      title="Extracted Referral Summary"
      subtitle="Structured intake data has been assembled, validated, and marked ready for placement."
      actions={
        <button
          onClick={() => navigate(`/schedule/${id}`)}
          className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          Initialize Patient Outreach & Scheduling
        </button>
      }
    >
      <div className="mb-6 rounded-3xl border border-emerald-400/20 bg-emerald-400/10 p-5 text-emerald-200">
        Referral placed successfully.
      </div>

      <div className="space-y-6">
        <Section title="Patient Demographics">
          <Field label="Patient Name" value="John Doe" />
          <Field label="MRN" value="MRN-483920" />
          <Field label="DOB" value="1948-02-14" />
          <Field label="Phone" value="(214) 555-0192" />
          <Field label="Address" value="123 Main St, Dallas, TX 75201" />
          <Field label="ZIP" value="75201" />
        </Section>

        <Section title="Referral & Insurance">
          <Field label="Hospital" value="Baylor Scott & White" />
          <Field label="Insurance Provider" value="Aetna Medicare" />
          <Field label="Eligibility Status" value="Eligible" />
          <Field label="Serviceability" value="Within Service Area" />
        </Section>

        <Section title="Clinical Requirements">
          <Field label="Services Required" value="PT, OT, Skilled Nursing" />
          <Field label="Primary Care Physician" value="Dr. Sarah Lee" />
          <Field label="Ordering Physician" value="Dr. James Carter" />
          <Field label="Readiness" value="Ready for Placement" />
        </Section>
      </div>
    </PageShell>
  )
}