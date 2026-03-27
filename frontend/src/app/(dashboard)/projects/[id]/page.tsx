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
import { PipelineProgress } from "@/components/pipeline-progress";
import { usePipelineSSE } from "@/hooks/use-pipeline-sse";
import { apiClient } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900 text-blue-300",
  completed: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
  cancelled: "bg-yellow-900 text-yellow-300",
};

interface PipelineStep {
  name: string;
  status: string;
  progress: number;
  message?: string;
}

interface Project {
  id: number;
  title: string;
  type: string;
  status: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface PipelineStatus {
  project: Project;
  steps: PipelineStep[];
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

  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  const isRunning = pipelineStatus?.project.status === "running";

  const { events, isConnected } = usePipelineSSE({
    projectId,
    enabled: isRunning,
  });

  useEffect(() => {
    async function fetchStatus() {
      try {
        const data = await apiClient(`/api/pipeline/${projectId}/status`);
        setPipelineStatus(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load project");
      } finally {
        setIsLoading(false);
      }
    }
    fetchStatus();
  }, [projectId]);

  async function handleStart() {
    setIsStarting(true);
    setError(null);
    try {
      await apiClient(`/api/pipeline/${projectId}/start`, { method: "POST" });
      const data = await apiClient(`/api/pipeline/${projectId}/status`);
      setPipelineStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start pipeline");
    } finally {
      setIsStarting(false);
    }
  }

  async function handleCancel() {
    setIsCancelling(true);
    setError(null);
    try {
      await apiClient(`/api/pipeline/${projectId}/cancel`, { method: "POST" });
      const data = await apiClient(`/api/pipeline/${projectId}/status`);
      setPipelineStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to cancel pipeline");
    } finally {
      setIsCancelling(false);
    }
  }

  if (isLoading) return <ProjectSkeleton />;

  if (error && !pipelineStatus) {
    return (
      <div className="space-y-4">
        <Link href="/dashboard">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </Link>
        <Card className="border-red-900/50 bg-zinc-900/50">
          <CardContent className="py-8 text-center">
            <p className="text-red-400">{error}</p>
            <Button variant="ghost" className="mt-4" onClick={() => router.refresh()}>
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const project = pipelineStatus?.project;
  const steps = pipelineStatus?.steps ?? [];

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
                {project?.status ?? "draft"}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-zinc-400">
              {project?.type === "shorts" ? "Shorts" : "Long-form"} &middot; Created{" "}
              {project ? new Date(project.created_at).toLocaleDateString() : ""}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {!isRunning && project?.status !== "completed" && (
            <Button onClick={handleStart} disabled={isStarting}>
              <Play className="mr-2 h-4 w-4" />
              {isStarting ? "Starting..." : "Start Pipeline"}
            </Button>
          )}
          {isRunning && (
            <Button variant="destructive" onClick={handleCancel} disabled={isCancelling}>
              <Square className="mr-2 h-4 w-4" />
              {isCancelling ? "Cancelling..." : "Cancel"}
            </Button>
          )}
          {project?.status === "completed" && (
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
          )}
        </div>
      </div>

      {error && (
        <p className="text-sm text-red-400">{error}</p>
      )}

      {steps.length > 0 && (
        <PipelineProgress
          steps={steps}
          events={events}
          isConnected={isConnected}
        />
      )}

      {project?.status === "completed" && (
        <Card className="border-zinc-800 bg-zinc-900/50">
          <CardHeader>
            <CardTitle className="text-sm font-medium text-zinc-400">Output</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-500">
              Video and assets will appear here once available.
            </p>
          </CardContent>
        </Card>
      )}

      <Card className="border-zinc-800 bg-zinc-900/50">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-zinc-400">Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-auto rounded-lg bg-zinc-950 p-4 text-xs text-zinc-400">
            {JSON.stringify(project?.config ?? {}, null, 2)}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
