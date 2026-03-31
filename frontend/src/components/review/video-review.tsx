"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

interface VideoReviewProps {
  outputData: {
    video_url?: string;
    resolution?: number[];
    duration?: number;
    fps?: number;
    scene_count?: number;
    video_type?: string;
  };
  onApprove: () => void;
  onReject: () => void;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return mins > 0 ? `${mins}분 ${secs}초` : `${secs}초`;
}

function formatResolution(res: number[]): string {
  if (res.length >= 2) return `${res[0]}x${res[1]}`;
  return String(res);
}

export function VideoReview({ outputData, onApprove, onReject }: VideoReviewProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-4 space-y-4">
          {outputData.video_url ? (
            <video
              controls
              className="w-full rounded-lg"
              preload="metadata"
            >
              <source src={outputData.video_url} type="video/mp4" />
              브라우저가 비디오 재생을 지원하지 않습니다.
            </video>
          ) : (
            <p className="text-sm text-muted-foreground">
              영상 미리보기를 사용할 수 없습니다. (R2 스토리지 미설정)
            </p>
          )}

          <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
            {outputData.video_type && (
              <span>타입: {outputData.video_type}</span>
            )}
            {outputData.resolution && (
              <span>해상도: {formatResolution(outputData.resolution)}</span>
            )}
            {outputData.duration != null && (
              <span>길이: {formatDuration(outputData.duration)}</span>
            )}
            {outputData.fps != null && (
              <span>FPS: {outputData.fps}</span>
            )}
            {outputData.scene_count != null && (
              <span>장면: {outputData.scene_count}개</span>
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
