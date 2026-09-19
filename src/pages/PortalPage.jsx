import { useMemo, useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import PageShell from "../components/layout/PageShell"
import { referrals as initialReferrals } from "../data/referrals"

export default function PortalPage() {
  const navigate = useNavigate()
  const [rows, setRows] = useState(initialReferrals)
  const [highlightedId, setHighlightedId] = useState(null)

  const sortedRows = useMemo(() => rows, [rows])

  function handleNewReferral() {
    const newReferral = {
      id: `ref-new-${Date.now()}`,
      patientName: "John Doe",
      hospitalName: "UT Southwestern",
      mrn: "MRN-772901",
      status: "New Referral",
      receivedAt: "Just now",
      pdfName: "sample_referral.pdf",
      usesSamplePdf: true,
      details: {
        dob: "1946-10-09",
        insurance: "Aetna Medicare",
        address: null,
        phone: null,
        services: ["PT", "Skilled Nursing"],
        pcp: null,
      },
    }

    setRows((prev) => [newReferral, ...prev])
    setHighlightedId(newReferral.id)

    setTimeout(() => {
      setHighlightedId(null)
    }, 3000)
  }

  return (
    <PageShell
      title="Referral Portal"
      subtitle="Incoming referrals from hospital discharge teams. Select a referral to review the packet and begin intake."
      actions={
        <button
          onClick={handleNewReferral}
          className="rounded-xl bg-cyan-400 px-5 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          New Referral
        </button>
      }
    >
      <div className="overflow-hidden rounded-3xl border border-white/10 bg-zinc-950">
        <div className="grid grid-cols-[1.3fr_1.3fr_1fr_1fr_1fr] border-b border-white/10 bg-zinc-900/70 px-6 py-4 text-sm font-semibold text-zinc-300">
          <div>Patient Name</div>
          <div>Hospital</div>
          <div>MRN</div>
          <div>Status</div>
          <div>Received</div>
        </div>

        <AnimatePresence initial={false}>
          {sortedRows.map((row) => {
            const highlighted = row.id === highlightedId

            return (
              <motion.button
                key={row.id}
                layout
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                onClick={() => navigate(`/referral/${row.id}`)}
                className={`grid w-full grid-cols-[1.3fr_1.3fr_1fr_1fr_1fr] border-b border-white/5 px-6 py-5 text-left transition ${highlighted
                    ? "bg-cyan-400/10 ring-1 ring-inset ring-cyan-300/50"
                    : "bg-transparent hover:bg-white/5"
                  }`}
              >
                <div className="font-medium">{row.patientName}</div>
                <div className="text-zinc-300">{row.hospitalName}</div>
                <div className="text-zinc-400">{row.mrn}</div>
                <div>
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-zinc-300">
                    {row.status}
                  </span>
                </div>
                <div className="text-zinc-400">{row.receivedAt}</div>
              </motion.button>
            )
          })}
        </AnimatePresence>
      </div>
    </PageShell>
  )
}