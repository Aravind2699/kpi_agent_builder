const STEPS = [
  "KPI Name",
  "Questions",
  "Intent",
  "Validation",
  "Calculation",
  "Review",
];

export default function ProgressStepper({ currentStep }) {
  return (
    <ol className="grid grid-cols-2 gap-2 md:grid-cols-6">
      {STEPS.map((step, index) => {
        const active = index <= currentStep;
        return (
          <li
            key={step}
            className={`rounded-xl border px-3 py-2 text-center text-xs font-semibold transition ${
              active
                ? "border-ocean-600 bg-ocean-50 text-ocean-800"
                : "border-slate-200 bg-white text-slate-400"
            }`}
          >
            {index + 1}. {step}
          </li>
        );
      })}
    </ol>
  );
}
