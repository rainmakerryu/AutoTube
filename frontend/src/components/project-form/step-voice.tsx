"use client";

import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  VOICE_OPTIONS,
  EMOTIONS,
  VOICE_SPEED_MIN,
  VOICE_SPEED_MAX,
  VOICE_SPEED_STEP,
  type FormData,
  type VoiceConfig,
  type VoiceOption,
} from "./types";

interface StepVoiceProps {
  formData: FormData;
  onChange: (data: Partial<FormData>) => void;
}

function updateVoice(
  formData: FormData,
  onChange: (data: Partial<FormData>) => void,
  patch: Partial<VoiceConfig>,
) {
  onChange({ voice: { ...formData.voice, ...patch } });
}

function VoiceCard({
  voice,
  isSelected,
  onSelect,
}: {
  voice: VoiceOption;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${
        isSelected
          ? "border-violet-500/60 bg-violet-950/30"
          : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
      }`}
    >
      {/* Avatar placeholder */}
      <div
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
          voice.gender === "female"
            ? "bg-pink-950/60 text-pink-400"
            : "bg-blue-950/60 text-blue-400"
        }`}
      >
        {voice.name.charAt(0)}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-200">
            {voice.name}
          </span>
          {voice.free ? (
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
        </div>
        <p className="truncate text-xs text-zinc-500">{voice.tags}</p>
      </div>
    </button>
  );
}

export function StepVoice({ formData, onChange }: StepVoiceProps) {
  const v = formData.voice;

  function selectVoice(voice: VoiceOption) {
    updateVoice(formData, onChange, {
      enabled: true,
      provider: voice.provider,
      voiceId: voice.id,
      voiceName: voice.name,
    });
  }

  function toggleEnabled(enabled: boolean) {
    updateVoice(formData, onChange, { enabled });
    // TTS step 토글
    onChange({
      voice: { ...formData.voice, enabled },
      steps: { ...formData.steps, tts: enabled },
    });
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-zinc-50">AI 보이스 설정</h2>
        <p className="text-sm text-zinc-400">
          대본을 읽는 나레이션 목소리를 설정하세요.
        </p>
      </div>

      {/* Enable/Disable toggle */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={() => toggleEnabled(true)}
          className={`flex-1 rounded-lg border p-4 text-left transition-all ${
            v.enabled
              ? "border-violet-500/60 bg-violet-950/30"
              : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
          }`}
        >
          <div className="text-sm font-medium text-zinc-200">
            AI 보이스 사용
          </div>
          <p className="mt-1 text-xs text-zinc-500">
            대본을 읽는 나레이션 목소리를 생성해요
          </p>
        </button>
        <button
          type="button"
          onClick={() => toggleEnabled(false)}
          className={`flex-1 rounded-lg border p-4 text-left transition-all ${
            !v.enabled
              ? "border-violet-500/60 bg-violet-950/30"
              : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
          }`}
        >
          <div className="text-sm font-medium text-zinc-200">보이스 없음</div>
          <p className="mt-1 text-xs text-zinc-500">
            AI 보이스를 생성하지 않아요
          </p>
        </button>
      </div>

      {v.enabled && (
        <>
          {/* Voice list */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-zinc-300">음성 선택</h3>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 max-h-64 overflow-y-auto rounded-lg border border-zinc-800 p-2">
              {VOICE_OPTIONS.map((voice) => (
                <VoiceCard
                  key={voice.id}
                  voice={voice}
                  isSelected={v.voiceId === voice.id}
                  onSelect={() => selectVoice(voice)}
                />
              ))}
            </div>
          </div>

          {/* Emotion */}
          <div className="space-y-3">
            <Label className="text-sm font-medium text-zinc-300">
              감정 선택
            </Label>
            <div className="flex flex-wrap gap-2">
              {EMOTIONS.map((em) => (
                <button
                  key={em.id}
                  type="button"
                  onClick={() =>
                    updateVoice(formData, onChange, { emotion: em.id })
                  }
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                    v.emotion === em.id
                      ? "bg-violet-600 text-white"
                      : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
                  }`}
                >
                  {em.label}
                </button>
              ))}
            </div>
          </div>

          {/* Speed slider */}
          <div className="space-y-3">
            <Label className="text-sm font-medium text-zinc-300">
              읽는 속도 (템포)
            </Label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min={VOICE_SPEED_MIN}
                max={VOICE_SPEED_MAX}
                step={VOICE_SPEED_STEP}
                value={v.speed}
                onChange={(e) =>
                  updateVoice(formData, onChange, {
                    speed: parseFloat(e.target.value),
                  })
                }
                className="h-2 flex-1 cursor-pointer appearance-none rounded-full bg-zinc-800 accent-violet-500"
              />
              <span className="w-12 text-right text-sm font-medium text-zinc-300">
                {v.speed.toFixed(1)}x
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
