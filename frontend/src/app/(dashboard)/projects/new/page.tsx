"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Film, Mic, Image, Video, Subtitles, FileText, ArrowLeft, ArrowRight, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { apiClient } from "@/lib/api";

const TOTAL_STEPS = 4;

const VIDEO_TYPES = [
  {
    value: "shorts",
    label: "Shorts",
    description: "60초 세로 숏폼 영상",
    icon: Film,
  },
  {
    value: "longform",
    label: "Long-form",
    description: "5-15분 가로 영상",
    icon: Video,
  },
] as const;

const PIPELINE_STEPS = [
  { key: "script", label: "스크립트", icon: FileText, description: "주제를 기반으로 AI 스크립트 생성" },
  { key: "tts", label: "TTS", icon: Mic, description: "텍스트를 음성으로 변환" },
  { key: "images", label: "이미지", icon: Image, description: "AI 생성 또는 스톡 이미지" },
  { key: "video", label: "영상", icon: Video, description: "켄 번즈 효과로 장면 합성" },
  { key: "subtitle", label: "자막", icon: Subtitles, description: "Whisper 자동 자막 생성" },
  { key: "metadata", label: "메타데이터", icon: FileText, description: "AI 제목·설명·태그 생성" },
] as const;

const STEP_LABELS = ["영상 타입", "제목/주제", "파이프라인", "최종 확인"] as const;

interface FormData {
  type: string;
  title: string;
  topic: string;
  steps: Record<string, boolean>;
}

