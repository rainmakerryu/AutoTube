"use client";

import { Badge } from "@/components/ui/badge";
import {
  VIDEO_TYPES,
  IMAGE_PROVIDERS,
  IMAGE_STYLES,
  VOICE_OPTIONS,
  EMOTIONS,
  LANGUAGES,
  PURPOSES,
  TONES,
  SPEECH_STYLES,
  type FormData,
} from "./types";

interface StepConfirmProps {
  formData: FormData;
}

function findLabel<T extends { id: string; label?: string; name?: string }>(
  list: readonly T[],
  id: string,
): string {
  const item = list.find((i) => i.id === id);
  if (!item) return id;
  return "label" in item && item.label ? String(item.label) : "name" in item && item.name ? String(item.name) : id;
}

function SummaryCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950/50 p-4 space-y-3">
      <h3 className="text-sm font-semibold text-zinc-300">{title}</h3>
      <div className="space-y-2 text-sm">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <span className="shrink-0 text-zinc-500">{label}</span>
      <span className="text-right text-zinc-200">{value}</span>
    </div>
  );
}

export function StepConfirm({ formData }: StepConfirmProps) {
  const { script: s, imageStyle: img, voice: v } = formData;

  const videoType = VIDEO_TYPES.find((vt) => vt.value === formData.type);
  const imageProvider = IMAGE_PROVIDERS.find((p) => p.id === img.provider);
  const imageStyle = IMAGE_STYLES.find((st) => st.id === img.style);
  const selectedVoice = VOICE_OPTIONS.find((vo) => vo.id === v.voiceId);

  const scriptModeLabel =
    s.mode === "basic"
      ? "기본 설정 (AI 자동)"
      : s.mode === "ai"
        ? "AI로 작성하기"
        : "직접 입력";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">최종 확인</h2>
        <p className="text-sm text-zinc-400">
          설정을 확인하고 프로젝트를 생성하세요.
        </p>
      </div>

      {/* 영상 타입 */}
      <SummaryCard title="01. 영상 타입">
        <Row
          label="타입"
          value={
            <span className="flex items-center gap-2">
              {videoType?.label ?? formData.type}
              <Badge
                variant="outline"
                className="border-zinc-700 text-zinc-400 text-[10px]"
              >
                {videoType?.ratio}
              </Badge>
            </span>
          }
        />
      </SummaryCard>

      {/* 대본 설정 */}
      <SummaryCard title="02. 대본 설정">
        <Row label="모드" value={scriptModeLabel} />
        {s.title && <Row label="제목" value={s.title} />}
        {s.topic && (
          <Row
            label="주제"
            value={
              <span className="max-w-[260px] truncate inline-block">
                {s.topic}
              </span>
            }
          />
        )}
        {s.mode === "ai" && (
          <>
            <Row label="언어" value={findLabel(LANGUAGES, s.language)} />
            <Row label="목적" value={findLabel(PURPOSES, s.purpose)} />
            <Row label="톤" value={findLabel(TONES, s.tone)} />
            <Row label="말투" value={findLabel(SPEECH_STYLES, s.speechStyle)} />
            {s.openingComment && (
              <Row label="오프닝" value={s.openingComment} />
            )}
            {s.closingComment && (
              <Row label="클로징" value={s.closingComment} />
            )}
          </>
        )}
        {s.mode === "manual" && s.manualScript && (
          <Row
            label="대본"
            value={
              <span className="max-w-[260px] truncate inline-block">
                {s.manualScript.slice(0, 80)}
                {s.manualScript.length > 80 ? "..." : ""}
              </span>
            }
          />
        )}
      </SummaryCard>

      {/* 이미지 스타일 */}
      <SummaryCard title="03. 이미지 스타일">
        <Row
          label="소스"
          value={
            <span className="flex items-center gap-2">
              {imageProvider?.name ?? img.provider}
              {imageProvider?.free && (
                <Badge
                  variant="outline"
                  className="border-green-800 text-green-400 text-[10px]"
                >
                  무료
                </Badge>
              )}
            </span>
          }
        />
        <Row label="스타일" value={imageStyle?.name ?? img.style} />
      </SummaryCard>

      {/* AI 보이스 */}
      <SummaryCard title="04. AI 보이스">
        {v.enabled ? (
          <>
            <Row
              label="음성"
              value={
                <span className="flex items-center gap-2">
                  {selectedVoice?.name ?? v.voiceId}
                  {selectedVoice?.free ? (
                    <Badge
                      variant="outline"
                      className="border-green-800 text-green-400 text-[10px]"
                    >
                      무료
                    </Badge>
                  ) : (
                    <Badge
                      variant="outline"
                      className="border-amber-800 text-amber-400 text-[10px]"
                    >
                      유료
                    </Badge>
                  )}
                </span>
              }
            />
            <Row
              label="감정"
              value={findLabel(EMOTIONS, v.emotion)}
            />
            <Row label="속도" value={`${v.speed.toFixed(1)}x`} />
          </>
        ) : (
          <Row label="상태" value="보이스 없음" />
        )}
      </SummaryCard>
    </div>
  );
}
