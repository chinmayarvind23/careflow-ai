import { useMemo, useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import PageShell from "../components/layout/PageShell"
import { referrals } from "../data/referrals"
import { processSampleDocument } from "../services/api"

const API_BASE = "http://localhost:8000"

function Field({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-4">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className={`mt-2 text-sm ${value ? "text-white" : "text-amber-300"}`}>
        {value || "Missing / incomplete"}
      </div>
    </div>
  )
}

export default function ReferralDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState("")

  const referral = useMemo(
    () => referrals.find((r) => r.id === id) || referrals[0],
    [id]
  )

  const pdfUrl = `${API_BASE}/files/${referral.pdfName}`

  async function handleProcess() {
    try {
      setProcessing(true)
      setError("")

      const result = await processSampleDocument()
      navigate(`/processing/${result.run_id}`)
    } catch (err) {
      setError(err.message || "Failed to process document.")
    } finally {
      setProcessing(false)
    }
  }

  return (
    <PageShell
      title={`Referral Review — ${referral.patientName}`}
      subtitle="Review the incoming packet and available intake fields before starting extraction."
      actions={
        <button
          onClick={handleProcess}
          disabled={processing}
          className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {processing ? "Processing..." : "Process / Extract"}
        </button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="space-y-4 rounded-3xl border border-white/10 bg-zinc-950 p-5">
          <Field label="Patient Name" value={referral.patientName} />
          <Field label="Hospital" value={referral.hospitalName} />
          <Field label="MRN" value={referral.mrn} />
          <Field label="DOB" value={referral.details.dob} />
          <Field label="Insurance" value={referral.details.insurance} />
          <Field label="Address" value={referral.details.address} />
          <Field label="Phone" value={referral.details.phone} />
          <Field label="Services" value={referral.details.services?.join(", ")} />
          <Field label="PCP" value={referral.details.pcp} />

          <div className="rounded-2xl border border-white/10 bg-zinc-900/70 p-4">
            <div className="text-xs uppercase tracking-wide text-zinc-500">Attached packet</div>
            <div className="mt-2 text-sm text-zinc-300">
              Mapped to backend sample PDF: {referral.pdfName}
            </div>
          </div>

          {error && (
            <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Referral Packet Preview</div>
              <div className="text-xs text-zinc-500">{referral.pdfName}</div>
              <div className="mt-1 break-all text-[11px] text-zinc-600">{pdfUrl}</div>
            </div>
            <span className="rounded-full border border-white/10 px-3 py-1 text-xs text-zinc-400">
              PDF Preview
            </span>
          </div>

          <div className="overflow-hidden rounded-2xl border border-white/10 bg-zinc-900">
            <object
              data={pdfUrl}
              type="application/pdf"
              className="h-[700px] w-full"
            >
              <embed
                src={pdfUrl}
                type="application/pdf"
                className="h-[700px] w-full"
              />
              <div className="flex h-[700px] flex-col items-center justify-center gap-3 text-zinc-400">
                <div>Unable to preview PDF inline.</div>
                <a
                  href={pdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/5"
                >
                  Open PDF in new tab
                </a>
              </div>
            </object>
          </div>
        </div>
      </div>
    </PageShell>
  )
}