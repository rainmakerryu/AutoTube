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
    description: "GPT models for script & metadata, DALL-E for images, Whisper for subtitles",
  },
  {
    provider: "claude",
    label: "Anthropic (Claude)",
    description: "Claude models for script generation and metadata",
  },
  {
    provider: "gemini",
    label: "Google Gemini",
    description: "Gemini models for image generation",
  },
  {
    provider: "elevenlabs",
    label: "ElevenLabs",
    description: "High-quality text-to-speech voices",
  },
  {
    provider: "pexels",
    label: "Pexels",
    description: "Free stock photos and videos",
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
        <h1 className="text-2xl font-semibold text-zinc-50">Settings</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Manage your API keys and preferences.
        </p>
      </div>

      <Tabs defaultValue="api-keys">
        <TabsList className="bg-zinc-900">
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="api-keys" className="mt-4 space-y-4">
          <Card className="border-zinc-800 bg-zinc-900/50">
            <CardHeader>
              <CardTitle className="text-zinc-50">API Keys</CardTitle>
              <CardDescription className="text-zinc-400">
                Add your API keys for AI services. Keys are encrypted with AES-256-GCM before storage.
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
              <CardTitle className="text-zinc-50">Preferences</CardTitle>
              <CardDescription className="text-zinc-400">
                General settings for video generation.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-zinc-500">
                Additional preferences will be available in a future update.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
