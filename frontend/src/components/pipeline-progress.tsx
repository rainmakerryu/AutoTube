"use client";

import {
  FileText,
  Mic,
  Image,
  Video,
  Subtitles,
  Check,
  Loader2,
  Circle,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { PipelineEvent } from "@/hooks/use-pipeline-sse";

const STEP_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  script: { label: "스크립트", icon: FileText },
  tts: { label: "TTS", icon: Mic },
  images: { label: "이미지", icon: Image },
  video: { label: "영상", icon: Video },
  subtitle: { label: "자막", icon: Subtitles },
  metadata: { label: "메타데이터", icon: FileText },
};

const STATUS_LABELS: Record<string, string> = {
  pending: "대기 중",
  running: "진행 중",
  completed: "완료",
  failed: "실패",
  skipped: "건너뜀",
};

const STATUS_DISPLAY: Record<string, { color: string; badgeClass: string }> = {
  pending: { color: "text-zinc-600", badgeClass: "bg-zinc-800 text-zinc-400" },
  running: { color: "text-blue-400", badgeClass: "bg-blue-900 text-blue-300" },
  completed: { color: "text-green-400", badgeClass: "bg-green-900 text-green-300" },
  failed: { color: "text-red-400", badgeClass: "bg-red-900 text-red-300" },
  skipped: { color: "text-zinc-500", badgeClass: "bg-zinc-800 text-zinc-500" },
};

function StatusIcon({ status }: { status: string }) {
  switch (status) {
    case "completed":
      return <Check className="h-4 w-4 text-green-400" />;
    case "running":
      return <Loader2 className="h-4 w-4 animate-spin text-blue-400" />;
    case "failed":
      return <XCircle className="h-4 w-4 text-red-400" />;
    default:
      return <Circle className="h-4 w-4 text-zinc-600" />;
  }
}

interface PipelineStep {
  name: string;
  status: string;
  progress: number;
  message?: string;
}

interface PipelineProgressProps {
  steps: PipelineStep[];
  events?: PipelineEvent[];
  isConnected?: boolean;
}

export function PipelineProgress({ steps, events = [], isConnected }: PipelineProgressProps) {
  // Merge SSE events into step states
  const latestByStep = new Map<string, PipelineEvent>();
  for (const event of events) {
    latestByStep.set(event.step, event);
  }

  const mergedSteps = steps.map((step) => {
    const event = latestByStep.get(step.name);
    if (event) {
      return {
        ...step,
        status: event.status,
        progress: event.progress,
        message: event.message,
      };
    }
    return step;
  });

  const completedCount = mergedSteps.filter((s) => s.status === "completed").length;
  const totalSteps = mergedSteps.length;
  const overallProgress = totalSteps > 0 ? Math.round((completedCount / totalSteps) * 100) : 0;

  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-400">파이프라인 진행 상황</CardTitle>
        <div className="flex items-center gap-2">
          {isConnected !== undefined && (
            <span className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500" : "bg-zinc-600"}`} />
          )}
          <span className="text-sm font-medium text-zinc-300">{overallProgress}%</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-4 h-2 rounded-full bg-zinc-800">
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>

        <div className="space-y-3">
          {mergedSteps.map((step) => {
            const config = STEP_CONFIG[step.name];
            const display = STATUS_DISPLAY[step.status] || STATUS_DISPLAY.pending;
            if (!config) return null;
            const Icon = config.icon;

            return (
              <div
                key={step.name}
                className="flex items-center gap-3 rounded-lg border border-zinc-800/50 p-3"
              >
                <StatusIcon status={step.status} />
                <Icon className={`h-4 w-4 ${display.color}`} />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-zinc-200">{config.label}</span>
                    <Badge className={display.badgeClass}>{STATUS_LABELS[step.status] ?? step.status}</Badge>
                  </div>
                  {step.message && (
                    <p className="mt-1 text-xs text-zinc-500">{step.message}</p>
                  )}
                  {step.status === "running" && step.progress > 0 && (
                    <div className="mt-1 h-1 rounded-full bg-zinc-800">
                      <div
                        className="h-full rounded-full bg-blue-500/60 transition-all"
                        style={{ width: `${step.progress}%` }}
                      />
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
