"use client";

import Link from "next/link";
import { Film, Video, Clock, CheckCircle2, XCircle, ArrowRight, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900 text-blue-300",
  completed: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
  cancelled: "bg-yellow-900 text-yellow-300",
};

const TYPE_LABELS: Record<string, string> = {
  shorts: "Shorts",
  longform: "Long-form",
};

interface Project {
  id: number;
  title: string;
  type: string;
  status: string;
  created_at: string;
}

const START_OPTIONS = [
  {
    type: "shorts",
    label: "Shorts 만들기",
    description: "세로 60초 숏폼",
    detail: "YouTube Shorts, TikTok, Reels 최적화",
    icon: Zap,
    gradient: "from-violet-600/20 to-indigo-600/20",
    border: "border-violet-800/40",
    hoverBorder: "hover:border-violet-600/60",
    iconBg: "bg-violet-950/60",
    iconColor: "text-violet-400",
  },
  {
    type: "longform",
    label: "Long-form 만들기",
    description: "가로 5-15분 영상",
    detail: "일반 YouTube 영상, 튜토리얼, 리뷰",
    icon: Video,
    gradient: "from-indigo-600/20 to-blue-600/20",
    border: "border-indigo-800/40",
    hoverBorder: "hover:border-indigo-600/60",
    iconBg: "bg-indigo-950/60",
    iconColor: "text-indigo-400",
  },
] as const;

function WelcomeSection() {
  return (
    <div className="space-y-1">
      <h1 className="text-2xl font-bold text-zinc-50">
        오늘은 어떤 영상을 만들까요?
      </h1>
      <p className="text-sm text-zinc-400">
        AI가 스크립트부터 자막까지 자동으로 생성해드립니다.
      </p>
    </div>
  );
}

function StartCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {START_OPTIONS.map((opt) => {
        const Icon = opt.icon;
        return (
          <Link key={opt.type} href={`/projects/new?type=${opt.type}`}>
            <div
              className={`group relative overflow-hidden rounded-xl border bg-gradient-to-br p-6 transition-all cursor-pointer ${opt.gradient} ${opt.border} ${opt.hoverBorder} hover:shadow-lg hover:shadow-violet-950/20`}
            >
              <div
                className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${opt.iconBg}`}
              >
                <Icon className={`h-6 w-6 ${opt.iconColor}`} />
              </div>
              <div className="space-y-1 pr-8">
                <div className="text-lg font-semibold text-zinc-100">
                  {opt.label}
                </div>
                <div className="text-sm font-medium text-zinc-300">
                  {opt.description}
                </div>
                <div className="text-xs text-zinc-500">{opt.detail}</div>
              </div>
              <ArrowRight className="absolute right-4 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-600 transition-transform group-hover:translate-x-1 group-hover:text-zinc-400" />
            </div>
          </Link>
        );
      })}
    </div>
  );
}

function RecentProjectCard({ project }: { project: Project }) {
  const statusIcon =
    project.status === "completed" ? (
      <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />
    ) : project.status === "running" ? (
      <Clock className="h-4 w-4 text-blue-400 animate-spin shrink-0" />
    ) : project.status === "failed" ? (
      <XCircle className="h-4 w-4 text-red-400 shrink-0" />
    ) : (
      <Clock className="h-4 w-4 text-zinc-500 shrink-0" />
    );

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="border-zinc-800 bg-zinc-900/50 transition-colors hover:border-zinc-700 hover:bg-zinc-800/50 cursor-pointer h-full">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-2">
            <p className="truncate text-sm font-medium text-zinc-200">
              {project.title}
            </p>
            {statusIcon}
          </div>
          <p className="text-xs text-zinc-500 mt-1">
            {new Date(project.created_at).toLocaleDateString("ko-KR")}
          </p>
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <Badge
              variant="outline"
              className="border-zinc-700 text-zinc-400 text-xs"
            >
              {TYPE_LABELS[project.type] || project.type}
            </Badge>
            <Badge
              className={`text-xs ${STATUS_COLORS[project.status] || STATUS_COLORS.draft}`}
            >
              {project.status}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

function RecentProjects({ projects }: { projects: Project[] }) {
  if (projects.length === 0) return null;
  const recent = projects.slice(0, 3);
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium text-zinc-400">최근 생성된 영상</h2>
        <a
          href="#all-projects"
          className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
        >
          전체 보기 →
        </a>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {recent.map((p) => (
          <RecentProjectCard key={p.id} project={p} />
        ))}
      </div>
    </div>
  );
}

function StatsRow({ projects }: { projects: Project[] }) {
  const total = projects.length;
  const completed = projects.filter((p) => p.status === "completed").length;
  const failed = projects.filter((p) => p.status === "failed").length;

  const stats = [
    { label: "전체 생성", value: total, icon: Film, color: "text-violet-400" },
    {
      label: "완료",
      value: completed,
      icon: CheckCircle2,
      color: "text-green-400",
    },
    { label: "실패", value: failed, icon: XCircle, color: "text-red-400" },
  ] as const;

  return (
    <div className="grid grid-cols-3 gap-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.label} className="border-zinc-800 bg-zinc-900/50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2">
                <Icon className={`h-4 w-4 ${stat.color}`} />
                <span className="text-xs text-zinc-400">{stat.label}</span>
              </div>
              <div className="mt-1 text-2xl font-bold text-zinc-50">
                {stat.value}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="border-dashed border-zinc-700 bg-zinc-900/50">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl gradient-brand opacity-80">
          <Film className="h-8 w-8 text-white" />
        </div>
        <h3 className="mb-2 text-lg font-medium text-zinc-300">
          아직 생성된 영상이 없습니다
        </h3>
        <p className="text-sm text-zinc-500">
          위에서 영상 타입을 선택해 첫 번째 영상을 만들어보세요.
        </p>
      </CardContent>
    </Card>
  );
}

function ProjectTable({ projects }: { projects: Project[] }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900/50">
      <Table>
        <TableHeader>
          <TableRow className="border-zinc-800 hover:bg-transparent">
            <TableHead className="text-zinc-400">제목</TableHead>
            <TableHead className="text-zinc-400">타입</TableHead>
            <TableHead className="text-zinc-400">상태</TableHead>
            <TableHead className="text-right text-zinc-400">생성일</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {projects.map((project) => (
            <TableRow
              key={project.id}
              className="border-zinc-800 hover:bg-zinc-800/50"
            >
              <TableCell>
                <Link
                  href={`/projects/${project.id}`}
                  className="font-medium text-zinc-200 hover:text-zinc-50"
                >
                  {project.title}
                </Link>
              </TableCell>
              <TableCell>
                <Badge
                  variant="outline"
                  className="border-zinc-700 text-zinc-400"
                >
                  {TYPE_LABELS[project.type] || project.type}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge
                  className={
                    STATUS_COLORS[project.status] || STATUS_COLORS.draft
                  }
                >
                  {project.status}
                </Badge>
              </TableCell>
              <TableCell className="text-right text-zinc-500">
                {new Date(project.created_at).toLocaleDateString("ko-KR")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

export default function DashboardPage() {
  // TODO: Fetch projects from API with auth
  const projects: Project[] = [];

  return (
    <div className="space-y-8">
      <WelcomeSection />
      <StartCards />
      <RecentProjects projects={projects} />
      <StatsRow projects={projects} />

      <div id="all-projects" className="space-y-3">
        <h2 className="text-sm font-medium text-zinc-400">전체 프로젝트</h2>
        {projects.length === 0 ? <EmptyState /> : <ProjectTable projects={projects} />}
      </div>
    </div>
  );
}
