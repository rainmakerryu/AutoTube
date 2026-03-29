"use client";

import { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiClient } from "@/lib/api";

interface ProviderOption {
  id: string;
  name: string;
  models: string[];
  voices?: string[];
  free?: boolean;
}

const STEP_PROVIDERS: Record<string, ProviderOption[]> = {
  script: [
    { id: "openai", name: "OpenAI", models: ["gpt-4o"] },
    { id: "claude", name: "Claude", models: ["claude-sonnet-4-6"] },
    { id: "deepseek", name: "DeepSeek", models: ["deepseek-chat"], free: true },
    { id: "ollama", name: "Ollama (로컬)", models: ["llama3", "mistral"], free: true },
  ],
  tts: [
    { id: "elevenlabs", name: "ElevenLabs", models: ["eleven_multilingual_v2"] },
    { id: "openai", name: "OpenAI TTS", models: ["tts-1"], voices: ["alloy", "echo", "fern", "onyx", "nova", "shimmer"] },
    { id: "edgetts", name: "Edge TTS (무료)", models: ["neural"], free: true },
  ],
  images: [
    { id: "gemini", name: "Gemini", models: ["gemini-2.0-flash-exp"] },
    { id: "openai", name: "DALL-E", models: ["dall-e-3"] },
    { id: "pexels", name: "Pexels (스톡)", models: ["search"], free: true },
    { id: "comfyui", name: "ComfyUI (로컬)", models: ["SDXL + IP-Adapter"], free: true },
  ],
  video: [],
  subtitle: [
    { id: "openai", name: "Whisper", models: ["whisper-1"] },
  ],
  metadata: [
    { id: "openai", name: "OpenAI", models: ["gpt-4o"] },
    { id: "claude", name: "Claude", models: ["claude-sonnet-4-6"] },
    { id: "deepseek", name: "DeepSeek", models: ["deepseek-chat"], free: true },
    { id: "ollama", name: "Ollama (로컬)", models: ["llama3", "mistral"], free: true },
  ],
};

const STEP_LABELS: Record<string, string> = {
  script: "스크립트 생성",
  tts: "음성 생성 (TTS)",
  images: "이미지 생성",
  video: "영상 합성",
  subtitle: "자막 생성",
  metadata: "메타데이터 생성",
};

interface StepConfigPanelProps {
  step: string;
  onRun: (provider: string, config: Record<string, unknown>) => void;
  isLoading?: boolean;
}

// API 키가 필요 없는 무료/로컬 프로바이더
const FREE_PROVIDERS = new Set(["edgetts", "ollama", "comfyui"]);

export function StepConfigPanel({ step, onRun, isLoading }: StepConfigPanelProps) {
  const providers = STEP_PROVIDERS[step] ?? [];
  const [selectedProvider, setSelectedProvider] = useState(providers[0]?.id ?? "");
  const [selectedModel, setSelectedModel] = useState(providers[0]?.models[0] ?? "");
  const [selectedVoice, setSelectedVoice] = useState<string>("");
  const [registeredProviders, setRegisteredProviders] = useState<Set<string>>(new Set());
  const [keysLoaded, setKeysLoaded] = useState(false);

  // 등록된 API 키 목록 조회
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const keys = await apiClient("/api/api-keys");
        if (!cancelled) {
          const providerSet = new Set<string>(
            (keys as Array<{ provider: string }>).map((k) => k.provider)
          );
          setRegisteredProviders(providerSet);
        }
      } catch {
        // 조회 실패 시 빈 Set 유지 — 백엔드에서 최종 검증
      } finally {
        if (!cancelled) setKeysLoaded(true);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const currentProvider = providers.find((p) => p.id === selectedProvider);

  // 선택된 프로바이더의 API 키 등록 여부
  const needsApiKey = !FREE_PROVIDERS.has(selectedProvider);
  const hasApiKey = registeredProviders.has(selectedProvider);
  const canRun = !needsApiKey || hasApiKey;

  const handleProviderChange = (value: string | null) => {
    if (!value) return;
    setSelectedProvider(value);
    const provider = providers.find((p) => p.id === value);
    if (provider) {
      setSelectedModel(provider.models[0] ?? "");
      setSelectedVoice(provider.voices?.[0] ?? "");
    }
  };

  const handleRun = () => {
    const config: Record<string, unknown> = { model: selectedModel };
    if (selectedVoice) {
      config.voice_id = selectedVoice;
    }
    onRun(selectedProvider, config);
  };

  // video 단계는 프로바이더 선택 불필요
  if (providers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{STEP_LABELS[step] ?? step}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            이 단계는 이전 단계의 결과를 사용하여 자동으로 처리됩니다.
          </p>
          <Button onClick={() => onRun("", {})} disabled={isLoading}>
            {isLoading ? "처리 중..." : "시작"}
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{STEP_LABELS[step] ?? step}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>AI 프로바이더</Label>
          <Select value={selectedProvider} onValueChange={handleProviderChange}>
            <SelectTrigger>
              <SelectValue placeholder="프로바이더 선택" />
            </SelectTrigger>
            <SelectContent>
              {providers.map((p) => {
                const isFree = FREE_PROVIDERS.has(p.id);
                const keyRegistered = registeredProviders.has(p.id);
                const available = isFree || keyRegistered;
                return (
                  <SelectItem key={p.id} value={p.id}>
                    <span className="flex items-center gap-2">
                      <span className={available ? "" : "text-zinc-500"}>{p.name}</span>
                      {p.free && (
                        <Badge variant="secondary" className="bg-emerald-900/60 text-emerald-300 text-[10px] px-1.5 py-0">
                          무료
                        </Badge>
                      )}
                      {!isFree && !keyRegistered && keysLoaded && (
                        <Badge variant="secondary" className="bg-yellow-900/60 text-yellow-300 text-[10px] px-1.5 py-0">
                          키 미등록
                        </Badge>
                      )}
                    </span>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
        </div>

        {currentProvider && currentProvider.models.length > 1 && (
          <div className="space-y-2">
            <Label>모델</Label>
            <Select value={selectedModel} onValueChange={(v) => { if (v) setSelectedModel(v); }}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currentProvider.models.map((m) => (
                  <SelectItem key={m} value={m}>
                    {m}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {currentProvider?.voices && currentProvider.voices.length > 0 && (
          <div className="space-y-2">
            <Label>음성</Label>
            <Select value={selectedVoice} onValueChange={(v) => { if (v) setSelectedVoice(v); }}>
              <SelectTrigger>
                <SelectValue placeholder="음성 선택" />
              </SelectTrigger>
              <SelectContent>
                {currentProvider.voices.map((v) => (
                  <SelectItem key={v} value={v}>
                    {v}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        {keysLoaded && needsApiKey && !hasApiKey && (
          <div className="p-3 rounded-lg bg-yellow-950/50 border border-yellow-900/50 text-sm text-yellow-300">
            <strong>{currentProvider?.name ?? selectedProvider}</strong> API 키가 등록되지 않았습니다.
            <a href="/settings" className="underline ml-1">설정 페이지</a>에서 API 키를 먼저 등록해 주세요.
          </div>
        )}

        <Button onClick={handleRun} disabled={isLoading || !selectedProvider || !canRun} className="w-full">
          {isLoading ? "생성 중..." : canRun ? "생성 시작" : "API 키 필요"}
        </Button>
      </CardContent>
    </Card>
  );
}
