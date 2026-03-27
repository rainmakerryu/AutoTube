"use client";

import { useState } from "react";
import { Eye, EyeOff, Save, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiClient } from "@/lib/api";

interface ApiKeyFormProps {
  provider: string;
  label: string;
  description: string;
  hasKey: boolean;
  onSaved: () => void;
}

export function ApiKeyForm({ provider, label, description, hasKey, onSaved }: ApiKeyFormProps) {
  const [open, setOpen] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    if (!apiKey.trim()) return;
    setIsSaving(true);
    setError(null);
    try {
      await apiClient("/api/api-keys", {
        method: "POST",
        body: JSON.stringify({ provider, api_key: apiKey }),
      });
      setApiKey("");
      setOpen(false);
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "API 키 저장에 실패했습니다");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete() {
    setIsDeleting(true);
    setError(null);
    try {
      await apiClient(`/api/api-keys/${provider}`, { method: "DELETE" });
      onSaved();
    } catch (err) {
      setError(err instanceof Error ? err.message : "API 키 삭제에 실패했습니다");
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <div className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-zinc-200">{label}</span>
          {hasKey ? (
            <span className="h-2 w-2 rounded-full bg-green-500" />
          ) : (
            <span className="h-2 w-2 rounded-full bg-zinc-600" />
          )}
        </div>
        <p className="mt-1 text-xs text-zinc-500">{description}</p>
      </div>

      <div className="flex gap-2">
        {hasKey && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-red-400 hover:text-red-300"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        )}

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger render={<Button variant="outline" size="sm" />}>
              {hasKey ? "수정" : "키 추가"}
          </DialogTrigger>
          <DialogContent className="bg-zinc-950 border-zinc-800">
            <DialogHeader>
              <DialogTitle className="text-zinc-50">{label} API 키</DialogTitle>
              <DialogDescription className="text-zinc-400">
                {description}. 키는 암호화되어 저장됩니다.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor={`key-${provider}`}>API 키</Label>
                <div className="relative">
                  <Input
                    id={`key-${provider}`}
                    type={showKey ? "text" : "password"}
                    placeholder="sk-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                  >
                    {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
            </div>

            <DialogFooter>
              <Button variant="ghost" onClick={() => setOpen(false)}>
                취소
              </Button>
              <Button onClick={handleSave} disabled={isSaving || !apiKey.trim()}>
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? "저장 중..." : "키 저장"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
