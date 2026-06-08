import StatusBadge from "./StatusBadge";

export default function ReviewCard({ state, onApprove, onEdit, onRegenerate }) {
  const validation = state?.validation_result;
  const result = state?.calculation_result;
  const intent = state?.intent;

  return (
    <div className="rounded-2xl border border-white/60 bg-white/95 p-6 shadow-panel animate-rise">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slateink">KPI Review Card</h1>
          <p className="mt-1 text-sm text-slate-600">Review the generated KPI intent and computed output before approval.</p>
        </div>
        <StatusBadge status={result?.status} />
      </div>

      <dl className="mt-6 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">KPI Name</dt>
          <dd className="mt-1 text-sm text-slate-900">{state?.kpi_name || "-"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Validation Status</dt>
          <dd className="mt-1 text-sm text-slate-900">{validation?.valid ? "Passed" : "Failed"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Formula</dt>
          <dd className="mt-1 text-sm text-slate-900">{result?.formula || "-"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Computed Value</dt>
          <dd className="mt-1 text-sm text-slate-900">{result?.value ?? "-"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Unit</dt>
          <dd className="mt-1 text-sm text-slate-900">{result?.unit || "-"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Description</dt>
          <dd className="mt-1 text-sm text-slate-900">{result?.description || state?.description || "-"}</dd>
        </div>

        <div className="rounded-xl border border-slate-200 p-3">
          <dt className="text-xs font-semibold uppercase text-slate-500">Status Reason</dt>
          <dd className="mt-1 text-sm text-slate-900">{result?.status_reason || "-"}</dd>
        </div>

        {state?.metric_type === "ratio" && (
          <>
            <div className="rounded-xl border border-slate-200 p-3">
              <dt className="text-xs font-semibold uppercase text-slate-500">Numerator</dt>
              <dd className="mt-1 text-sm text-slate-900">{result?.numerator ?? "-"}</dd>
            </div>

            <div className="rounded-xl border border-slate-200 p-3">
              <dt className="text-xs font-semibold uppercase text-slate-500">Denominator</dt>
              <dd className="mt-1 text-sm text-slate-900">{result?.denominator ?? "-"}</dd>
            </div>
          </>
        )}
      </dl>

      {!validation?.valid && (
        <div className="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
          <p className="font-semibold">Validation Errors</p>
          <ul className="mt-1 list-inside list-disc">
            {(validation?.errors || []).map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-slate-200 bg-slate-900 p-3 text-xs text-slate-100">
        <p className="mb-2 text-sm font-semibold text-ocean-100">Final Intent</p>
        <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(intent, null, 2)}</pre>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-900 p-3 text-xs text-slate-100">
          <p className="mb-2 text-sm font-semibold text-ocean-100">Validation Response</p>
          <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(validation, null, 2)}</pre>
        </div>
        <div className="rounded-xl border border-slate-200 bg-slate-900 p-3 text-xs text-slate-100">
          <p className="mb-2 text-sm font-semibold text-ocean-100">Calculation Response</p>
          <pre className="overflow-auto whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          onClick={onApprove}
          disabled={!validation?.valid}
          className="rounded-xl bg-emerald-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={onEdit}
          className="rounded-xl bg-amber-500 px-5 py-2 text-sm font-semibold text-white transition hover:bg-amber-600"
        >
          Edit
        </button>
        <button
          onClick={onRegenerate}
          className="rounded-xl bg-rose-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
        >
          Regenerate
        </button>
      </div>
    </div>
  );
}
