"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Film, Mic, Image, Video, Subtitles, FileText, ArrowLeft, ArrowRight, Check } from "lucide-react";
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
    description: "60s vertical video for YouTube Shorts",
    icon: Film,
  },
  {
    value: "longform",
    label: "Long-form",
    description: "5-15 min horizontal video",
    icon: Video,
  },
] as const;

const PIPELINE_STEPS = [
  { key: "script", label: "Script", icon: FileText, description: "AI-generated script from your topic" },
  { key: "tts", label: "TTS", icon: Mic, description: "Text-to-speech audio generation" },
  { key: "images", label: "Images", icon: Image, description: "AI-generated or stock visuals" },
  { key: "video", label: "Video", icon: Video, description: "Compose scenes with Ken Burns effects" },
  { key: "subtitle", label: "Subtitle", icon: Subtitles, description: "Auto-generated captions (Whisper)" },
  { key: "metadata", label: "Metadata", icon: FileText, description: "AI title, description, and tags" },
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
        <h2 className="text-lg font-medium text-zinc-50">Choose video type</h2>
        <p className="text-sm text-zinc-400">Select the format for your video.</p>
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
        <h2 className="text-lg font-medium text-zinc-50">Describe your video</h2>
        <p className="text-sm text-zinc-400">Give your project a title and topic.</p>
      </div>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            placeholder="My Awesome Video"
            value={formData.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="topic">Topic / Prompt</Label>
          <Textarea
            id="topic"
            placeholder="Explain quantum computing in simple terms for beginners..."
            rows={4}
            value={formData.topic}
            onChange={(e) => onChange({ topic: e.target.value })}
          />
          <p className="text-xs text-zinc-500">
            Describe what the video should be about. The AI will generate a script from this.
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
        <h2 className="text-lg font-medium text-zinc-50">Pipeline steps</h2>
        <p className="text-sm text-zinc-400">Toggle which steps to include in generation.</p>
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
        <h2 className="text-lg font-medium text-zinc-50">Confirm & Create</h2>
        <p className="text-sm text-zinc-400">Review your project settings before starting.</p>
      </div>
      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardContent className="space-y-4 pt-6">
          <div className="flex justify-between">
            <span className="text-sm text-zinc-400">Type</span>
            <Badge variant="outline" className="border-zinc-700 text-zinc-300">
              {typeLabel}
            </Badge>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-zinc-400">Title</span>
            <span className="text-sm font-medium text-zinc-200">{formData.title || "(untitled)"}</span>
          </div>
          <div>
            <span className="text-sm text-zinc-400">Topic</span>
            <p className="mt-1 text-sm text-zinc-300">{formData.topic || "(no topic)"}</p>
          </div>
          <div>
            <span className="text-sm text-zinc-400">Pipeline</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {enabledSteps.map((s) => (
                <Badge key={s.key} className="bg-blue-900 text-blue-300">
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
          config: {
            topic: formData.topic,
            steps: formData.steps,
          },
        }),
      });
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
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
        <p className="text-sm text-red-400">{error}</p>
      )}

      <div className="flex justify-between">
        <Button
          variant="ghost"
          onClick={() => (step === 0 ? router.back() : setStep(step - 1))}
          disabled={isSubmitting}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          {step === 0 ? "Cancel" : "Back"}
        </Button>

        {step < TOTAL_STEPS - 1 ? (
          <Button onClick={() => setStep(step + 1)} disabled={!canProceed}>
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button onClick={handleCreate} disabled={isSubmitting || !canProceed}>
            {isSubmitting ? "Creating..." : "Create Project"}
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
