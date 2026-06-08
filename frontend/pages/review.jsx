import { useEffect, useState } from "react";
import { useRouter } from "next/router";

import ProgressStepper from "../components/ProgressStepper";
import ReviewCard from "../components/ReviewCard";
import { resetSession } from "../services/api";

export default function ReviewPage() {
  const router = useRouter();
  const [state, setState] = useState(null);
  const [approved, setApproved] = useState(false);

  useEffect(() => {
    const raw = localStorage.getItem("kpiAgentState");
    if (!raw) {
      router.replace("/");
      return;
    }
    const parsed = JSON.parse(raw);
    setState(parsed);
  }, [router]);

  const onApprove = () => {
    setApproved(true);
  };

  const onEdit = () => {
    if (!state) return;
    // Transition step back to questionnaire. The full state including
    // questions, answers, and kpi_name is already in state from the enriched
    // save that handleQuestionSubmit performed.  No data is lost.
    const edited = {
      ...state,
      current_step: "questionnaire",
      // Clear stale review artifacts so the user sees a clean edit form.
      calculation_result: null,
      validation_result: null,
    };
    localStorage.setItem("kpiAgentState", JSON.stringify(edited));
    router.push("/");
  };

  const onRegenerate = async () => {
    await resetSession();
    localStorage.removeItem("kpiAgentState");
    router.push("/");
  };

  if (!state) {
    return null;
  }

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-4 py-10 md:px-8">
      <div className="space-y-6">
        <ProgressStepper currentStep={5} />
        <ReviewCard state={state} onApprove={onApprove} onEdit={onEdit} onRegenerate={onRegenerate} />

        {approved && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-700">
            KPI approved. You can now operationalize this KPI or export the intent for downstream systems.
          </div>
        )}
      </div>
    </main>
  );
}
