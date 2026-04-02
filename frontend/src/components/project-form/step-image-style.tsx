"use client";

import { Badge } from "@/components/ui/badge";
import {
  IMAGE_PROVIDERS,
  IMAGE_STYLES,
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
    </div>
  );
}
