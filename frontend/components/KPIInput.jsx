import { useState } from "react";

export default function KPIInput({ onGenerate, isLoading }) {
  const [kpiName, setKpiName] = useState("");

  const handleSubmit = (event) => {
    event.preventDefault();
    onGenerate(kpiName);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-white/60 bg-white/90 p-6 shadow-panel backdrop-blur">
      <div>
        <h1 className="text-2xl font-bold text-slateink">Agentic KPI Builder</h1>
        <p className="mt-1 text-sm text-slate-600">Describe the KPI in plain English. The agent will infer the metric type and guide you.</p>
      </div>

      <label className="block">
        <span className="mb-2 block text-sm font-semibold text-slate-700">KPI Name</span>
        <input
          value={kpiName}
          onChange={(e) => setKpiName(e.target.value)}
          placeholder="Near Miss to Issue Ratio"
          className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none ring-0 transition focus:border-ocean-600"
          required
        />
      </label>

      <button
        type="submit"
        disabled={isLoading}
        className="inline-flex items-center rounded-xl bg-ocean-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-ocean-800 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Generate KPI
      </button>
    </form>
  );
}
