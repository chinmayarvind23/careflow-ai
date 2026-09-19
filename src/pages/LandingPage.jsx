import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import PageShell from "../components/layout/PageShell"

const stats = [
  { label: "U.S. healthcare economy", value: "$5T+" },
  { label: "Home health referrals processed yearly", value: "Millions" },
  { label: "Referrals delayed by missing data", value: "High" },
  { label: "Manual intake time per packet", value: "30–60 min" },
]

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <PageShell
      title="Agentic Referral Intake for Home Health"
      subtitle="From messy discharge packets to structured referral placement, eligibility verification, and scheduling initialization."
      actions={
        <button
          onClick={() => navigate("/portal")}
          className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          Start Demo
        </button>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-3xl border border-white/10 bg-gradient-to-br from-zinc-900 to-zinc-950 p-8 shadow-2xl"
        >
          <div className="max-w-3xl">
            <p className="mb-4 text-sm uppercase tracking-[0.2em] text-cyan-400">
              Intake automation
            </p>
            <h2 className="text-5xl font-semibold leading-tight">
              Home health referral processing built for speed, accuracy, and operational scale.
            </h2>
            <p className="mt-5 text-lg leading-8 text-zinc-400">
              Referral packets arrive incomplete, inconsistent, and delayed. Our system extracts critical intake data, runs downstream checks, and prepares referrals for placement with agentic orchestration.
            </p>
          </div>
        </motion.div>

        <div className="grid gap-4">
          {stats.map((stat, idx) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08 }}
              className="rounded-2xl border border-white/10 bg-zinc-900/80 p-6"
            >
              <div className="text-3xl font-semibold">{stat.value}</div>
              <div className="mt-2 text-sm text-zinc-400">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </PageShell>
  )
}