const STATUS_STYLES = {
  Good: "bg-emerald-100 text-emerald-700 border-emerald-300",
  Warning: "bg-amber-100 text-amber-700 border-amber-300",
  Critical: "bg-rose-100 text-rose-700 border-rose-300",
};

export default function StatusBadge({ status }) {
  const style = STATUS_STYLES[status] || "bg-slate-100 text-slate-700 border-slate-300";
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${style}`}>
      {status || "Unknown"}
    </span>
  );
}
