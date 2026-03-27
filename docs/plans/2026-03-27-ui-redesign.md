# AutoTube UI Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** AutoTube만의 보라/인디고 그라디언트 아이덴티티를 적용하고, WakaShorts 스타일의 홈 화면(큰 시작 카드 2개 + 최근 영상 미리보기 + 통계)과 개선된 위자드 UI를 구현한다.

**Architecture:** globals.css에서 CSS 변수로 보라 계열 primary 컬러를 정의하고, 대시보드 레이아웃 사이드바, 홈 페이지, 프로젝트 생성 위자드 순으로 개선한다. 새 컴포넌트는 최소한으로 유지하고 기존 shadcn 컴포넌트를 최대한 재사용한다.

**Tech Stack:** Next.js 16 App Router, Tailwind CSS v4, shadcn/ui, lucide-react, Clerk

---

## 변경 대상 파일 요약

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/app/globals.css` | primary 컬러 → 보라 계열 OKLCH 값으로 교체 |
| `frontend/src/app/(dashboard)/layout.tsx` | 로고 그라디언트, 사이드바 active 스타일 보라로 변경, nav 항목 추가 |
| `frontend/src/app/(dashboard)/dashboard/page.tsx` | 홈 화면 완전 재설계 (환영 + 큰 카드 2개 + 최근 영상 카드 + 통계 + 전체 테이블) |
| `frontend/src/app/(dashboard)/projects/new/page.tsx` | 위자드 step indicator 번호형으로, 타입 카드 그라디언트 선택 상태 적용 |

---

## Task 1: CSS 변수 — 보라/인디고 primary 컬러 적용

**Files:**
- Modify: `frontend/src/app/globals.css`

**목표:** `--primary`를 보라(violet) OKLCH 값으로 교체하고, 그라디언트 유틸리티 변수 추가.

**Step 1: .dark 섹션의 primary 변수 교체**

`globals.css` 86-118줄 `.dark` 블록에서:
```css
/* 변경 전 */
--primary: oklch(0.922 0 0);
--primary-foreground: oklch(0.205 0 0);

/* 변경 후 */
--primary: oklch(0.567 0.225 293.5);        /* violet-600 계열 */
--primary-foreground: oklch(0.985 0 0);
```

또한 `.dark` 블록 끝에 그라디언트용 변수 추가:
```css
--gradient-from: oklch(0.567 0.225 293.5);  /* violet-600 */
--gradient-to: oklch(0.511 0.262 276.5);    /* indigo-600 */
```

**Step 2: :root 섹션의 primary도 교체 (light mode fallback)**

```css
/* 변경 전 */
--primary: oklch(0.205 0 0);
--primary-foreground: oklch(0.985 0 0);

