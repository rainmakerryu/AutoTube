"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

interface Scene {
  visual: string;
  narration: string;
}

interface ScriptReviewProps {
  outputData: {
    full_text?: string;
    scenes?: Scene[];
    scene_count?: number;
  };
  onApprove: (editedData?: Record<string, unknown>) => void;
  onReject: () => void;
}

export function ScriptReview({ outputData, onApprove, onReject }: ScriptReviewProps) {
  const [scenes, setScenes] = useState<Scene[]>(outputData.scenes ?? []);
  const [isEdited, setIsEdited] = useState(false);

  const updateScene = useCallback((index: number, field: keyof Scene, value: string) => {
    setScenes((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
    setIsEdited(true);
  }, []);

  const addScene = useCallback(() => {
    setScenes((prev) => [...prev, { visual: "", narration: "" }]);
    setIsEdited(true);
  }, []);

  const removeScene = useCallback((index: number) => {
    setScenes((prev) => prev.filter((_, i) => i !== index));
    setIsEdited(true);
  }, []);

  const handleApprove = () => {
    if (isEdited) {
      const fullText = scenes.map((s) => s.narration).join("\n\n");
      onApprove({
        full_text: fullText,
        scenes,
        scene_count: scenes.length,
      });
    } else {
      onApprove();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">
          {scenes.length}개 장면
        </h3>
        <Button variant="outline" size="sm" onClick={addScene}>
          장면 추가
        </Button>
      </div>

      <div className="space-y-3">
        {scenes.map((scene, i) => (
          <Card key={i}>
            <CardContent className="pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-muted-foreground">
                  장면 {i + 1}
                </span>
                {scenes.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs text-destructive"
                    onClick={() => removeScene(i)}
                  >
                    삭제
                  </Button>
                )}
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">시각 설명</Label>
                <Textarea
                  value={scene.visual}
                  onChange={(e) => updateScene(i, "visual", e.target.value)}
                  rows={2}
                  className="text-sm"
                  placeholder="이 장면의 영상/이미지 설명..."
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">내레이션</Label>
                <Textarea
                  value={scene.narration}
                  onChange={(e) => updateScene(i, "narration", e.target.value)}
                  rows={3}
                  className="text-sm"
                  placeholder="이 장면의 나레이션 텍스트..."
                />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex gap-2 pt-2">
        <Button onClick={handleApprove} className="flex-1">
          {isEdited ? "수정 후 승인" : "승인"}
        </Button>
        <Button variant="outline" onClick={onReject}>
          재생성
        </Button>
      </div>
    </div>
  );
}
