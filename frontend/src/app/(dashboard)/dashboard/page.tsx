"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Film,
  Video,
  Clock,
  CheckCircle2,
  XCircle,
  ArrowRight,
  Zap,
  Loader2,
  Search,
  Mic,
  Tag,
  ImagePlus,
  Clapperboard,
  Captions,
  ScrollText,
} from "lucide-react";
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
import { apiClient } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  running: "bg-blue-900 text-blue-300",
  completed: "bg-green-900 text-green-300",
  failed: "bg-red-900 text-red-300",
  cancelled: "bg-yellow-900 text-yellow-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "초안",
  running: "진행 중",
  completed: "완료",
  failed: "실패",
  cancelled: "취소됨",
};

const TYPE_LABELS: Record<string, string> = {
  shorts: "Shorts",
  longform: "Long-form",
};

type FilterKey = "all" | "shorts" | "longform" | "running" | "completed";

const FILTER_TABS: { key: FilterKey; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "shorts", label: "Shorts" },
  { key: "longform", label: "Long-form" },
  { key: "running", label: "진행 중" },
  { key: "completed", label: "완료" },
];

interface Project {
  id: number;
  title: string;
  type: string;
  status: string;
  created_at: string;
}

// ──────────────────────────────────────────────
// 영상 생성 파이프라인 도구 목록 (Kling의 Video Generation 상당)
// ──────────────────────────────────────────────
const PIPELINE_TOOLS = [
  {
    key: "script",
    label: "스크립트 생성",
    description: "주제 → AI 대본 자동 작성",
    icon: ScrollText,
    badge: null,
    color: "text-violet-400",
    bg: "bg-violet-950/40",
    border: "border-violet-800/30",
  },
  {
    key: "tts",
    label: "텍스트 → 음성",
    description: "TTS 음성 합성 (ElevenLabs / OpenAI / Edge TTS)",
    icon: Mic,
    badge: "HOT",
    color: "text-blue-400",
    bg: "bg-blue-950/40",
    border: "border-blue-800/30",
  },
  {
    key: "images",
    label: "이미지 생성",
    description: "AI 생성 또는 스톡 이미지 수집",
    icon: ImagePlus,
    badge: null,
    color: "text-emerald-400",
    bg: "bg-emerald-950/40",
    border: "border-emerald-800/30",
  },
  {
    key: "video",
    label: "영상 합성",
    description: "켄 번즈 효과로 장면 조합",
    icon: Clapperboard,
    badge: null,
    color: "text-orange-400",
    bg: "bg-orange-950/40",
    border: "border-orange-800/30",
  },
  {
    key: "subtitle",
    label: "자막 생성",
    description: "Whisper 자동 자막 & SRT 출력",
    icon: Captions,
    badge: "NEW",
    color: "text-pink-400",
    bg: "bg-pink-950/40",
    border: "border-pink-800/30",
  },
  {
    key: "metadata",
    label: "메타데이터",
    description: "AI 제목 · 설명 · 태그 생성",
    icon: Tag,
    badge: null,
    color: "text-yellow-400",
    bg: "bg-yellow-950/40",
    border: "border-yellow-800/30",
  },
] as const;

