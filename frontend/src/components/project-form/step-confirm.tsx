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
  SUBTITLE_STYLES,
  SUBTITLE_POSITIONS,
  SYNC_MODES,
  LOGO_POSITIONS,
  BGM_MOODS,
  AUDIO_POST_MODES,
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
        {v.enabled && v.customAudioUrl && v.customAudioUrl !== "pending" ? (
          <>
            <Row label="모드" value="외부 음성 업로드" />
            <Row
              label="파일"
              value={
                <span className="max-w-[260px] truncate inline-block">
                  {v.customAudioName || "업로드된 파일"}
                </span>
              }
            />
          </>
        ) : v.enabled ? (
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

      {/* 자막 스타일 */}
      <SummaryCard title="05. 자막 스타일">
        {formData.subtitle.enabled && formData.subtitle.style !== "none" ? (
          <>
            <Row
              label="스타일"
              value={findLabel(SUBTITLE_STYLES, formData.subtitle.style)}
            />
            <Row label="글꼴 크기" value={`${formData.subtitle.fontSize}px`} />
            <Row
              label="위치"
              value={findLabel(SUBTITLE_POSITIONS, formData.subtitle.position)}
            />
            <Row
              label="불투명도"
              value={`${Math.round(formData.subtitle.opacity * 100)}%`}
            />
          </>
        ) : (
          <Row label="상태" value="자막 미사용" />
        )}
      </SummaryCard>

      {/* 영상 싱크 모드 */}
      <SummaryCard title="05-1. 영상 싱크">
        <Row
          label="모드"
          value={findLabel(SYNC_MODES, formData.videoSync.mode)}
        />
        {formData.videoSync.mode === "speed" && (
          <Row
            label="전환 속도"
            value={`${formData.videoSync.speedFactor.toFixed(1)}x`}
          />
        )}
      </SummaryCard>

      {/* 인트로 / 로고 */}
      {(formData.intro.introVideoUrl || formData.intro.logoUrl) && (
        <SummaryCard title="05-2. 인트로 / 로고">
          {formData.intro.introVideoUrl && (
            <Row
              label="인트로 영상"
              value={
                <span className="max-w-[200px] truncate inline-block">
                  {formData.intro.introVideoName || "업로드됨"}
                </span>
              }
            />
          )}
          {formData.intro.logoUrl && (
            <>
              <Row
                label="로고"
                value={
                  <span className="max-w-[200px] truncate inline-block">
                    {formData.intro.logoName || "업로드됨"}
                  </span>
                }
              />
              <Row
                label="위치"
                value={findLabel(LOGO_POSITIONS, formData.intro.logoPosition)}
              />
              <Row
                label="불투명도"
                value={`${Math.round(formData.intro.logoOpacity * 100)}%`}
              />
            </>
          )}
        </SummaryCard>
      )}

      {/* 오디오 후처리 */}
      {formData.audioPost.enabled && (
        <SummaryCard title="05-3. 오디오 후처리">
          <Row
            label="모드"
            value={findLabel(AUDIO_POST_MODES, formData.audioPost.mode)}
          />
        </SummaryCard>
      )}

      {/* BGM 설정 */}
      <SummaryCard title="06. BGM 설정">
        {formData.bgm.enabled ? (
          <>
            <Row
              label="분위기"
              value={findLabel(BGM_MOODS, formData.bgm.mood)}
            />
            <Row
              label="볼륨"
              value={`${Math.round(formData.bgm.volume * 100)}%`}
            />
          </>
        ) : (
          <Row label="상태" value="BGM 없음" />
        )}
      </SummaryCard>

      {/* 썸네일 */}
      {formData.thumbnail.enabled && (
        <SummaryCard title="06-1. AI 썸네일">
          <Row label="상태" value="AI 자동 생성" />
        </SummaryCard>
      )}

      {/* SEO / SNS */}
      <SummaryCard title="07. SEO & SNS">
        <Row
          label="SEO 최적화"
          value={
            formData.steps.seo ? (
              <Badge
                variant="outline"
                className="border-green-800 text-green-400 text-[10px]"
              >
                자동 최적화
              </Badge>
            ) : (
              "사용 안 함"
            )
          }
        />
        <Row
          label="SNS 배포"
          value={
            formData.steps.sns ? (
              <Badge
                variant="outline"
                className="border-green-800 text-green-400 text-[10px]"
              >
                공유 콘텐츠 자동 생성
              </Badge>
            ) : (
              "사용 안 함"
            )
          }
        />
      </SummaryCard>
    </div>
  );
}