const DEFAULT_FORM_DATA: FormData = {
  type: "shorts",
  title: "",
  topic: "",
  steps: {
    script: true,
    tts: true,
    images: true,
    video: true,
    subtitle: true,
    metadata: true,
  },
};

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {Array.from({ length: total }, (_, i) => {
        const isDone = i < current;
        const isActive = i === current;
        const num = String(i + 1).padStart(2, "0");
        return (
          <div key={i} className="flex items-center gap-1">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all ${
                  isDone
                    ? "gradient-brand text-white"
                    : isActive
                    ? "border-2 border-violet-500 text-violet-400 bg-violet-950/40"
                    : "border border-zinc-700 text-zinc-600 bg-zinc-900"
                }`}
              >
                {isDone ? "✓" : num}
              </div>
              <span
                className={`hidden text-xs sm:block transition-colors ${
                  isActive
                    ? "text-zinc-200 font-medium"
                    : isDone
                    ? "text-zinc-400"
                    : "text-zinc-600"
                }`}
              >
                {STEP_LABELS[i]}
              </span>
            </div>
            {i < total - 1 && (
              <div
                className={`h-px w-6 mx-1 ${i < current ? "bg-violet-600" : "bg-zinc-800"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function StepType({ formData, onChange }: { formData: FormData; onChange: (data: Partial<FormData>) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">영상 타입 선택</h2>
        <p className="text-sm text-zinc-400">만들 영상의 형식을 선택하세요.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {VIDEO_TYPES.map((vt) => {
          const Icon = vt.icon;
          const isSelected = formData.type === vt.value;
          return (
            <button
              key={vt.value}
              type="button"
              onClick={() => onChange({ type: vt.value })}
              className={`flex flex-col items-start gap-3 rounded-lg border p-4 text-left transition-colors ${
                isSelected
                  ? "border-violet-500/60 bg-gradient-to-br from-violet-950/60 to-indigo-950/60 shadow-sm shadow-violet-900/30"
                  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
              }`}
            >
              <Icon className={`h-6 w-6 ${isSelected ? "text-violet-400" : "text-zinc-500"}`} />
              <div>
                <div className="font-medium text-zinc-200">{vt.label}</div>
                <div className="text-sm text-zinc-500">{vt.description}</div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function StepTopic({ formData, onChange }: { formData: FormData; onChange: (data: Partial<FormData>) => void }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">영상 내용 입력</h2>
        <p className="text-sm text-zinc-400">프로젝트 제목과 주제를 입력하세요.</p>
      </div>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">제목</Label>
          <Input
            id="title"
            placeholder="내 영상 제목"
            value={formData.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="topic">주제 / 프롬프트</Label>
          <Textarea
            id="topic"
            placeholder="초보자를 위한 양자컴퓨팅 쉬운 설명..."
            rows={4}
            value={formData.topic}
            onChange={(e) => onChange({ topic: e.target.value })}
          />
          <p className="text-xs text-zinc-500">
            영상 내용을 설명하세요. AI가 이를 바탕으로 스크립트를 생성합니다.
          </p>
        </div>
      </div>
    </div>
  );
}

function StepPipeline({ formData, onChange }: { formData: FormData; onChange: (data: Partial<FormData>) => void }) {
  function toggleStep(key: string) {
    onChange({
      steps: { ...formData.steps, [key]: !formData.steps[key] },
    });
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">파이프라인 단계</h2>
        <p className="text-sm text-zinc-400">생성에 포함할 단계를 선택하세요.</p>
      </div>
      <div className="space-y-3">
        {PIPELINE_STEPS.map((step) => {
          const Icon = step.icon;
          return (
            <div
              key={step.key}
              className={`flex items-center justify-between rounded-lg border p-4 transition-colors ${
                  formData.steps[step.key]
                    ? "border-violet-800/40 bg-violet-950/20"
                    : "border-zinc-800 bg-zinc-900/50"
                }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`h-5 w-5 ${formData.steps[step.key] ? "text-violet-400" : "text-zinc-400"}`} />
                <div>
                  <div className="text-sm font-medium text-zinc-200">{step.label}</div>
                  <div className="text-xs text-zinc-500">{step.description}</div>
                </div>
              </div>
              <Switch
                checked={formData.steps[step.key]}
                onCheckedChange={() => toggleStep(step.key)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StepConfirm({ formData }: { formData: FormData }) {
  const enabledSteps = PIPELINE_STEPS.filter((s) => formData.steps[s.key]);
  const typeLabel = VIDEO_TYPES.find((v) => v.value === formData.type)?.label ?? formData.type;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">확인 및 생성</h2>
        <p className="text-sm text-zinc-400">시작 전 설정을 검토하세요.</p>
      </div>
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardContent className="space-y-4 pt-6">
          <div className="flex justify-between">
            <span className="text-sm text-zinc-400">타입</span>
            <Badge variant="outline" className="border-zinc-700 text-zinc-300">
              {typeLabel}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-zinc-400">제목</span>
            <span className="text-sm font-medium text-zinc-200">{formData.title || "(제목 없음)"}</span>
          </div>
          <div>
            <span className="text-sm text-zinc-400">주제</span>
            <p className="mt-1 text-sm text-zinc-300">{formData.topic || "(주제 없음)"}</p>
          </div>
          <div>
            <span className="text-sm text-zinc-400">파이프라인</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {enabledSteps.map((s) => (
                <Badge key={s.key} className="bg-violet-900 text-violet-300">
                  {s.label}
                </Badge>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function NewProjectInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialType = searchParams.get("type") ?? "shorts";
  const [step, setStep] = useState(searchParams.get("type") ? 1 : 0);
  const [formData, setFormData] = useState<FormData>({
    ...DEFAULT_FORM_DATA,
    type: initialType,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateForm(data: Partial<FormData>) {
    setFormData((prev) => ({ ...prev, ...data }));
  }

  const isStep1Valid = formData.title.trim().length > 0 && formData.topic.trim().length > 0;
  const canProceed =
    step === 0 ||
    (step === 1 && isStep1Valid) ||
    step === 2 ||
    (step === 3 && isStep1Valid);

  async function handleCreate() {
    setIsSubmitting(true);
    setError(null);
    try {
      const project = await apiClient("/api/projects", {
        method: "POST",
        body: JSON.stringify({
          title: formData.title,
          type: formData.type,
          topic: formData.topic,
          pipeline_config: formData.steps,
        }),
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "프로젝트 생성에 실패했습니다");
    } finally {
      setIsSubmitting(false);
    }
  }

  const steps = [
    <StepType key="type" formData={formData} onChange={updateForm} />,
    <StepTopic key="topic" formData={formData} onChange={updateForm} />,
    <StepPipeline key="pipeline" formData={formData} onChange={updateForm} />,
    <StepConfirm key="confirm" formData={formData} />,
  ];

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-50">새 영상 만들기</h1>
        <p className="mt-1 text-sm text-zinc-500">{STEP_LABELS[step]}</p>
      </div>

      <StepIndicator current={step} total={TOTAL_STEPS} />

      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardContent className="pt-6">{steps[step]}</CardContent>
      </Card>

      {error && (
        <div className={`rounded-lg p-4 flex gap-3 ${
            error.includes("한도") 
            ? "bg-indigo-950/40 border border-indigo-500/50" 
            : "bg-red-950/20 border border-red-500/30"
        }`}>
          <AlertCircle className={`h-5 w-5 shrink-0 ${error.includes("한도") ? "text-indigo-400" : "text-red-400"}`} />
          <div className="flex-1 space-y-2">
            <p className={`text-sm ${error.includes("한도") ? "text-indigo-200 font-medium" : "text-red-200"}`}>
                {error}
            </p>
            {error.includes("한도") && (
                <Button 
                    size="sm" 
                    variant="link" 
                    className="h-auto p-0 text-indigo-400 font-bold hover:text-indigo-300"
                    onClick={() => router.push("/pricing")}
                >
                    껌값으로 무제한 생성하기 →
                </Button>
            )}
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <Button
          variant="ghost"
          onClick={() => (step === 0 ? router.back() : setStep(step - 1))}
          disabled={isSubmitting}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {step === 0 ? "취소" : "이전"}
        </Button>

        {step < TOTAL_STEPS - 1 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed}>
            다음
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleCreate} disabled={isSubmitting || !canProceed}>
            {isSubmitting ? "생성 중..." : "프로젝트 생성"}
            <Check className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}

export default function NewProjectPage() {
  return (
    <Suspense fallback={<div className="mx-auto max-w-2xl py-12 text-center text-zinc-400">로딩 중...</div>}>
      <NewProjectInner />
    </Suspense>
  );
}