// ──────────────────────────────────────────────
// 지원 AI 서비스 목록 (Kling의 Recommended Models 상당)
// ──────────────────────────────────────────────
const AI_SERVICES = [
  {
    key: "openai",
    name: "OpenAI",
    models: "GPT · DALL-E · Whisper",
    desc: "스크립트·이미지·자막",
    badge: "GPT",
    badgeColor: "bg-green-900/60 text-green-300",
  },
  {
    key: "claude",
    name: "Anthropic Claude",
    models: "Claude 3.5 / 4",
    desc: "스크립트·메타데이터 생성",
    badge: "AI",
    badgeColor: "bg-orange-900/60 text-orange-300",
  },
  {
    key: "gemini",
    name: "Google Gemini",
    models: "Gemini Pro",
    desc: "이미지 생성",
    badge: "GEM",
    badgeColor: "bg-blue-900/60 text-blue-300",
  },
  {
    key: "elevenlabs",
    name: "ElevenLabs",
    models: "Multilingual v2",
    desc: "고품질 텍스트 음성 변환",
    badge: "TTS",
    badgeColor: "bg-violet-900/60 text-violet-300",
  },
  {
    key: "pexels",
    name: "Pexels",
    models: "Stock Photos & Video",
    desc: "무료 스톡 이미지·영상",
    badge: "PX",
    badgeColor: "bg-teal-900/60 text-teal-300",
  },
  {
    key: "whisper",
    name: "OpenAI Whisper",
    models: "Whisper v3",
    desc: "음성 인식 및 자막 생성",
    badge: "STT",
    badgeColor: "bg-zinc-700/60 text-zinc-300",
  },
  {
    key: "deepseek",
    name: "DeepSeek",
    models: "DeepSeek Chat",
    desc: "무료/저가 스크립트·메타데이터",
    badge: "무료",
    badgeColor: "bg-emerald-900/60 text-emerald-300",
  },
  {
    key: "ollama",
    name: "Ollama (로컬)",
    models: "LLaMA 3 등",
    desc: "로컬 LLM — API 비용 없음",
    badge: "무료",
    badgeColor: "bg-emerald-900/60 text-emerald-300",
  },
  {
    key: "edgetts",
    name: "Edge TTS",
    models: "Microsoft Neural TTS",
    desc: "무료 음성 합성 — 키 불필요",
    badge: "무료",
    badgeColor: "bg-emerald-900/60 text-emerald-300",
  },
  {
    key: "comfyui",
    name: "ComfyUI (로컬)",
    models: "SDXL + IP-Adapter",
    desc: "로컬 이미지 생성 — 스타일 일관성",
    badge: "무료",
    badgeColor: "bg-emerald-900/60 text-emerald-300",
  },
] as const;

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

// ──────────────────────────────────────────────
// 컴포넌트
// ──────────────────────────────────────────────

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

