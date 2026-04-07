"use client";

import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  SUBTITLE_STYLES,
  SUBTITLE_POSITIONS,
  SUBTITLE_FONT_SIZE_MIN,
  SUBTITLE_FONT_SIZE_MAX,
  SUBTITLE_FONT_SIZE_STEP,
  SUBTITLE_OUTLINE_MIN,
  SUBTITLE_OUTLINE_MAX,
  SUBTITLE_OUTLINE_STEP,
  SUBTITLE_OPACITY_MIN,
  SUBTITLE_OPACITY_MAX,
  SUBTITLE_OPACITY_STEP,
  SYNC_MODES,
  SYNC_SPEED_MIN,
  SYNC_SPEED_MAX,
  SYNC_SPEED_STEP,
  type FormData,
  type SubtitleConfig,
  type VideoSyncConfig,
} from "./types";

interface StepSubtitleProps {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}

function updateSubtitle(
  formData: FormData,
  onChange: (data: Partial<FormData>) => void,
  patch: Partial<SubtitleConfig>,
) {
  onChange({ subtitle: { ...formData.subtitle, ...patch } });
}

function updateSync(
  formData: FormData,
  onChange: (data: Partial<FormData>) => void,
  patch: Partial<VideoSyncConfig>,
) {
  onChange({ videoSync: { ...formData.videoSync, ...patch } });
}

export function StepSubtitle({ formData, onChange }: StepSubtitleProps) {
  const sub = formData.subtitle;
  const sync = formData.videoSync;

  return (
    <div className="space-y-8">
      {/* 자막 스타일 */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-medium text-zinc-50">자막 스타일</h2>
          <p className="text-sm text-zinc-400">
            영상에 표시될 자막의 스타일을 선택하세요.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {SUBTITLE_STYLES.map((style) => {
            const isSelected = sub.style === style.id;
            return (
              <button
                key={style.id}
                type="button"
                onClick={() =>
                  updateSubtitle(formData, onChange, {
                    style: style.id,
                    enabled: style.id !== "none",
                  })
                }
                className={`group relative rounded-lg border p-3 text-left transition-all ${
                  isSelected
                    ? "border-violet-500 bg-violet-950/40"
                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                }`}
              >
                {/* 미리보기 영역 */}
                <div
                  className="mb-2 flex h-10 items-center justify-center rounded"
                  style={{ backgroundColor: "#18181b" }}
                >
                  {style.color ? (
                    <span
                      className="text-sm font-bold"
                      style={{
                        color: style.color,
                        textShadow:
                          style.bg !== "none"
                            ? "none"
                            : "0 0 4px rgba(0,0,0,0.8)",
                        backgroundColor:
                          style.bg !== "none" ? style.bg : "transparent",
                        padding: style.bg !== "none" ? "2px 6px" : "0",
                        borderRadius: "2px",
                      }}
                    >
                      자막 미리보기
                    </span>
                  ) : (
                    <span className="text-xs text-zinc-600">OFF</span>
                  )}
                </div>
                <p className="text-sm font-medium text-zinc-200">
                  {style.name}
                </p>
                <p className="text-[11px] text-zinc-500">
                  {style.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* 커스텀 슬라이더 (자막 미사용이 아닐 때만) */}
      {sub.enabled && sub.style !== "none" && (
        <div className="space-y-4 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
          <h3 className="text-sm font-semibold text-zinc-300">세부 설정</h3>

          {/* 글꼴 크기 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-zinc-400">글꼴 크기</Label>
              <span className="text-sm text-zinc-300">{sub.fontSize}px</span>
            </div>
            <input
              type="range"
              min={SUBTITLE_FONT_SIZE_MIN}
              max={SUBTITLE_FONT_SIZE_MAX}
              step={SUBTITLE_FONT_SIZE_STEP}
              value={sub.fontSize}
              onChange={(e) =>
                updateSubtitle(formData, onChange, {
                  fontSize: Number(e.target.value),
                })
              }
              className="w-full accent-violet-500"
            />
          </div>

          {/* 위치 */}
          <div className="space-y-2">
            <Label className="text-zinc-400">위치</Label>
            <div className="flex gap-2">
              {SUBTITLE_POSITIONS.map((pos) => (
                <button
                  key={pos.id}
                  type="button"
                  onClick={() =>
                    updateSubtitle(formData, onChange, { position: pos.id })
                  }
                  className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                    sub.position === pos.id
                      ? "bg-violet-600 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </div>

          {/* 외곽선 두께 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-zinc-400">외곽선 두께</Label>
              <span className="text-sm text-zinc-300">
                {sub.outlineWidth}px
              </span>
            </div>
            <input
              type="range"
              min={SUBTITLE_OUTLINE_MIN}
              max={SUBTITLE_OUTLINE_MAX}
              step={SUBTITLE_OUTLINE_STEP}
              value={sub.outlineWidth}
              onChange={(e) =>
                updateSubtitle(formData, onChange, {
                  outlineWidth: Number(e.target.value),
                })
              }
              className="w-full accent-violet-500"
            />
          </div>

          {/* 불투명도 */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-zinc-400">불투명도</Label>
              <span className="text-sm text-zinc-300">
                {Math.round(sub.opacity * 100)}%
              </span>
            </div>
            <input
              type="range"
              min={SUBTITLE_OPACITY_MIN}
              max={SUBTITLE_OPACITY_MAX}
              step={SUBTITLE_OPACITY_STEP}
              value={sub.opacity}
              onChange={(e) =>
                updateSubtitle(formData, onChange, {
                  opacity: Number(e.target.value),
                })
              }
              className="w-full accent-violet-500"
            />
          </div>
        </div>
      )}

      {/* 영상 싱크 모드 */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-medium text-zinc-50">영상 싱크 모드</h2>
          <p className="text-sm text-zinc-400">
            이미지와 오디오의 동기화 방식을 선택하세요.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {SYNC_MODES.map((mode) => {
            const isSelected = sync.mode === mode.id;
            return (
              <button
                key={mode.id}
                type="button"
                onClick={() =>
                  updateSync(formData, onChange, {
                    mode: mode.id as FormData["videoSync"]["mode"],
                  })
                }
                className={`rounded-lg border p-3 text-left transition-all ${
                  isSelected
                    ? "border-violet-500 bg-violet-950/40"
                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                }`}
              >
                <p className="text-sm font-medium text-zinc-200">
                  {mode.name}
                </p>
                <p className="text-[11px] text-zinc-500">
                  {mode.description}
                </p>
              </button>
            );
          })}
        </div>

        {/* 속도 조절 슬라이더 (speed 모드일 때만) */}
        {sync.mode === "speed" && (
          <div className="space-y-2 rounded-lg border border-zinc-800 bg-zinc-950/50 p-4">
            <div className="flex items-center justify-between">
              <Label className="text-zinc-400">전환 속도</Label>
              <Badge
                variant="outline"
                className="border-zinc-700 text-zinc-300"
              >
                {sync.speedFactor.toFixed(1)}x
              </Badge>
            </div>
            <input
              type="range"
              min={SYNC_SPEED_MIN}
              max={SYNC_SPEED_MAX}
              step={SYNC_SPEED_STEP}
              value={sync.speedFactor}
              onChange={(e) =>
                updateSync(formData, onChange, {
                  speedFactor: Number(e.target.value),
                })
              }
              className="w-full accent-violet-500"
            />
            <div className="flex justify-between text-[10px] text-zinc-600">
              <span>느리게 (0.5x)</span>
              <span>빠르게 (2.0x)</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
