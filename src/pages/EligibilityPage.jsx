import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { useLocation, useNavigate, useParams } from "react-router-dom"
import PageShell from "../components/layout/PageShell"
import { getRun, getTinyfishRun, startTinyfishEligibility } from "../services/api"

function statusClasses(status) {
  if (status === "complete") return "bg-emerald-400/15 text-emerald-300"
  if (status === "running") return "bg-cyan-400/15 text-cyan-300"
  if (status === "failed") return "bg-red-400/15 text-red-300"
  return "bg-zinc-800 text-zinc-400"
}

function AgentCard({ agent }) {
  return (
    <motion.div
      layout
      className="rounded-2xl border border-white/10 bg-zinc-900/80 p-4"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-sm font-medium">{agent.name}</div>
          <div className="mt-1 text-xs text-zinc-500">{agent.goal}</div>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs ${statusClasses(agent.status)}`}>
          {agent.status}
        </span>
      </div>

      <div className="mt-4 space-y-3">
        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">Website</div>
          <div className="mt-1 break-all text-sm text-zinc-200">{agent.site}</div>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">Observation</div>
          <div className="mt-1 text-sm text-zinc-200">{agent.observation}</div>
        </div>

        <div className="rounded-xl border border-white/5 bg-black/20 p-3">
          <div className="text-[11px] uppercase tracking-wide text-zinc-500">Action</div>
          <div className="mt-1 text-sm text-zinc-200">{agent.action}</div>
        </div>

        {agent.streaming_url && (
          <a
            href={agent.streaming_url}
            target="_blank"
            rel="noreferrer"
            className="block rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-cyan-300 hover:bg-white/10"
          >
            Open TinyFish Live Browser
          </a>
        )}

        {agent.updates?.length > 0 && (
          <div className="rounded-xl border border-white/5 bg-black/20 p-3">
            <div className="text-[11px] uppercase tracking-wide text-zinc-500">Recent updates</div>
            <div className="mt-2 space-y-2">
              {agent.updates.map((u, idx) => (
                <div key={idx} className="text-sm text-zinc-300">
                  • {u}
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <a
            href={agent.site}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300 hover:bg-white/5"
          >
            Open Target Page
          </a>
        </div>
      </div>
    </motion.div>
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

export default function EligibilityPage() {
  const { id: runId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()

  const insuranceProviderOverride = location.state?.insuranceProvider || ""
  const zipCodeOverride = location.state?.zipCode || ""

  const [documentRun, setDocumentRun] = useState(null)
  const [tinyfishRun, setTinyfishRun] = useState(null)
  const [tinyfishRunId, setTinyfishRunId] = useState("")
  const [error, setError] = useState("")

  useEffect(() => {
    async function fetchDocumentRun() {
      try {
        const data = await getRun(runId)
        setDocumentRun(data)
      } catch (err) {
        setError(err.message || "Failed to fetch document run.")
      }
    }

    fetchDocumentRun()
  }, [runId])

  useEffect(() => {
    let intervalId

    async function beginTinyfish() {
      try {
        const start = await startTinyfishEligibility({
          runId,
          insuranceProvider: insuranceProviderOverride,
          zipCode: zipCodeOverride,
        })

        setTinyfishRunId(start.tinyfish_run_id)

        async function fetchTinyfishRun() {
          try {
            const data = await getTinyfishRun(start.tinyfish_run_id)
            setTinyfishRun(data)

            if (data.status === "complete" || data.status === "failed") {
              if (intervalId) clearInterval(intervalId)
            }
          } catch (err) {
            setError(err.message || "Failed to fetch TinyFish run.")
            if (intervalId) clearInterval(intervalId)
          }
        }

        await fetchTinyfishRun()
        intervalId = setInterval(fetchTinyfishRun, 1500)
      } catch (err) {
        setError(err.message || "Failed to start TinyFish eligibility.")
      }
    }

    beginTinyfish()

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [runId, insuranceProviderOverride, zipCodeOverride])

  const done = tinyfishRun?.status === "complete"

  return (
    <PageShell
      title="TinyFish Eligibility Checks"
      subtitle="TinyFish agents are using the structured referral to verify payer acceptance and serviceability through real browser workflows."
      actions={
        done && (
          <button
            onClick={() => navigate(`/schedule/${runId}`)}
            className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
          >
            Schedule Visit
          </button>
        )
      }
    >
      {error && (
        <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-red-200">
          {error}
        </div>
      )}

      {tinyfishRun?.status === "failed" && (
        <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-red-200">
          TinyFish workflow failed: {tinyfishRun.error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
        <div className="space-y-6">
          <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
            <div className="mb-4 text-sm font-medium">Eligibility Context</div>
            <div className="grid gap-4">
              <Field
                label="Patient Name"
                value={documentRun?.referral?.patient_name}
              />
              <Field
                label="Insurance Provider Used"
                value={insuranceProviderOverride || documentRun?.referral?.insurance_provider}
              />
              <Field
                label="ZIP Code Used"
                value={zipCodeOverride || documentRun?.referral?.zip_code}
              />
              <Field
                label="TinyFish Run ID"
                value={tinyfishRunId || "Starting..."}
              />
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
            <div className="mb-4 text-sm font-medium">TinyFish Event Stream</div>
            <div className="space-y-3">
              {tinyfishRun?.logs?.map((log, idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-white/5 bg-zinc-900/70 px-4 py-3 text-sm text-zinc-300"
                >
                  {log.message}
                </div>
              ))}
            </div>
          </div>

          {done && (
            <div className="space-y-4">
              <div
                className={`rounded-3xl border p-5 ${
                  tinyfishRun?.insurance_accepted && tinyfishRun?.serviceable_zip
                    ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200"
                    : "border-amber-400/20 bg-amber-400/10 text-amber-200"
                }`}
              >
                {tinyfishRun?.insurance_accepted && tinyfishRun?.serviceable_zip
                  ? "Eligibility checks passed. Insurance accepted, ZIP is serviceable, and referral is accepted for intake."
                  : "Eligibility checks completed. One or more checks did not pass."}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <Field
                  label="Insurance Accepted"
                  value={String(tinyfishRun?.insurance_accepted)}
                />
                <Field
                  label="Serviceable ZIP"
                  value={String(tinyfishRun?.serviceable_zip)}
                />
                <Field
                  label="Matched Branch"
                  value={tinyfishRun?.matched_branch}
                />
                <Field
                  label="Eligibility Status"
                  value={tinyfishRun?.status}
                />
              </div>
            </div>
          )}
        </div>

        <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
          <div className="mb-4 text-sm font-medium">TinyFish Agent Activity</div>
          <div className="grid gap-4 xl:grid-cols-2">
            {tinyfishRun?.agents?.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        </div>
      </div>
    </PageShell>
  )
}