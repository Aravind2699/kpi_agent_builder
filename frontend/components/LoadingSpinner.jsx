export default function LoadingSpinner({ label = "Processing..." }) {
  return (
    <div className="flex items-center gap-3 text-ocean-800">
      <div className="h-5 w-5 rounded-full border-2 border-ocean-600 border-t-transparent animate-spin" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
