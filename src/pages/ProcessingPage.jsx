import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { useNavigate, useParams } from "react-router-dom"
import PageShell from "../components/layout/PageShell"
import { getRun } from "../services/api"

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
                    <div className="text-[11px] uppercase tracking-wide text-zinc-500">Current task</div>
                    <div className="mt-1 text-sm text-zinc-200">{agent.current_task}</div>
                </div>

                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                    <div className="text-[11px] uppercase tracking-wide text-zinc-500">Observation</div>
                    <div className="mt-1 text-sm text-zinc-200">{agent.observation}</div>
                </div>

                <div className="rounded-xl border border-white/5 bg-black/20 p-3">
                    <div className="text-[11px] uppercase tracking-wide text-zinc-500">Action</div>
                    <div className="mt-1 text-sm text-zinc-200">{agent.action}</div>
                </div>

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
            </div>
        </motion.div>
    )
}

const progressLabels = [
    "Queued",
    "Packet loaded",
    "OCR / text extraction",
    "LLM extraction",
    "Validation",
    "Complete",
]

export default function ProcessingPage() {
    const { id: runId } = useParams()
    const navigate = useNavigate()

    const [run, setRun] = useState(null)
    const [error, setError] = useState("")

    useEffect(() => {
        let intervalId

        async function fetchRun() {
            try {
                const data = await getRun(runId)
                setRun(data)

                if (data.status === "complete" || data.status === "failed") {
                    if (intervalId) clearInterval(intervalId)
                }
            } catch (err) {
                setError(err.message || "Failed to fetch workflow status.")
                if (intervalId) clearInterval(intervalId)
            }
        }

        fetchRun()
        intervalId = setInterval(fetchRun, 1500)

        return () => {
            if (intervalId) clearInterval(intervalId)
        }
    }, [runId])

    const done = run?.status === "complete"

    return (
        <PageShell
            title="Document Processing"
            subtitle="The referral packet is being analyzed, extracted into structured fields, and validated before downstream operational workflows begin."
            actions={
                done && (
                    <button
                        onClick={() => navigate(`/review/${runId}`)}
                        className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
                    >
                        Next: Review Extracted Referral
                    </button>
                )
            }
        >
            {error && (
                <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-red-200">
                    {error}
                </div>
            )}

            {run?.status === "failed" && (
                <div className="mb-6 rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-red-200">
                    Workflow failed: {run.error}
                </div>
            )}

            <div className="grid gap-6 lg:grid-cols-[0.72fr_1.28fr]">
                <div className="space-y-6">
                    <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
                        <div className="mb-4 text-sm font-medium">Packet Summary</div>
                        <div className="space-y-3 text-sm text-zinc-300">
                            <div><span className="text-zinc-500">File:</span> {run?.file_name || "Loading..."}</div>
                            <div><span className="text-zinc-500">Document type:</span> {run?.document_type || "Detecting..."}</div>
                            <div><span className="text-zinc-500">Stage:</span> {run?.current_stage || "Queued"}</div>
                            <div><span className="text-zinc-500">Status:</span> {run?.status || "Queued"}</div>
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
                        <div className="mb-4 text-sm font-medium">Document Pipeline Progress</div>
                        <div className="grid gap-3">
                            {progressLabels.map((label, idx) => {
                                const active = run ? idx <= run.progress : idx === 0
                                return (
                                    <div
                                        key={label}
                                        className={`rounded-2xl border p-4 text-sm ${active
                                            ? "border-cyan-400/50 bg-cyan-400/10 text-cyan-200"
                                            : "border-white/10 bg-zinc-900 text-zinc-500"
                                            }`}
                                    >
                                        {label}
                                    </div>
                                )
                            })}
                        </div>
                    </div>

                    <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
                        <div className="mb-4 text-sm font-medium">Document Event Stream</div>
                        <div className="space-y-3">
                            {run?.logs?.map((log, idx) => (
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
                        <div className="rounded-3xl border border-emerald-400/20 bg-emerald-400/10 p-5 text-emerald-200">
                            Document understanding complete. Structured referral is ready for operational checks.
                        </div>
                    )}
                </div>

                <div className="rounded-3xl border border-white/10 bg-zinc-950 p-5">
                    <div className="mb-4 text-sm font-medium">Agent Activity</div>
                    <div className="grid gap-4 xl:grid-cols-2">
                        {run?.agents?.map((agent) => (
                            <AgentCard key={agent.id} agent={agent} />
                        ))}
                    </div>
                </div>
            </div>
        </PageShell>
    )
}