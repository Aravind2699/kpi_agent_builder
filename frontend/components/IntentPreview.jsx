export default function IntentPreview({ intent }) {
  if (!intent) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-900 p-4 text-xs text-slate-100 shadow-panel animate-rise">
      <p className="mb-2 text-sm font-semibold text-ocean-100">KPI Intent JSON</p>
      <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(intent, null, 2)}</pre>
    </div>
  );
}
