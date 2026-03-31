"use client";

import { useState, useEffect, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import {
  apiClient,
  runStep,
  getStepOutput,
  approveStep,
  rejectStep,
} from "@/lib/api";
import { StepConfigPanel } from "@/components/review/step-config-panel";
import { ScriptReview } from "@/components/review/script-review";
import { TtsReview } from "@/components/review/tts-review";
import { ImagesReview } from "@/components/review/images-review";
import { MetadataReview } from "@/components/review/metadata-review";
import { VideoReview } from "@/components/review/video-review";

const POLL_INTERVAL_MS = 3000;

interface StepInfo {
  step: string;
  status: string;
  provider?: string | null;
  error_message?: string | null;
}

const STEP_LABELS: Record<string, string> = {
  script: "스크립트",
  tts: "TTS",
  images: "이미지",
  video: "영상",
  subtitle: "자막",
  metadata: "메타데이터",
};

const STATUS_LABELS: Record<string, string> = {
  pending: "대기",
  running: "생성 중",
  awaiting_review: "검토 대기",
  approved: "승인됨",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900/60 text-blue-300",
  awaiting_review: "bg-violet-900/60 text-violet-300",
  approved: "bg-emerald-900/60 text-emerald-300",
  completed: "bg-emerald-900/60 text-emerald-300",
  failed: "bg-red-900/60 text-red-300",
  cancelled: "bg-zinc-700 text-zinc-400",
};

interface PipelineWizardProps {
  projectId: string;
  initialSteps: StepInfo[];
}

export function PipelineWizard({ projectId, initialSteps }: PipelineWizardProps) {
  const [steps, setSteps] = useState<StepInfo[]>(initialSteps);
  const [activeStep, setActiveStep] = useState<string>("");
  const [stepOutput, setStepOutput] = useState<Record<string, unknown> | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 현재 포커스할 단계 결정
  useEffect(() => {
    // 첫 번째 "actionable" 단계를 찾는다
    const actionable = steps.find(
      (s) => s.status === "pending" || s.status === "running" || s.status === "awaiting_review" || s.status === "failed"
    );
    if (actionable) {
      setActiveStep(actionable.step);
    } else {
      // 모든 단계가 완료/승인 → 마지막 단계
      const last = steps[steps.length - 1];
      if (last) setActiveStep(last.step);
    }
  }, [steps]);

  // running 상태 단계가 있으면 폴링
  useEffect(() => {
    const hasRunning = steps.some((s) => s.status === "running");
    if (!hasRunning) return;

    const interval = setInterval(async () => {
      try {
        const data = await apiClient(`/api/pipeline/${projectId}/status`);
        if (data.steps) {
          setSteps(data.steps);
        }
      } catch {
        // 폴링 실패는 무시
      }
    }, POLL_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [steps, projectId]);

  // awaiting_review 상태가 되면 output 자동 로드
  useEffect(() => {
    const reviewStep = steps.find((s) => s.step === activeStep && s.status === "awaiting_review");
    if (!reviewStep) {
      setStepOutput(null);
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const data = await getStepOutput(projectId, reviewStep.step);
        if (!cancelled && data.output_data) {
          setStepOutput(data.output_data);
        }
      } catch {
        if (!cancelled) setStepOutput(null);
      }
    })();

    return () => { cancelled = true; };
  }, [activeStep, steps, projectId]);

  const handleRun = useCallback(async (provider: string, config: Record<string, unknown>) => {
    setError(null);
    setIsRunning(true);
    try {
      await runStep(projectId, activeStep, provider, config);
      // 상태 갱신
      setSteps((prev) =>
        prev.map((s) =>
          s.step === activeStep ? { ...s, status: "running", provider } : s
        )
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "단계 실행에 실패했습니다.";
      setError(msg);
    } finally {
      setIsRunning(false);
    }
  }, [projectId, activeStep]);

  const handleApprove = useCallback(async (editedData?: Record<string, unknown>) => {
    setError(null);
    try {
      await approveStep(projectId, activeStep, editedData);
      // 상태 갱신
      const data = await apiClient(`/api/pipeline/${projectId}/status`);
      if (data.steps) setSteps(data.steps);
      setStepOutput(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "승인에 실패했습니다.";
      setError(msg);
    }
  }, [projectId, activeStep]);

  const handleReject = useCallback(async () => {
    setError(null);
    try {
      await rejectStep(projectId, activeStep);
      setSteps((prev) =>
        prev.map((s) =>
          s.step === activeStep ? { ...s, status: "pending" } : s
        )
      );
      setStepOutput(null);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "재생성 요청에 실패했습니다.";
      setError(msg);
    }
  }, [projectId, activeStep]);

  const currentStep = steps.find((s) => s.step === activeStep);
  const completedCount = steps.filter(
    (s) => s.status === "approved" || s.status === "completed"
  ).length;
  const progressPercent = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* 스텝 인디케이터 */}
      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {steps.map((s, i) => (
          <button
            key={s.step}
            onClick={() => setActiveStep(s.step)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap",
              s.step === activeStep
                ? "bg-violet-600 text-white ring-2 ring-violet-400/30"
                : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
            )}
          >
            <span className="text-[10px] opacity-60">{i + 1}</span>
            {STEP_LABELS[s.step] ?? s.step}
            <Badge
              variant="secondary"
              className={cn("text-[9px] px-1 py-0", STATUS_COLORS[s.status])}
            >
              {STATUS_LABELS[s.status] ?? s.status}
            </Badge>
          </button>
        ))}
      </div>

      {/* 진행률 바 */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>전체 진행률</span>
          <span>{progressPercent}%</span>
        </div>
        <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-600 to-indigo-500 transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="p-3 rounded-lg bg-red-950/50 border border-red-900/50 text-sm text-red-300">
          {error}
        </div>
      )}

      {/* 현재 단계 컨텐츠 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            {STEP_LABELS[activeStep] ?? activeStep}
            {currentStep && (
              <Badge
                variant="secondary"
                className={cn("text-xs", STATUS_COLORS[currentStep.status])}
              >
                {STATUS_LABELS[currentStep.status] ?? currentStep.status}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {currentStep?.status === "pending" && (
            <StepConfigPanel
              step={activeStep}
              onRun={handleRun}
              isLoading={isRunning}
            />
          )}

          {currentStep?.status === "running" && (
            <div className="flex flex-col items-center gap-3 py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
              <p className="text-sm text-muted-foreground">
                {STEP_LABELS[activeStep]} 생성 중...
              </p>
              <Skeleton className="h-4 w-48" />
            </div>
          )}

          {currentStep?.status === "awaiting_review" && stepOutput && (
            <ReviewContent
              step={activeStep}
              outputData={stepOutput}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          )}

          {currentStep?.status === "awaiting_review" && !stepOutput && (
            <div className="space-y-3 py-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          )}

          {(currentStep?.status === "approved" || currentStep?.status === "completed") && (
            <div className="text-center py-6">
              <div className="text-2xl mb-2">&#10003;</div>
              <p className="text-sm text-muted-foreground">
                이 단계는 {currentStep.status === "approved" ? "승인" : "완료"}되었습니다.
              </p>
            </div>
          )}

          {currentStep?.status === "failed" && (
            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-red-950/50 border border-red-900/50 text-sm text-red-300">
                {currentStep.error_message ?? "알 수 없는 오류가 발생했습니다."}
              </div>
              <StepConfigPanel
                step={activeStep}
                onRun={handleRun}
                isLoading={isRunning}
              />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

// 단계별 검토 컴포넌트 라우팅
function ReviewContent({
  step,
  outputData,
  onApprove,
  onReject,
}: {
  step: string;
  outputData: Record<string, unknown>;
  onApprove: (editedData?: Record<string, unknown>) => void;
  onReject: () => void;
}) {
  switch (step) {
    case "script":
      return (
        <ScriptReview
          outputData={outputData as Parameters<typeof ScriptReview>[0]["outputData"]}
          onApprove={onApprove}
          onReject={onReject}
        />
      );
    case "tts":
      return (
        <TtsReview
          outputData={outputData as Parameters<typeof TtsReview>[0]["outputData"]}
          onApprove={() => onApprove()}
          onReject={onReject}
        />
      );
    case "images":
      return (
        <ImagesReview
          outputData={outputData as Parameters<typeof ImagesReview>[0]["outputData"]}
          onApprove={() => onApprove()}
          onReject={onReject}
        />
      );
    case "metadata":
      return (
        <MetadataReview
          outputData={outputData as Parameters<typeof MetadataReview>[0]["outputData"]}
          onApprove={onApprove}
          onReject={onReject}
        />
      );
    case "video":
      return (
        <VideoReview
          outputData={outputData as Parameters<typeof VideoReview>[0]["outputData"]}
          onApprove={() => onApprove()}
          onReject={onReject}
        />
      );
    default:
      // subtitle 등 — 간단한 승인/재생성 버튼
      return (
        <div className="space-y-3">
          <pre className="text-xs bg-zinc-900 p-3 rounded overflow-auto max-h-60">
            {JSON.stringify(outputData, null, 2)}
          </pre>
          <div className="flex gap-2">
            <button
              onClick={() => onApprove()}
              className="flex-1 px-4 py-2 bg-violet-600 text-white rounded-lg text-sm hover:bg-violet-700"
            >
              승인
            </button>
            <button
              onClick={onReject}
              className="px-4 py-2 border border-zinc-700 text-zinc-300 rounded-lg text-sm hover:bg-zinc-800"
            >
              재생성
            </button>
          </div>
        </div>
      );
  }
}
