'use client'

import React, { useState, useEffect } from 'react'
import { 
  ShieldCheck, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle2, 
  Layers, 
  ArrowRight, 
  Clock, 
  RefreshCw, 
  UploadCloud,
  FileSpreadsheet,
  Cpu
} from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ReconcilerDashboard() {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'matches' | 'exceptions' | 'benchmark'>('matches')
  const [batchSummary, setBatchSummary] = useState<any>(null)
  const [matches, setMatches] = useState<any[]>([])
  const [exceptions, setExceptions] = useState<any[]>([])
  const [health, setHealth] = useState<any>({ status: 'checking', llm_provider: 'gemini' })
  const [uploadBankFile, setUploadBankFile] = useState<File | null>(null)
  const [uploadLedgerFile, setUploadLedgerFile] = useState<File | null>(null)
  const [statusMessage, setStatusMessage] = useState<string>('')

  useEffect(() => {
    fetch(`${API_BASE}/api/health`)
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth({ status: 'offline', llm_provider: 'gemini' }))
  }, [])

  const loadDemoData = async () => {
    setLoading(true)
    setStatusMessage('Executing 3-Layer Reconciliation (Deterministic -> Gemini 2.0 -> Exceptions)...')
    try {
      const res = await fetch(`${API_BASE}/api/demo/load`, { method: 'POST' })
      const data = await res.json()
      setBatchSummary(data)
      
      // Fetch Matches
      const matchRes = await fetch(`${API_BASE}/api/matches?batch_id=${data.batch_id}`)
      const matchData = await matchRes.json()
      setMatches(matchData)

      // Fetch Exceptions
      const excRes = await fetch(`${API_BASE}/api/exceptions?batch_id=${data.batch_id}`)
      const excData = await excRes.json()
      setExceptions(excData)

      setStatusMessage('Reconciliation Completed Successfully.')
    } catch (err: any) {
      setStatusMessage('Error executing reconciliation: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleManualUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadBankFile || !uploadLedgerFile) {
      alert('Please select both Bank CSV and Ledger CSV')
      return
    }

    setLoading(true)
    setStatusMessage('Uploading and parsing CSV records...')
    try {
      const formData = new FormData()
      formData.append('name', 'Manual Batch - ' + new Date().toLocaleTimeString())
      formData.append('bank_csv', uploadBankFile)
      formData.append('ledger_csv', uploadLedgerFile)

      const upRes = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData
      })
      const upData = await upRes.json()

      setStatusMessage('Running 3-Layer Pipeline on uploaded dataset...')
      const recRes = await fetch(`${API_BASE}/api/reconcile/${upData.batch_id}`, {
        method: 'POST'
      })
      const recData = await recRes.json()
      setBatchSummary(recData)

      const matchRes = await fetch(`${API_BASE}/api/matches?batch_id=${upData.batch_id}`)
      setMatches(await matchRes.json())

      const excRes = await fetch(`${API_BASE}/api/exceptions?batch_id=${upData.batch_id}`)
      setExceptions(await excRes.json())

      setStatusMessage('Custom Reconciliation Finished.')
    } catch (err: any) {
      setStatusMessage('Upload failed: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                Finance-Ops Reconciliation Agent
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300">
                  2026 Verification Loop
                </span>
              </h1>
              <p className="text-sm text-slate-400">
                Multi-source ledger verification: Deterministic rules + Gemini 2.0 Flash reasoning
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
            <span className={`w-2 h-2 rounded-full ${health.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
            <span className="text-slate-400 font-mono">Backend: {health.status} ({health.llm_provider || 'gemini'})</span>
          </div>

          <button
            onClick={loadDemoData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium text-sm transition-all shadow-lg shadow-emerald-950/50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            Load Benchmark Demo (58 Records)
          </button>
        </div>
      </header>

      {/* KPI Stats Row */}
      {batchSummary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Records</div>
            <div className="text-2xl font-bold text-white mt-1">
              {batchSummary.total_bank} <span className="text-xs text-slate-500">Bank</span> / {batchSummary.total_ledger} <span className="text-xs text-slate-500">Ledger</span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Matched Pairs</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1 flex items-baseline gap-2">
              {batchSummary.matched}
              <span className="text-xs font-normal text-emerald-500/80">
                ({batchSummary.layer_breakdown?.deterministic || 0} L1 + {batchSummary.layer_breakdown?.llm || 0} L2)
              </span>
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Match Rate</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {batchSummary.match_rate}%
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Exceptions Flagged</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">
              {batchSummary.exceptions}
            </div>
          </div>

          <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Latency / Cost</div>
            <div className="text-2xl font-bold text-slate-200 mt-1 flex items-baseline gap-1">
              {batchSummary.duration_ms}ms <span className="text-xs text-emerald-400 font-mono">$0.00</span>
            </div>
          </div>
        </div>
      )}

      {/* Manual Upload Section */}
      <section className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 backdrop-blur">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-2 mb-4">
          <UploadCloud className="w-4 h-4 text-emerald-400" />
          Custom File Upload & Multi-Source Reconciliation
        </h2>
        <form onSubmit={handleManualUpload} className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Bank Statement Feed CSV</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setUploadBankFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer border border-slate-800 rounded-lg p-1 bg-slate-950/50"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">Internal Ledger (ERP) CSV</label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setUploadLedgerFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer border border-slate-800 rounded-lg p-1 bg-slate-950/50"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 font-medium text-sm text-slate-200 transition-colors flex items-center justify-center gap-2"
          >
            <Layers className="w-4 h-4 text-emerald-400" />
            Start Batch Reconciliation
          </button>
        </form>
        {statusMessage && (
          <p className="text-xs text-emerald-400/90 mt-3 font-mono">● {statusMessage}</p>
        )}
      </section>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm">
        <button
          onClick={() => setActiveTab('matches')}
          className={`pb-3 font-medium transition-all ${activeTab === 'matches' ? 'border-b-2 border-emerald-400 text-emerald-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Matched Records ({matches.length})
        </button>
        <button
          onClick={() => setActiveTab('exceptions')}
          className={`pb-3 font-medium transition-all ${activeTab === 'exceptions' ? 'border-b-2 border-rose-400 text-rose-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Forensic Exceptions ({exceptions.length})
        </button>
        <button
          onClick={() => setActiveTab('benchmark')}
          className={`pb-3 font-medium transition-all ${activeTab === 'benchmark' ? 'border-b-2 border-cyan-400 text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Architecture & Benchmark Ground Truth
        </button>
      </div>

      {/* Tab 1: Matched Records */}
      {activeTab === 'matches' && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3.5">Bank Ref / Date</th>
                <th className="p-3.5">Ledger Inv / Date</th>
                <th className="p-3.5">Counterparty & Vendor</th>
                <th className="p-3.5">Amount</th>
                <th className="p-3.5">Layer</th>
                <th className="p-3.5">Confidence</th>
                <th className="p-3.5">Forensic Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {matches.map((m, idx) => (
                <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3.5">
                    <div className="font-semibold text-slate-200">{m.bank_ref}</div>
                    <div className="text-[11px] text-slate-500">{m.bank_date}</div>
                  </td>
                  <td className="p-3.5">
                    <div className="font-semibold text-slate-200">{m.ledger_invoice}</div>
                    <div className="text-[11px] text-slate-500">{m.ledger_date}</div>
                  </td>
                  <td className="p-3.5">
                    <div className="text-slate-200">{m.bank_counterparty}</div>
                    <div className="text-[11px] text-slate-400">{m.ledger_vendor}</div>
                  </td>
                  <td className="p-3.5 font-semibold text-emerald-400">
                    ${Number(m.bank_amount).toFixed(2)}
                  </td>
                  <td className="p-3.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${m.layer === 'deterministic' ? 'bg-blue-950 text-blue-300 border border-blue-800' : 'bg-purple-950 text-purple-300 border border-purple-800'}`}>
                      {m.layer}
                    </span>
                  </td>
                  <td className="p-3.5">
                    <span className="text-emerald-400 font-semibold">{Math.round(m.confidence * 100)}%</span>
                  </td>
                  <td className="p-3.5 text-[11px] text-slate-400 max-w-xs truncate font-sans" title={m.reason}>
                    {m.reason}
                  </td>
                </tr>
              ))}
              {matches.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No matches yet. Click <strong>"Load Benchmark Demo"</strong> above.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Forensic Exceptions */}
      {activeTab === 'exceptions' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {exceptions.map((e, idx) => (
              <div key={idx} className="p-4 rounded-xl border border-rose-950/80 bg-rose-950/10 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-rose-950 text-rose-300 border border-rose-800">
                    {e.source.toUpperCase()} EXCEPTION: {e.category}
                  </span>
                  <span className="font-mono text-sm font-semibold text-rose-300">
                    ${Number(e.amount || 0).toFixed(2)}
                  </span>
                </div>
                <div className="text-sm font-medium text-slate-200">
                  {e.identifier} — {e.entity_name}
                </div>
                <p className="text-xs text-slate-400">{e.detail}</p>
              </div>
            ))}
            {exceptions.length === 0 && (
              <div className="col-span-2 p-8 text-center text-slate-500 border border-slate-800 rounded-xl">
                No exceptions loaded. Run reconciliation above.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: Benchmark & Architecture */}
      {activeTab === 'benchmark' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-emerald-400" />
              Honest Verification Architecture
            </h3>
            <p className="text-sm text-slate-300 leading-relaxed">
              Standard LLM agents fail in financial operations because they hallucinate fuzzy matches on coincidental amounts. Our agent enforces a <strong>3-Layer Verification Loop</strong>:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-xs text-blue-400 font-bold uppercase">Layer 1: Deterministic</div>
                <div className="text-sm text-slate-300 mt-1">Exact ref ID, date proximity ≤1d, amount equality. 0ms LLM latency.</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-xs text-purple-400 font-bold uppercase">Layer 2: Gemini 2.0 Flash</div>
                <div className="text-sm text-slate-300 mt-1">Batched semantic reasoning on entity aliases, wire fee deltas, ACH lag.</div>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <div className="text-xs text-rose-400 font-bold uppercase">Layer 3: Forensic Refusal</div>
                <div className="text-sm text-slate-300 mt-1">Rejection of trap records (e.g. Delta Air vs Shell Oil with same $450).</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
