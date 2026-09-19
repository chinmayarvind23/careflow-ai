import { useEffect, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
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

export default function ReviewPage() {
  const { id: runId } = useParams()
  const navigate = useNavigate()

  const [run, setRun] = useState(null)
  const [error, setError] = useState("")
  const [insuranceProvider, setInsuranceProvider] = useState("")
  const [zipCode, setZipCode] = useState("")

  useEffect(() => {
    async function fetchRun() {
      try {
        const data = await getRun(runId)
        setRun(data)
        setInsuranceProvider(data?.referral?.insurance_provider || "")
        setZipCode(data?.referral?.zip_code || "")
      } catch (err) {
        setError(err.message || "Failed to fetch extracted referral.")
      }
    }

    fetchRun()
  }, [runId])

  const referral = run?.referral

  function handleRunEligibility() {
    navigate(`/eligibility/${runId}`, {
      state: {
        insuranceProvider,
        zipCode,
      },
    })
  }

  return (
    <PageShell
      title="Structured Referral Review"
      subtitle="The document has been parsed, validated, and converted into structured operational fields."
      actions={
        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/processing/${runId}`)}
            className="rounded-xl border border-white/10 bg-zinc-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-zinc-800"
          >
            Back to Processing
          </button>
          <button
            onClick={handleRunEligibility}
            className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
          >
            Run Eligibility Checks
          </button>
        </div>
      }
    >
      {error && (
        <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-red-200">
          {error}
        </div>
      )}

      {!referral ? (
        <div className="rounded-3xl border border-white/10 bg-zinc-950 p-8 text-zinc-400">
          Loading extracted referral...
        </div>
      ) : (
        <>
          <div className="mb-6 rounded-3xl border border-cyan-400/20 bg-cyan-400/10 p-5 text-cyan-200">
            Document understanding complete. Structured referral is ready for operational checks.
          </div>

          <div className="space-y-6">
            <Section title="Patient Demographics">
              <Field label="Patient Name" value={referral.patient_name} />
              <Field label="MRN" value={referral.mrn} />
              <Field label="DOB" value={referral.dob} />
              <Field label="Discharge Date" value={referral.discharge_date} />
            </Section>

            <Section title="Contact Information">
              <Field label="Phone" value={referral.phone} />
              <Field label="Address" value={referral.address} />
              <Field label="ZIP Code" value={referral.zip_code} />
              <Field
                label="Missing Fields"
                value={referral.missing_fields?.join(", ")}
              />
            </Section>

            <Section title="Referral Source & Insurance">
              <Field label="Hospital" value={referral.hospital_name} />
              <Field label="Insurance Provider" value={referral.insurance_provider} />
              <Field label="Member ID" value={referral.member_id} />
              <Field label="Diagnosis" value={referral.diagnosis} />
            </Section>

            <Section title="Clinical Services & Physicians">
              <Field
                label="Services Required"
                value={referral.services_required?.join(", ")}
              />
              <Field
                label="Primary Care Physician"
                value={referral.primary_care_physician}
              />
              <Field
                label="Ordering Physician"
                value={referral.ordering_physician}
              />
              <Field label="Validation Status" value={run.status} />
            </Section>

            <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
              <div className="mb-4 text-sm font-medium">Eligibility Override Inputs</div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-4">
                  <div className="text-xs uppercase tracking-wide text-zinc-500">
                    Insurance Provider
                  </div>
                  <input
                    value={insuranceProvider}
                    onChange={(e) => setInsuranceProvider(e.target.value)}
                    className="mt-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
                    placeholder="Enter insurance provider"
                  />
                </div>

                <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-4">
                  <div className="text-xs uppercase tracking-wide text-zinc-500">
                    ZIP Code
                  </div>
                  <input
                    value={zipCode}
                    onChange={(e) => setZipCode(e.target.value)}
                    className="mt-3 w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none"
                    placeholder="Enter ZIP code"
                  />
                </div>
              </div>
              <div className="mt-3 text-xs text-zinc-500">
                These values are used for TinyFish eligibility checks if extraction missed or misread them.
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
              <div className="mb-4 text-sm font-medium">Validation Notes</div>
              <div className="space-y-3">
                {referral.validation_notes?.map((note, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border border-white/5 bg-zinc-900/70 px-4 py-3 text-sm text-zinc-300"
                  >
                    • {note}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </PageShell>
  )
}