function PipelineTools() {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-zinc-400">영상 생성 파이프라인</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {PIPELINE_TOOLS.map((tool) => {
          const Icon = tool.icon;
          return (
            <Link key={tool.key} href={`/projects/new`}>
              <div
                className={`group relative flex flex-col items-center gap-2 rounded-xl border p-4 text-center transition-all cursor-pointer hover:bg-zinc-800/60 ${tool.border} bg-zinc-900/50`}
              >
                {tool.badge && (
                  <span
                    className={`absolute -top-1.5 right-2 rounded-full px-1.5 py-0.5 text-[10px] font-bold ${
                      tool.badge === "HOT"
                        ? "bg-red-900/80 text-red-300"
                        : "bg-emerald-900/80 text-emerald-300"
                    }`}
                  >
                    {tool.badge}
                  </span>
                )}
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${tool.bg}`}
                >
                  <Icon className={`h-5 w-5 ${tool.color}`} />
                </div>
                <div className="text-xs font-medium text-zinc-200 leading-tight">
                  {tool.label}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

function AiServices() {
  return (
    <div className="space-y-3">
      <h2 className="text-sm font-medium text-zinc-400">지원 AI 서비스</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {AI_SERVICES.map((svc) => (
          <Link key={svc.key} href="/settings">
            <div className="group flex flex-col items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-center transition-all hover:border-zinc-700 hover:bg-zinc-800/60 cursor-pointer">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-800/60">
                <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-bold ${svc.badgeColor}`}>
                  {svc.badge}
                </span>
              </div>
              <div>
                <div className="text-xs font-medium text-zinc-200 leading-tight">
                  {svc.name}
                </div>
                <div className="mt-0.5 text-[10px] text-zinc-500 leading-tight">
                  {svc.desc}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function RecentProjectCard({ project }: { project: Project }) {
  const statusIcon =
    project.status === "completed" ? (
      <CheckCircle2 className="h-4 w-4 text-green-400 shrink-0" />
    ) : project.status === "running" ? (
      <Loader2 className="h-4 w-4 text-blue-400 animate-spin shrink-0" />
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
              {STATUS_LABELS[project.status] ?? project.status}
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
    { label: "완료", value: completed, icon: CheckCircle2, color: "text-green-400" },
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

function FilterTabs({
  activeFilter,
  onFilterChange,
  searchQuery,
  onSearchChange,
  projects,
}: {
  activeFilter: FilterKey;
  onFilterChange: (filter: FilterKey) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  projects: Project[];
}) {
  const counts: Record<FilterKey, number> = {
    all: projects.length,
    shorts: projects.filter((p) => p.type === "shorts").length,
    longform: projects.filter((p) => p.type === "longform").length,
    running: projects.filter((p) => p.status === "running").length,
    completed: projects.filter((p) => p.status === "completed").length,
  };

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-1 overflow-x-auto pb-1">
        {FILTER_TABS.map((tab) => {
          const isActive = activeFilter === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => onFilterChange(tab.key)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-violet-950/60 text-violet-200 border border-violet-800/40"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
              }`}
            >
              {tab.label}
              <span
                className={`rounded-full px-1.5 py-0.5 text-xs ${
                  isActive
                    ? "bg-violet-900/60 text-violet-300"
                    : "bg-zinc-800 text-zinc-500"
                }`}
              >
                {counts[tab.key]}
              </span>
            </button>
          );
        })}
      </div>

      <div className="relative shrink-0">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
        <input
          type="text"
          placeholder="프로젝트 검색..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="h-8 w-48 rounded-lg border border-zinc-800 bg-zinc-900/50 pl-8 pr-3 text-sm text-zinc-300 placeholder:text-zinc-600 focus:border-violet-700/50 focus:outline-none focus:ring-1 focus:ring-violet-700/30"
        />
      </div>
    </div>
  );
}

function EmptyState({ filtered }: { filtered: boolean }) {
  return (
    <Card className="border-dashed border-zinc-700 bg-zinc-900/50">
      <CardContent className="flex flex-col items-center justify-center py-12">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl gradient-brand opacity-80">
          <Film className="h-8 w-8 text-white" />
        </div>
        <h3 className="mb-2 text-lg font-medium text-zinc-300">
          {filtered
            ? "해당 조건의 프로젝트가 없습니다"
            : "아직 생성된 영상이 없습니다"}
        </h3>
        <p className="text-sm text-zinc-500">
          {filtered
            ? "다른 필터를 선택해보세요."
            : "위에서 영상 타입을 선택해 첫 번째 영상을 만들어보세요."}
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
                  {STATUS_LABELS[project.status] ?? project.status}
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

function filterProjects(
  projects: Project[],
  filter: FilterKey,
  searchQuery: string
): Project[] {
  let result = projects;
  switch (filter) {
    case "shorts":
      result = projects.filter((p) => p.type === "shorts");
      break;
    case "longform":
      result = projects.filter((p) => p.type === "longform");
      break;
    case "running":
      result = projects.filter((p) => p.status === "running");
      break;
    case "completed":
      result = projects.filter((p) => p.status === "completed");
      break;
  }
  if (searchQuery.trim()) {
    const q = searchQuery.toLowerCase();
    result = result.filter((p) => p.title.toLowerCase().includes(q));
  }
  return result;
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<FilterKey>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchProjects = useCallback(async () => {
    try {
      const data = await apiClient("/api/projects");
      setProjects(Array.isArray(data) ? data : []);
    } catch {
      // 인증 전이거나 서버 미연결 시 빈 목록 유지
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const filteredProjects = filterProjects(projects, activeFilter, searchQuery);
  const isFiltered = activeFilter !== "all" || searchQuery.trim().length > 0;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="h-6 w-6 animate-spin text-violet-400" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <WelcomeSection />
      <StartCards />
      <PipelineTools />
      <AiServices />
      <RecentProjects projects={projects} />
      <StatsRow projects={projects} />

      <div id="all-projects" className="space-y-3">
        <h2 className="text-sm font-medium text-zinc-400">전체 프로젝트</h2>
        <FilterTabs
          activeFilter={activeFilter}
          onFilterChange={setActiveFilter}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          projects={projects}
        />
        {filteredProjects.length === 0 ? (
          <EmptyState filtered={isFiltered} />
        ) : (
          <ProjectTable projects={filteredProjects} />
        )}
      </div>
    </div>
  );
}
