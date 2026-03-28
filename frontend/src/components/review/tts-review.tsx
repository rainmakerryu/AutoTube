"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface TtsReviewProps {
  outputData: {
    audio_url?: string;
    audio_size?: number;
    chunk_count?: number;
    provider?: string;
  };
  onApprove: () => void;
  onReject: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function TtsReview({ outputData, onApprove, onReject }: TtsReviewProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-4 space-y-4">
          {outputData.audio_url ? (
            <audio controls className="w-full" preload="metadata">
              <source src={outputData.audio_url} type="audio/mpeg" />
              브라우저가 오디오 재생을 지원하지 않습니다.
            </audio>
          ) : (
            <p className="text-sm text-muted-foreground">
              오디오 미리듣기를 사용할 수 없습니다.
            </p>
          )}

          <div className="flex gap-4 text-xs text-muted-foreground">
            {outputData.provider && (
              <span>프로바이더: {outputData.provider}</span>
            )}
            {outputData.audio_size != null && (
              <span>크기: {formatBytes(outputData.audio_size)}</span>
            )}
            {outputData.chunk_count != null && (
              <span>청크: {outputData.chunk_count}개</span>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2 pt-2">
        <Button onClick={onApprove} className="flex-1">
          승인
        </Button>
        <Button variant="outline" onClick={onReject}>
          재생성
        </Button>
      </div>
    </div>
  );
}
