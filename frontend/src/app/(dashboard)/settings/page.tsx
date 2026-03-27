"use client";

import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiKeyForm } from "@/components/api-key-form";
import { apiClient } from "@/lib/api";

const API_KEY_PROVIDERS = [
  {
    provider: "openai",
    label: "OpenAI",
    description: "스크립트·메타데이터용 GPT, 이미지용 DALL-E, 자막용 Whisper",
  },
  {
    provider: "claude",
    label: "Anthropic (Claude)",
    description: "스크립트·메타데이터 생성용 Claude",
  },
  {
    provider: "gemini",
    label: "Google Gemini",
    description: "이미지 생성용 Gemini",
  },
  {
    provider: "elevenlabs",
    label: "ElevenLabs",
    description: "고품질 텍스트 음성 변환",
  },
  {
    provider: "pexels",
    label: "Pexels",
    description: "무료 스톡 사진·영상",
  },
] as const;

interface ApiKeyInfo {
  provider: string;
  created_at: string;
}

export default function SettingsPage() {
  const [keys, setKeys] = useState<ApiKeyInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchKeys = useCallback(async () => {
    try {
      const data = await apiClient("/api/api-keys");
      setKeys(data);
    } catch {
      // Keys might not be loaded if not authenticated yet
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const savedProviders = new Set(keys.map((k) => k.provider));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-50">설정</h1>
        <p className="mt-1 text-sm text-zinc-400">
          API 키와 기본 설정을 관리하세요.
        </p>
      </div>

      <Tabs defaultValue="api-keys">
        <TabsList className="bg-zinc-900">
          <TabsTrigger value="api-keys">API 키</TabsTrigger>
          <TabsTrigger value="preferences">환경 설정</TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys" className="mt-4 space-y-4">
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardHeader>
              <CardTitle className="text-zinc-50">API 키</CardTitle>
              <CardDescription className="text-zinc-400">
                AI 서비스 API 키를 추가하세요. 키는 AES-256-GCM으로 암호화되어 저장됩니다.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {isLoading ? (
                Array.from({ length: 5 }, (_, i) => (
                  <Skeleton key={i} className="h-16 w-full bg-zinc-800" />
                ))
              ) : (
                API_KEY_PROVIDERS.map((p) => (
                  <ApiKeyForm
                    key={p.provider}
                    provider={p.provider}
                    label={p.label}
                    description={p.description}
                    hasKey={savedProviders.has(p.provider)}
                    onSaved={fetchKeys}
                  />
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="mt-4">
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardHeader>
              <CardTitle className="text-zinc-50">환경 설정</CardTitle>
              <CardDescription className="text-zinc-400">
                영상 생성 기본 설정입니다.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-500">
                추가 설정은 향후 업데이트에서 제공될 예정입니다.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
