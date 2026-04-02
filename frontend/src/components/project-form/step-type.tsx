"use client";

import { Film, Monitor } from "lucide-react";
import { VIDEO_TYPES, type FormData } from "./types";

interface StepTypeProps {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}

const ICONS: Record<string, typeof Film> = {
  shorts: Film,
  longform: Monitor,
};

export function StepType({ formData, onChange }: StepTypeProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">영상 타입 선택</h2>
        <p className="text-sm text-zinc-400">만들 영상의 형식을 선택하세요.</p>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {VIDEO_TYPES.map((vt) => {
          const Icon = ICONS[vt.value] ?? Film;
          const isSelected = formData.type === vt.value;
          return (
            <button
              key={vt.value}
              type="button"
              onClick={() => onChange({ type: vt.value })}
              className={`group relative flex flex-col items-center gap-4 rounded-xl border p-6 text-center transition-all ${
                isSelected
                  ? "border-violet-500/60 bg-gradient-to-br from-violet-950/60 to-indigo-950/60 shadow-lg shadow-violet-900/20"
                  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700 hover:bg-zinc-900/80"
              }`}
            >
              {/* Aspect ratio preview */}
              <div
                className={`flex items-center justify-center rounded-lg border-2 border-dashed transition-colors ${
                  isSelected ? "border-violet-400/60" : "border-zinc-700"
                } ${vt.value === "shorts" ? "h-24 w-14" : "h-14 w-24"}`}
              >
                <Icon
                  className={`h-6 w-6 ${
                    isSelected ? "text-violet-400" : "text-zinc-500"
                  }`}
                />
              </div>

              <div>
                <div className="flex items-center justify-center gap-2">
                  <span className="font-semibold text-zinc-200">
                    {vt.label}
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                      isSelected
                        ? "bg-violet-500/20 text-violet-300"
                        : "bg-zinc-800 text-zinc-500"
                    }`}
                  >
                    {vt.ratio}
                  </span>
                </div>
                <p className="mt-1 text-sm text-zinc-500">{vt.description}</p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
