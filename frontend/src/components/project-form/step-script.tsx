"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  LANGUAGES,
  PURPOSES,
  TONES,
  SPEECH_STYLES,
  OPENING_CLOSING_MAX_LENGTH,
  type FormData,
  type ScriptConfig,
  type ScriptMode,
} from "./types";

interface StepScriptProps {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}

const EMOTION_TAGS = [
  "[웃음]",
  "[한숨]",
  "[속삭임]",
  "[화남]",
  "[슬픔]",
  "[놀람]",
  "[하품]",
  "[딸꾹]",
] as const;

const TABS: { mode: ScriptMode; label: string }[] = [
  { mode: "basic", label: "기본 설정" },
  { mode: "ai", label: "AI로 작성하기" },
  { mode: "url", label: "URL로 만들기" },
  { mode: "manual", label: "직접 입력하기" },
];

function ChipGroup<T extends string>({
  options,
  value,
  onSelect,
}: {
  options: readonly { id: T; label: string }[];
  value: T;
  onSelect: (id: T) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <button
          key={opt.id}
          type="button"
          onClick={() => onSelect(opt.id)}
          className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
            value === opt.id
              ? "bg-violet-600 text-white"
              : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-300"
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

function updateScript(
  formData: FormData,
  onChange: (data: Partial<FormData>) => void,
  patch: Partial<ScriptConfig>,
) {
  onChange({ script: { ...formData.script, ...patch } });
}

function BasicTab({
  formData,
  onChange,
}: {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-zinc-500">
        제목과 주제만 입력하면 AI가 나머지를 자동으로 설정합니다.
      </p>
      <TitleTopicFields formData={formData} onChange={onChange} />
    </div>
  );
}

function AITab({
  formData,
  onChange,
}: {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}) {
  const s = formData.script;
  return (
    <div className="space-y-5">
      <TitleTopicFields formData={formData} onChange={onChange} />

      {/* 01. 기본 설정 */}
      <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
        <h4 className="text-xs font-semibold text-zinc-400">01. 기본 설정</h4>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">대본 언어</Label>
            <ChipGroup
              options={LANGUAGES}
              value={s.language}
              onSelect={(v) => updateScript(formData, onChange, { language: v })}
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">목적</Label>
            <ChipGroup
              options={PURPOSES}
              value={s.purpose}
              onSelect={(v) => updateScript(formData, onChange, { purpose: v })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label className="text-xs text-zinc-500">톤</Label>
          <ChipGroup
            options={TONES}
            value={s.tone}
            onSelect={(v) => updateScript(formData, onChange, { tone: v })}
          />
        </div>

        <div className="space-y-2">
          <Label className="text-xs text-zinc-500">말투</Label>
          <ChipGroup
            options={SPEECH_STYLES}
            value={s.speechStyle}
            onSelect={(v) =>
              updateScript(formData, onChange, { speechStyle: v })
            }
          />
        </div>
      </div>

      {/* 02. 오프닝/클로징 멘트 */}
      <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
        <h4 className="text-xs font-semibold text-zinc-400">
          02. 오프닝/클로징 멘트
        </h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">오프닝 멘트 (선택)</Label>
            <Textarea
              placeholder="시작 멘트를 입력하세요. 입력하지 않으면 AI가 자동 생성해요"
              rows={2}
              maxLength={OPENING_CLOSING_MAX_LENGTH}
              value={s.openingComment}
              onChange={(e) =>
                updateScript(formData, onChange, {
                  openingComment: e.target.value,
                })
              }
            />
            <span className="text-[10px] text-zinc-600">
              {s.openingComment.length}/{OPENING_CLOSING_MAX_LENGTH}
            </span>
          </div>
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">클로징 멘트 (선택)</Label>
            <Textarea
              placeholder="마무리 멘트를 입력하세요. 입력하지 않으면 AI가 자동 생성해요"
              rows={2}
              maxLength={OPENING_CLOSING_MAX_LENGTH}
              value={s.closingComment}
              onChange={(e) =>
                updateScript(formData, onChange, {
                  closingComment: e.target.value,
                })
              }
            />
            <span className="text-[10px] text-zinc-600">
              {s.closingComment.length}/{OPENING_CLOSING_MAX_LENGTH}
            </span>
          </div>
        </div>
      </div>

      {/* 03. 제품 및 정보 설정 */}
      <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
        <h4 className="text-xs font-semibold text-zinc-400">
          03. 제품 및 정보 설정
        </h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">제품명 (선택)</Label>
            <Textarea
              placeholder="언급할 제품이 있다면 입력하세요"
              rows={3}
              value={s.productName}
              onChange={(e) =>
                updateScript(formData, onChange, {
                  productName: e.target.value,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">
              대본에 들어가야할 정보 (선택)
            </Label>
            <Textarea
              placeholder="꼭 들어가야 할 정보가 있다면 입력해주세요 (예: 제품 특징 등)"
              rows={3}
              value={s.requiredInfo}
              onChange={(e) =>
                updateScript(formData, onChange, {
                  requiredInfo: e.target.value,
                })
              }
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">벤치마킹 (선택)</Label>
            <Textarea
              placeholder="벤치마킹하고 싶은 영상의 대본을 입력하세요"
              rows={3}
              value={s.referenceScript}
              onChange={(e) =>
                updateScript(formData, onChange, {
                  referenceScript: e.target.value,
                })
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function URLTab({
  formData,
  onChange,
}: {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}) {
  const s = formData.script;
  return (
    <div className="space-y-4">
      <p className="text-xs text-zinc-500">
        웹 기사나 블로그 URL을 입력하면 AI가 내용을 분석하여 영상 대본을
        자동으로 생성합니다.
      </p>
      <div className="space-y-2">
        <Label htmlFor="url-title">제목</Label>
        <Input
          id="url-title"
          placeholder="내 영상 제목"
          value={s.title}
          onChange={(e) =>
            updateScript(formData, onChange, { title: e.target.value })
          }
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="source-url">기사/블로그 URL</Label>
        <Input
          id="source-url"
          type="url"
          placeholder="https://example.com/article/..."
          value={s.sourceUrl}
          onChange={(e) =>
            updateScript(formData, onChange, { sourceUrl: e.target.value })
          }
        />
        <p className="text-xs text-zinc-500">
          기사, 블로그, 뉴스 등의 URL을 입력하세요. AI가 내용을 추출하여 영상
          대본으로 변환합니다.
        </p>
      </div>

      {/* 기본 설정 (언어, 톤 등) */}
      <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
        <h4 className="text-xs font-semibold text-zinc-400">대본 스타일</h4>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">대본 언어</Label>
            <ChipGroup
              options={LANGUAGES}
              value={s.language}
              onSelect={(v) =>
                updateScript(formData, onChange, { language: v })
              }
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs text-zinc-500">톤</Label>
            <ChipGroup
              options={TONES}
              value={s.tone}
              onSelect={(v) => updateScript(formData, onChange, { tone: v })}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function ManualTab({
  formData,
  onChange,
}: {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="manual-title">제목</Label>
        <Input
          id="manual-title"
          placeholder="내 영상 제목"
          value={formData.script.title}
          onChange={(e) =>
            updateScript(formData, onChange, { title: e.target.value })
          }
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="manual-script">대본 입력</Label>
        <div className="flex flex-wrap gap-1.5 pb-1">
          {EMOTION_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => {
                const el = document.getElementById(
                  "manual-script",
                ) as HTMLTextAreaElement | null;
                if (!el) return;
                const start = el.selectionStart ?? formData.script.manualScript.length;
                const before = formData.script.manualScript.slice(0, start);
                const after = formData.script.manualScript.slice(start);
                updateScript(formData, onChange, {
                  manualScript: `${before}${tag}${after}`,
                });
                requestAnimationFrame(() => {
                  el.focus();
                  const pos = start + tag.length;
                  el.setSelectionRange(pos, pos);
                });
              }}
              className="rounded-md bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400 transition-colors hover:bg-violet-900/50 hover:text-violet-300"
            >
              {tag}
            </button>
          ))}
        </div>
        <Textarea
          id="manual-script"
          placeholder={`장면별로 나누어 입력하세요.\n\n[장면 1]\n나레이션: 안녕하세요, 오늘은...\n\n[장면 2]\n나레이션: 다음으로...`}
          rows={12}
          value={formData.script.manualScript}
          onChange={(e) =>
            updateScript(formData, onChange, {
              manualScript: e.target.value,
            })
          }
        />
        <div className="flex justify-between">
          <p className="text-xs text-zinc-500">
            직접 입력한 대본으로 영상이 생성됩니다. 스크립트 생성 단계가
            스킵됩니다.
          </p>
          <span className="shrink-0 text-[10px] text-zinc-600">
            {formData.script.manualScript.length}자 (공백 포함) /{" "}
            {formData.script.manualScript.replace(/\s/g, "").length}자 (공백
            제외)
          </span>
        </div>
      </div>
    </div>
  );
}

function TitleTopicFields({
  formData,
  onChange,
}: {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}) {
  return (
    <>
      <div className="space-y-2">
        <Label htmlFor="title">제목</Label>
        <Input
          id="title"
          placeholder="내 영상 제목"
          value={formData.script.title}
          onChange={(e) =>
            updateScript(formData, onChange, { title: e.target.value })
          }
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="topic">주제 / 프롬프트</Label>
        <Textarea
          id="topic"
          placeholder="초보자를 위한 양자컴퓨팅 쉬운 설명..."
          rows={3}
          value={formData.script.topic}
          onChange={(e) =>
            updateScript(formData, onChange, { topic: e.target.value })
          }
        />
        <div className="flex justify-between">
          <p className="text-xs text-zinc-500">
            영상 내용을 설명하세요. AI가 이를 바탕으로 스크립트를 생성합니다.
          </p>
          <span className="shrink-0 text-[10px] text-zinc-600">
            {formData.script.topic.length}자
          </span>
        </div>
      </div>
    </>
  );
}

export function StepScript({ formData, onChange }: StepScriptProps) {
  const currentMode = formData.script.mode;

  function setMode(mode: ScriptMode) {
    updateScript(formData, onChange, { mode });
    // manual 모드일 때 script step 비활성화
    if (mode === "manual") {
      onChange({
        script: { ...formData.script, mode },
        steps: { ...formData.steps, script: false },
      });
    } else if (!formData.steps.script) {
      onChange({
        script: { ...formData.script, mode },
        steps: { ...formData.steps, script: true },
      });
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">대본 설정</h2>
        <p className="text-sm text-zinc-400">
          스크립트 생성 방식을 선택하세요.
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 rounded-lg bg-zinc-900 p-1">
        {TABS.map((tab) => (
          <button
            key={tab.mode}
            type="button"
            onClick={() => setMode(tab.mode)}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              currentMode === tab.mode
                ? "bg-zinc-800 text-zinc-100 shadow-sm"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {currentMode === "basic" && (
        <BasicTab formData={formData} onChange={onChange} />
      )}
      {currentMode === "ai" && (
        <AITab formData={formData} onChange={onChange} />
      )}
      {currentMode === "url" && (
        <URLTab formData={formData} onChange={onChange} />
      )}
      {currentMode === "manual" && (
        <ManualTab formData={formData} onChange={onChange} />
      )}
    </div>
  );
}
