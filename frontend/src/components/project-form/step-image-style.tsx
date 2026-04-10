"use client";

import { Badge } from "@/components/ui/badge";
import {
  IMAGE_PROVIDERS,
  IMAGE_STYLES,
  VIDEO_GEN_MODES,
  VIDEO_GEN_MODELS,
  type FormData,
  type ImageConfig,
} from "./types";

interface StepImageStyleProps {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}

function updateImage(
  formData: FormData,
  onChange: (data: Partial<FormData>) => void,
  patch: Partial<ImageConfig>,
) {
  onChange({ imageStyle: { ...formData.imageStyle, ...patch } });
}

export function StepImageStyle({ formData, onChange }: StepImageStyleProps) {
  const img = formData.imageStyle;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">이미지 스타일</h2>
        <p className="text-sm text-zinc-400">
          영상에 사용할 이미지 생성 방식과 스타일을 선택하세요.
        </p>
      </div>

      {/* Provider selection */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-zinc-300">이미지 소스</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {IMAGE_PROVIDERS.map((p) => {
            const isSelected = img.provider === p.id;
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => updateImage(formData, onChange, { provider: p.id })}
                className={`rounded-lg border p-3 text-center transition-all ${
                  isSelected
                    ? "border-violet-500/60 bg-violet-950/30"
                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                }`}
              >
                <div className="text-sm font-medium text-zinc-200">
                  {p.name}
                </div>
                {p.free && (
                  <Badge
                    variant="outline"
                    className="mt-1 border-green-800 text-green-400 text-[10px]"
                  >
                    무료
                  </Badge>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Style selection */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-zinc-300">이미지 스타일</h3>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {IMAGE_STYLES.map((style) => {
            const isSelected = img.style === style.id;
            return (
              <button
                key={style.id}
                type="button"
                onClick={() =>
                  updateImage(formData, onChange, { style: style.id })
                }
                className={`rounded-lg border p-4 text-left transition-all ${
                  isSelected
                    ? "border-violet-500/60 bg-violet-950/30"
                    : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                }`}
              >
                <div className="text-sm font-medium text-zinc-200">
                  {style.name}
                </div>
                <p className="mt-1 text-xs text-zinc-500">
                  {style.description}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* AI Video Generation (ComfyUI only) */}
      {img.provider === "comfyui" && (
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-medium text-zinc-300">
              AI 영상 생성
            </h3>
            <p className="text-xs text-zinc-500">
              ComfyUI를 사용하여 정적 이미지 대신 AI 영상 클립을 생성합니다.
            </p>
          </div>

          {/* Mode selection */}
          <div className="grid grid-cols-3 gap-3">
            {VIDEO_GEN_MODES.map((mode) => {
              const isSelected = img.videoGenMode === mode.id;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() =>
                    updateImage(formData, onChange, { videoGenMode: mode.id })
                  }
                  className={`rounded-lg border p-3 text-left transition-all ${
                    isSelected
                      ? "border-violet-500/60 bg-violet-950/30"
                      : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                  }`}
                >
                  <div className="text-sm font-medium text-zinc-200">
                    {mode.name}
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    {mode.description}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Model selection (when mode is not "none") */}
          {img.videoGenMode !== "none" && (
            <div className="space-y-2">
              <h4 className="text-xs font-medium text-zinc-400">영상 생성 모델</h4>
              <div className="grid grid-cols-2 gap-3">
                {VIDEO_GEN_MODELS.filter((m) =>
                  (m.modes as readonly string[]).includes(img.videoGenMode),
                ).map((model) => {
                  const isSelected = img.videoGenModel === model.id;
                  return (
                    <button
                      key={model.id}
                      type="button"
                      onClick={() =>
                        updateImage(formData, onChange, {
                          videoGenModel: model.id,
                        })
                      }
                      className={`rounded-lg border p-3 text-left transition-all ${
                        isSelected
                          ? "border-violet-500/60 bg-violet-950/30"
                          : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
                      }`}
                    >
                      <div className="text-sm font-medium text-zinc-200">
                        {model.name}
                      </div>
                      <p className="mt-1 text-xs text-zinc-500">
                        {model.description}
                      </p>
                    </button>
                  );
                })}
              </div>

              {img.videoGenMode === "txt2vid" && (
                <div className="rounded-lg border border-amber-900/50 bg-amber-950/30 p-3">
                  <p className="text-xs text-amber-300">
                    텍스트에서 직접 영상을 생성합니다. 이미지 생성 단계는 건너뜁니다.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
