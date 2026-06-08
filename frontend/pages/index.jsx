import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";

import IntentPreview from "../components/IntentPreview";
import KPIInput from "../components/KPIInput";
import ProgressStepper from "../components/ProgressStepper";
import QuestionFlow from "../components/QuestionFlow";
import {
  buildIntent,
  calculateKpi,
  generateQuestions,
  validateIntent,
} from "../services/api";

const STEP_INDEX_MAP = {
  kpi_name: 0,
  questionnaire: 1,
  intent_validation: 2,
  calculation: 4,
  review: 5,
};

export default function HomePage() {
  const router = useRouter();
  const [state, setState] = useState({ current_step: "kpi_name", answers: {} });
  const [questions, setQuestions] = useState([]);
  const [defaultMeasureColumn, setDefaultMeasureColumn] = useState("cost_amount");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Merge server-returned state with locally-held questions/answers so they
  // are never dropped when navigating between flow steps.
  const mergeState = (serverState, localQuestions, localAnswers) => ({
    ...serverState,
    questions:
      (serverState.questions && serverState.questions.length)
        ? serverState.questions
        : localQuestions || [],
    answers: localAnswers || serverState.answers || {},
  });

  useEffect(() => {
    const raw = localStorage.getItem("kpiAgentState");
    if (!raw) {
      return;
    }
    try {
      const parsed = JSON.parse(raw);
      setState(parsed);
      setQuestions(parsed.questions || []);
      if (parsed.default_measure_column) {
        setDefaultMeasureColumn(parsed.default_measure_column);
      }
    } catch (err) {
      localStorage.removeItem("kpiAgentState");
    }
  }, []);

  const stepNumber = useMemo(() => STEP_INDEX_MAP[state.current_step] ?? 0, [state.current_step]);

  const handleGenerate = async (kpiName) => {
    setError("");
    setIsLoading(true);
    try {
      const response = await generateQuestions(kpiName);
      const qs = response.data.questions || [];
      const col = response.data.default_measure_column || "cost_amount";
      // Embed questions and default_measure_column into state so edit flow can
      // restore them directly from localStorage without an extra API call.
      const newState = { ...response.data.state, questions: qs, default_measure_column: col };
      setState(newState);
      setQuestions(qs);
      setDefaultMeasureColumn(col);
      localStorage.setItem("kpiAgentState", JSON.stringify(newState));
    } catch (err) {
      setError(err?.response?.data?.error || "Failed to generate questions");
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuestionSubmit = async (answers) => {
    setError("");
    setIsLoading(true);
    // Keep a reference to the question list so all downstream state saves
    // can embed them — the backend does not echo questions back.
    const currentQuestions = state.questions.length ? state.questions : questions;
    try {
      const intentResponse = await buildIntent(state.kpi_name, state.metric_type, answers);
      const intent = intentResponse.data.intent;

      const validationResponse = await validateIntent(intent);
      if (!validationResponse.data.validation_result.valid) {
        const vs = mergeState(validationResponse.data.state, currentQuestions, answers);
        setState(vs);
        localStorage.setItem("kpiAgentState", JSON.stringify(vs));
        setError(validationResponse.data.validation_result.errors.join(", "));
        return;
      }

      const calculationResponse = await calculateKpi(intent);
      // Enrich the review-bound state with questions + answers so Edit can
      // fully restore the questionnaire without any extra API calls.
      const cs = mergeState(calculationResponse.data.state, currentQuestions, answers);
      setState(cs);
      localStorage.setItem("kpiAgentState", JSON.stringify(cs));
      router.push("/review");
    } catch (err) {
      // Surface zero-division (422) or any other API error clearly.
      const apiError =
        err?.response?.data?.error ||
        err?.response?.data?.validation_result?.errors?.join(", ") ||
        "Failed during KPI flow";
      setError(apiError);
      // If backend returned a state (e.g. validation failure), persist it.
      const errState = err?.response?.data?.state;
      if (errState) {
        const es = mergeState(errState, currentQuestions, answers);
        setState(es);
        localStorage.setItem("kpiAgentState", JSON.stringify(es));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-10 md:px-8">
      <div className="space-y-6">
        <ProgressStepper currentStep={stepNumber} />

        {state.current_step === "kpi_name" && (
          <KPIInput onGenerate={handleGenerate} isLoading={isLoading} />
        )}

        {state.current_step !== "kpi_name" && (
          <>
          {state.kpi_name && (
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 shadow-sm">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Editing KPI</p>
                <p className="text-base font-bold text-slateink">{state.kpi_name}</p>
              </div>
              <button
                onClick={() => {
                  localStorage.removeItem("kpiAgentState");
                  setState({ current_step: "kpi_name", answers: {} });
                  setQuestions([]);
                  setError("");
                }}
                className="text-xs font-medium text-slate-500 underline hover:text-rose-600"
              >
                Start Over
              </button>
            </div>
          )}
          <QuestionFlow
            interpretation={state.interpretation}
            description={state.description}
            questions={questions.length ? questions : state.questions || []}
            defaultMeasureColumn={defaultMeasureColumn}
            onSubmit={handleQuestionSubmit}
            isLoading={isLoading}
            initialAnswers={state.answers || {}}
          />
          </>
        )}

        <IntentPreview intent={state.intent} />

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm font-medium text-rose-700">
            {error}
          </div>
        )}
      </div>
    </main>
  );
}