/* 변경 후 */
--primary: oklch(0.567 0.225 293.5);
--primary-foreground: oklch(0.985 0 0);
```

**Step 3: @layer base 아래에 그라디언트 유틸리티 추가**

```css
@layer utilities {
  .gradient-brand {
    background: linear-gradient(135deg, var(--gradient-from), var(--gradient-to));
  }
  .gradient-brand-text {
    background: linear-gradient(135deg, oklch(0.75 0.18 293.5), oklch(0.70 0.22 276.5));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
}
```

**Step 4: 개발 서버에서 시각적으로 확인 (기존 버튼들이 보라색으로 바뀌는지)**

---

## Task 2: 사이드바 레이아웃 — 로고 + 액티브 스타일 개선

**Files:**
- Modify: `frontend/src/app/(dashboard)/layout.tsx`

**목표:** AutoTube 로고에 그라디언트 아이콘, active nav 아이템을 보라 계열로.

**Step 1: Film 아이콘 → 로고 섹션 교체**

기존:
```tsx
<Film className="h-5 w-5 text-blue-500" />
<span className="text-lg font-semibold text-zinc-50">AutoTube</span>
```

변경 후:
```tsx
<div className="flex h-7 w-7 items-center justify-center rounded-lg gradient-brand">
  <Film className="h-4 w-4 text-white" />
</div>
<span className="text-lg font-semibold gradient-brand-text">AutoTube</span>
```

(모바일 헤더의 로고도 동일하게 교체)

**Step 2: NavLinks active 스타일 교체**

기존:
```tsx
isActive
  ? "bg-zinc-800 text-zinc-50"
  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
```

변경 후:
```tsx
isActive
  ? "bg-violet-950/60 text-violet-200 border border-violet-800/40"
  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
```

**Step 3: 아이콘 색상도 active 시 보라로**

```tsx
<Icon className={`h-4 w-4 ${isActive ? "text-violet-400" : ""}`} />
```

**Step 4: 시각적 확인**

---

## Task 3: 대시보드 홈 페이지 완전 재설계

**Files:**
- Modify: `frontend/src/app/(dashboard)/dashboard/page.tsx`

**목표:** WakaShorts 스타일의 홈 화면. 아래 레이아웃 구현:
1. 환영 헤더 ("오늘은 어떤 영상을 만들까요?")
2. 큰 시작 카드 2개 (Shorts / Long-form) — 그라디언트 호버
3. 최근 영상 미리보기 카드 3개 (있을 때만)
4. 통계 3개 (이번 달 생성 수 / 완료 / 실패)
5. 전체 프로젝트 테이블 (현재 것 유지)

**Step 1: 임포트 및 상수 업데이트**

```tsx
"use client";

import Link from "next/link";
import { Plus, Film, Video, Clock, CheckCircle2, XCircle, ArrowRight, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
```

**Step 2: 새 컴포넌트 — WelcomeSection**

```tsx
function WelcomeSection() {
  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-bold text-zinc-50">
        오늘은 어떤 영상을 만들까요? 🎬
      </h1>
      <p className="text-sm text-zinc-400">
        AI가 스크립트부터 자막까지 자동으로 생성해드립니다.
      </p>
    </div>
  );
}
```

**Step 3: 새 컴포넌트 — StartCards (Shorts / Long-form 두 큰 카드)**

```tsx
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
    badgeClass: "bg-violet-950 text-violet-300 border-violet-800/40",
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
    badgeClass: "bg-indigo-950 text-indigo-300 border-indigo-800/40",
  },
] as const;

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
              <div className={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl ${opt.iconBg}`}>
                <Icon className={`h-6 w-6 ${opt.iconColor}`} />
              </div>
              <div className="space-y-1">
                <div className="text-lg font-semibold text-zinc-100">{opt.label}</div>
                <div className="text-sm font-medium text-zinc-300">{opt.description}</div>
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
```

**Step 4: 새 컴포넌트 — RecentProjects (최근 3개 카드)**

```tsx
function RecentProjectCard({ project }: { project: Project }) {
  const statusIcon = {
    completed: <CheckCircle2 className="h-4 w-4 text-green-400" />,
    running: <Clock className="h-4 w-4 text-blue-400 animate-spin" />,
    failed: <XCircle className="h-4 w-4 text-red-400" />,
    draft: <Clock className="h-4 w-4 text-zinc-500" />,
  }[project.status] ?? <Clock className="h-4 w-4 text-zinc-500" />;

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="border-zinc-800 bg-zinc-900/50 transition-colors hover:border-zinc-700 hover:bg-zinc-800/50 cursor-pointer h-full">
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-medium text-zinc-200">{project.title}</p>
              <p className="text-xs text-zinc-500 mt-1">
                {new Date(project.created_at).toLocaleDateString("ko-KR")}
              </p>
            </div>
            {statusIcon}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-xs">
              {TYPE_LABELS[project.type] || project.type}
            </Badge>
            <Badge className={`text-xs ${STATUS_COLORS[project.status] || STATUS_COLORS.draft}`}>
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
        <Link href="#all-projects" className="text-xs text-violet-400 hover:text-violet-300">
          전체 보기 →
        </Link>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {recent.map((p) => <RecentProjectCard key={p.id} project={p} />)}
      </div>
    </div>
  );
}
```

**Step 5: 새 컴포넌트 — StatsRow (통계 3개)**

```tsx
function StatsRow({ projects }: { projects: Project[] }) {
  const total = projects.length;
  const completed = projects.filter((p) => p.status === "completed").length;
  const failed = projects.filter((p) => p.status === "failed").length;

  const stats = [
    { label: "이번 달 생성", value: total, icon: Film, color: "text-violet-400" },
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
              <div className="mt-1 text-2xl font-bold text-zinc-50">{stat.value}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
```

**Step 6: DashboardPage 메인 함수 재작성**

```tsx
export default function DashboardPage() {
  const projects: Project[] = [];

  return (
    <div className="space-y-8">
      <WelcomeSection />
      <StartCards />
      <RecentProjects projects={projects} />
      <StatsRow projects={projects} />

      {/* 전체 프로젝트 목록 */}
      <div id="all-projects" className="space-y-3">
        <h2 className="text-sm font-medium text-zinc-400">전체 프로젝트</h2>
        {projects.length === 0 ? (
          <EmptyState />
        ) : (
          <ProjectTable projects={projects} />
        )}
      </div>
    </div>
  );
}
```

**Step 7: EmptyState도 보라 계열로 업데이트**

```tsx
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
        <p className="mb-6 text-sm text-zinc-500">
          위에서 영상 타입을 선택해 첫 번째 영상을 만들어보세요.
        </p>
      </CardContent>
    </Card>
  );
}
```

---

## Task 4: 프로젝트 생성 위자드 UI 개선

**Files:**
- Modify: `frontend/src/app/(dashboard)/projects/new/page.tsx`

**목표:** WakaShorts 스타일의 번호형 step indicator, 타입 카드 그라디언트 선택 상태.

**Step 1: StepIndicator → 번호형으로 교체**

기존 바(bar) 형태 대신 WakaShorts처럼 "01 → 02 → 03 → 04" 형태:

```tsx
const STEP_LABELS = ["영상 타입", "제목/주제", "파이프라인", "최종 확인"] as const;

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-2">
      {Array.from({ length: total }, (_, i) => {
        const isDone = i < current;
        const isActive = i === current;
        const num = String(i + 1).padStart(2, "0");
        return (
          <div key={i} className="flex items-center gap-2">
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
                  isActive ? "text-zinc-200 font-medium" : isDone ? "text-zinc-400" : "text-zinc-600"
                }`}
              >
                {STEP_LABELS[i]}
              </span>
            </div>
            {i < total - 1 && (
              <div className={`h-px w-8 ${i < current ? "bg-violet-600" : "bg-zinc-800"}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
```

**Step 2: StepType 카드 — 선택 상태 그라디언트로**

기존:
```tsx
isSelected
  ? "border-blue-500 bg-blue-950/30"
  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
```

변경 후:
```tsx
isSelected
  ? "border-violet-500/60 bg-gradient-to-br from-violet-950/60 to-indigo-950/60 shadow-sm shadow-violet-900/30"
  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
```

아이콘 색상:
```tsx
isSelected ? "text-violet-400" : "text-zinc-500"
```

**Step 3: StepPipeline 토글 — 활성 상태 보라로**

활성화된 step row에 left border 강조:

```tsx
<div
  key={step.key}
  className={`flex items-center justify-between rounded-lg border p-4 transition-colors ${
    formData.steps[step.key]
      ? "border-violet-800/40 bg-violet-950/20"
      : "border-zinc-800 bg-zinc-900/50"
  }`}
>
```

**Step 4: 페이지 헤더 — step 번호 표시 개선**

```tsx
<div className="space-y-4">
  <div>
    <h1 className="text-2xl font-bold text-zinc-50">새 영상 만들기</h1>
    <p className="mt-1 text-sm text-zinc-500">
      {STEP_LABELS[step]}
    </p>
  </div>
  <StepIndicator current={step} total={TOTAL_STEPS} />
</div>
```

**Step 5: Next/Create 버튼 — 그라디언트 스타일 확인**

primary 버튼이 이미 CSS 변수에 의해 보라색이 됐을 것이므로 별도 수정 불필요. 확인만.

---

## Task 5: URL 파라미터로 타입 프리셀렉트 (StartCards → NewProjectPage 연결)

**Files:**
- Modify: `frontend/src/app/(dashboard)/projects/new/page.tsx`

**목표:** `/projects/new?type=shorts` 로 접근 시 첫 번째 단계를 건너뛰거나 타입이 미리 선택되도록.

**Step 1: useSearchParams로 초기 타입 읽기**

```tsx
import { useSearchParams } from "next/navigation";

// NewProjectPage 내부
const searchParams = useSearchParams();
const initialType = searchParams.get("type") ?? "shorts";

const [formData, setFormData] = useState<FormData>({
  ...DEFAULT_FORM_DATA,
  type: initialType as FormData["type"],
});
```

**Step 2: type이 URL로 전달된 경우 step 0을 건너뜀**

```tsx
// step 초기값: type이 명시된 경우 1번 단계부터
const [step, setStep] = useState(searchParams.get("type") ? 1 : 0);
```

---

## 구현 순서 및 커밋 전략

```
Task 1 → commit "style: apply violet/indigo brand colors as primary"
Task 2 → commit "feat: update sidebar logo and active nav styles"
Task 3 → commit "feat: redesign dashboard home with start cards and stats"
Task 4 → commit "feat: redesign project wizard with numbered steps"
Task 5 → commit "feat: pre-select video type from URL param"
```

---

## 검증 방법

각 Task 완료 후:
1. `cd frontend && npm run dev` 실행
2. http://localhost:3000/dashboard 접속
3. 시각적으로 확인:
   - Task 1: 버튼들이 보라색으로 변경됨
   - Task 2: 사이드바 로고에 그라디언트, active 링크 보라 배경
   - Task 3: 환영 메시지 + Shorts/Long-form 카드 2개 + 통계 행 보임
   - Task 4: 위자드에서 "01 → 02 → 03 → 04" 번호형 step
   - Task 5: `/projects/new?type=shorts` 접속 시 step 1부터 시작

---

## 주의사항

- `globals.css`의 OKLCH 값은 정확히 명시된 값 사용 (CSS calc로 변환 X)
- `gradient-brand`는 Tailwind utility로 정의되므로 className에 직접 사용 가능
- `gradient-brand-text`는 `-webkit-text-fill-color` 사용으로 일부 브라우저에서 확인 필요
- 모바일 레이아웃: StepIndicator의 STEP_LABELS는 `hidden sm:block`으로 처리
- StatsRow의 날짜 필터링은 현재 mock 데이터 기준이므로 추후 API 연결 시 수정 필요
