"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import {
  STEP_LABELS,
  TOTAL_STEPS,
  DEFAULT_FORM_DATA,
  type FormData,
} from "@/components/project-form/types";
import { StepType } from "@/components/project-form/step-type";
import { StepScript } from "@/components/project-form/step-script";
import { StepImageStyle } from "@/components/project-form/step-image-style";
import { StepVoice } from "@/components/project-form/step-voice";
import { StepSubtitle } from "@/components/project-form/step-subtitle";
import { StepConfirm } from "@/components/project-form/step-confirm";

function StepIndicator({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
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
                {isDone ? <Check className="h-3.5 w-3.5" /> : num}
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

function buildPipelineConfig(formData: FormData): Record<string, unknown> {
  const config: Record<string, unknown> = { ...formData.steps };

  // script config
  if (formData.script.mode !== "manual") {
    config.script_config = {
      mode: formData.script.mode,
      language: formData.script.language,
      purpose: formData.script.purpose,
      tone: formData.script.tone,
      speech_style: formData.script.speechStyle,
      opening_comment: formData.script.openingComment,
      closing_comment: formData.script.closingComment,
      product_name: formData.script.productName,
      required_info: formData.script.requiredInfo,
      reference_script: formData.script.referenceScript,
    };
  } else {
    config.script_config = {
      mode: "manual",
      manual_script: formData.script.manualScript,
    };
  }

  // image config
  config.image_config = {
    provider: formData.imageStyle.provider,
    style: formData.imageStyle.style,
  };

  // voice config
  config.voice_config = {
    enabled: formData.voice.enabled,
    provider: formData.voice.provider,
    voice_id: formData.voice.voiceId,
    emotion: formData.voice.emotion,
    speed: formData.voice.speed,
    custom_audio_url: formData.voice.customAudioUrl || undefined,
  };

  // subtitle config
  config.subtitle_config = {
    enabled: formData.subtitle.enabled,
    style: formData.subtitle.style,
    font_size: formData.subtitle.fontSize,
    position: formData.subtitle.position,
    outline_width: formData.subtitle.outlineWidth,
    opacity: formData.subtitle.opacity,
  };

  // video sync config
  config.video_config = {
    sync_mode: formData.videoSync.mode,
    speed_factor: formData.videoSync.speedFactor,
  };

  // intro config
  if (formData.intro.introVideoUrl || formData.intro.logoUrl) {
    config.intro_config = {
      intro_video_url: formData.intro.introVideoUrl || undefined,
      logo_url: formData.intro.logoUrl || undefined,
      logo_position: formData.intro.logoPosition,
      logo_opacity: formData.intro.logoOpacity,
    };
  }

  // bgm config
  config.bgm_config = {
    enabled: formData.bgm.enabled,
    mood: formData.bgm.mood,
    volume: formData.bgm.volume,
  };

  // audio post-processing config
  if (formData.audioPost.enabled) {
    config.audio_post_config = {
      enabled: true,
      mode: formData.audioPost.mode,
    };
  }

  // thumbnail config
  if (formData.thumbnail.enabled) {
    config.thumbnail = true;
  }

  return config;
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

  const hasTitle = formData.script.title.trim().length > 0;
  const hasTopic = formData.script.topic.trim().length > 0;
  const hasManualScript = formData.script.manualScript.trim().length > 0;

  const isScriptStepValid =
    formData.script.mode === "manual"
      ? hasTitle && hasManualScript
      : hasTitle && hasTopic;

  const canProceed =
    step === 0 ||
    (step === 1 && isScriptStepValid) ||
    step === 2 ||
    step === 3 ||
    step === 4 ||
    (step === 5 && isScriptStepValid);

  async function handleCreate() {
    setIsSubmitting(true);
    setError(null);
    try {
      const project = await apiClient("/api/projects", {
        method: "POST",
        body: JSON.stringify({
          title: formData.script.title || "새 프로젝트",
          type: formData.type,
          topic: formData.script.topic,
          pipeline_config: buildPipelineConfig(formData),
        }),
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "프로젝트 생성에 실패했습니다",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const steps = [
    <StepType key="type" formData={formData} onChange={updateForm} />,
    <StepScript key="script" formData={formData} onChange={updateForm} />,
    <StepImageStyle
      key="image"
      formData={formData}
      onChange={updateForm}
    />,
    <StepVoice key="voice" formData={formData} onChange={updateForm} />,
    <StepSubtitle key="subtitle" formData={formData} onChange={updateForm} />,
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
        <div
          className={`rounded-lg p-4 flex gap-3 ${
            error.includes("한도")
              ? "bg-indigo-950/40 border border-indigo-500/50"
              : "bg-red-950/20 border border-red-500/30"
          }`}
        >
          <AlertCircle
            className={`h-5 w-5 shrink-0 ${error.includes("한도") ? "text-indigo-400" : "text-red-400"}`}
          />
          <div className="flex-1 space-y-2">
            <p
              className={`text-sm ${error.includes("한도") ? "text-indigo-200 font-medium" : "text-red-200"}`}
            >
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
          <Button
            onClick={handleCreate}
            disabled={isSubmitting || !canProceed}
          >
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
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl py-12 text-center text-zinc-400">
          로딩 중...
        </div>
      }
    >
      <NewProjectInner />
    </Suspense>
  );
}
