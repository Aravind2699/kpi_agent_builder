import { useEffect, useMemo, useState } from "react";

import LoadingSpinner from "./LoadingSpinner";

function timeValuePlaceholder(type) {
  if (type === "year") return "Example: 2026";
  if (type === "month") return "1 to 12";
  if (type === "quarter") return "1 to 4";
  return "N/A";
}

export default function QuestionFlow({
  interpretation,
  description,
  questions,
  defaultMeasureColumn,
  onSubmit,
  isLoading,
  initialAnswers,
}) {
  const [answers, setAnswers] = useState(() => ({
    ...initialAnswers,
    measure_column: initialAnswers?.measure_column || defaultMeasureColumn,
    time_period_type: initialAnswers?.time_period_type || "all",
  }));

  useEffect(() => {
    setAnswers({
      ...initialAnswers,
      measure_column: initialAnswers?.measure_column || defaultMeasureColumn,
      time_period_type: initialAnswers?.time_period_type || "all",
    });
  }, [initialAnswers, defaultMeasureColumn]);

  const showTimeValue = useMemo(() => {
    return ["year", "month", "quarter"].includes(answers.time_period_type);
  }, [answers.time_period_type]);

  const updateAnswer = (key, value) => {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit(answers);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-2xl border border-white/60 bg-white/95 p-6 shadow-panel animate-rise">
      <div>
        <h2 className="text-xl font-bold text-slateink">Dynamic Question Flow</h2>
        {interpretation && (
          <p className="mb-1 rounded-lg border border-ocean-200 bg-ocean-50 px-3 py-2 text-sm text-ocean-800">
            {interpretation}
          </p>
        )}
        <p className="text-sm text-slate-600">{description}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {questions.map((question) => (
          <label key={question.id} className="block">
            <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">{question.label}</span>
            <select
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-ocean-600"
              value={answers[question.id] || (question.allow_all ? "All" : "")}
              onChange={(e) => updateAnswer(question.id, e.target.value)}
              required={question.required}
            >
              {!question.allow_all && <option value="">Select...</option>}
              {question.options.map((option) => (
                <option value={option} key={`${question.id}-${option}`}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>

      {showTimeValue && (
        <label className="block">
          <span className="mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500">Time Period Value</span>
          <input
            type="text"
            value={answers.time_period_value || ""}
            onChange={(e) => updateAnswer("time_period_value", e.target.value)}
            placeholder={timeValuePlaceholder(answers.time_period_type)}
            className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none transition focus:border-ocean-600"
            required
          />
        </label>
      )}

      <div className="flex items-center justify-between">
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center rounded-xl bg-ember-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-ember-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Build, Validate, and Calculate
        </button>
        {isLoading && <LoadingSpinner label="Agent is building intent..." />}
      </div>
    </form>
  );
}
