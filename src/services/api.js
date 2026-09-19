const API_BASE = "http://localhost:8000"

export async function processSampleDocument() {
  const res = await fetch(`${API_BASE}/api/documents/process-sample`, {
    method: "POST",
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function processUploadedDocument(file) {
  const formData = new FormData()
  formData.append("file", file)

  const res = await fetch(`${API_BASE}/api/documents/process`, {
    method: "POST",
    body: formData,
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getRun(runId) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function startTinyfishEligibility({ runId, insuranceProvider, zipCode }) {
  const res = await fetch(`${API_BASE}/api/tinyfish/eligibility/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_id: runId,
      insurance_provider: insuranceProvider || null,
      zip_code: zipCode || null,
    }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function startTinyfishPlacement({ runId }) {
  const res = await fetch(`${API_BASE}/api/tinyfish/placement/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function startTinyfishSchedule({ runId }) {
  const res = await fetch(`${API_BASE}/api/tinyfish/schedule/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ run_id: runId }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getTinyfishRun(tinyfishRunId) {
  const res = await fetch(`${API_BASE}/api/tinyfish/runs/${tinyfishRunId}`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}