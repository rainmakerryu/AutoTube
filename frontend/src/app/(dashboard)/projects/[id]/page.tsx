"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Play,
  Square,
  Download,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { PipelineWizard } from "@/components/pipeline-wizard";
import { apiClient } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900 text-blue-300",
  reviewing: "bg-violet-900 text-violet-300",
  completed: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
  cancelled: "bg-yellow-900 text-yellow-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "초안",
  running: "진행 중",
  reviewing: "검토 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

const TYPE_LABELS: Record<string, string> = {
  shorts: "Shorts",
  longform: "Long-form",
};

interface StepInfo {
  step: string;
  status: string;
  provider?: string | null;
  error_message?: string | null;
}

interface Project {
  id: number;
  title: string;
  type: string;
  topic: string;
  status: string;
  pipeline_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

function ProjectSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64 bg-zinc-800" />
      <Skeleton className="h-48 w-full bg-zinc-800" />
      <Skeleton className="h-64 w-full bg-zinc-800" />
    </div>
  );
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<Project | null>(null);
  const [pipelineSteps, setPipelineSteps] = useState<StepInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const isPipelineActive = pipelineSteps.length > 0 && project?.status !== "draft";

  useEffect(() => {
    async function fetchData() {
      try {
        // 프로젝트 정보와 파이프라인 상태를 함께 조회
        const [projectData, pipelineData] = await Promise.all([
          apiClient(`/api/projects/${projectId}`),
          apiClient(`/api/pipeline/${projectId}/status`).catch(() => null),
        ]);
        setProject(projectData);
        if (pipelineData?.steps) {
          setPipelineSteps(pipelineData.steps);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "프로젝트를 불러오지 못했습니다");
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [projectId]);

  async function handleStart() {
    setIsStarting(true);
    setError(null);
    try {
      await apiClient(`/api/pipeline/${projectId}/start`, { method: "POST" });
      // 파이프라인 시작 후 상태 갱신
      const pipelineData = await apiClient(`/api/pipeline/${projectId}/status`);
      setPipelineSteps(pipelineData.steps ?? []);
      setProject((prev) => prev ? { ...prev, status: "running" } : prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : "파이프라인 시작에 실패했습니다");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleCancel() {
    setIsCancelling(true);
    setError(null);
    try {
      await apiClient(`/api/pipeline/${projectId}/cancel`, { method: "POST" });
      const pipelineData = await apiClient(`/api/pipeline/${projectId}/status`);
      setPipelineSteps(pipelineData.steps ?? []);
      setProject((prev) => prev ? { ...prev, status: "cancelled" } : prev);
    } catch (err) {
      setError(err instanceof Error ? err.message : "파이프라인 취소에 실패했습니다");
    } finally {
      setIsCancelling(false);
    }
  }

  if (isLoading) return <ProjectSkeleton />;

  if (error && !project) {
    return (
      <div className="space-y-4">
        <Link href="/dashboard">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            뒤로
          </Button>
        </Link>
        <Card className="border-red-900/50 bg-zinc-900/50">
          <CardContent className="py-8 text-center">
            <p className="text-red-400">{error}</p>
            <Button variant="ghost" className="mt-4" onClick={() => router.refresh()}>
              다시 시도
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold text-zinc-50">
                {project?.title ?? "Project"}
              </h1>
              <Badge className={STATUS_COLORS[project?.status ?? "draft"]}>
                {STATUS_LABELS[project?.status ?? "draft"] ?? project?.status}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-zinc-400">
              {TYPE_LABELS[project?.type ?? ""] ?? project?.type} &middot; 생성일{" "}
              {project ? new Date(project.created_at).toLocaleDateString("ko-KR") : ""}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {!isPipelineActive && project?.status !== "completed" && (
            <Button onClick={handleStart} disabled={isStarting}>
              <Play className="mr-2 h-4 w-4" />
              {isStarting ? "시작 중..." : "파이프라인 시작"}
            </Button>
          )}
          {isPipelineActive && project?.status !== "completed" && project?.status !== "cancelled" && (
            <Button variant="destructive" onClick={handleCancel} disabled={isCancelling}>
              <Square className="mr-2 h-4 w-4" />
              {isCancelling ? "취소 중..." : "취소"}
            </Button>
          )}
          {project?.status === "completed" && (
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              다운로드
            </Button>
          )}
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {isPipelineActive && (
        <PipelineWizard
          projectId={projectId}
          initialSteps={pipelineSteps}
        />
      )}

      {project?.status === "completed" && (
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-400">출력물</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-500">
              영상과 에셋이 준비되면 여기에 표시됩니다.
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-400">설정 정보</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-auto rounded-lg bg-zinc-950 p-4 text-xs text-zinc-400">
            {JSON.stringify(project?.pipeline_config ?? {}, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
