"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

interface ImagesReviewProps {
  outputData: {
    image_urls?: string[];
    scene_count?: number;
    provider?: string;
  };
  onApprove: () => void;
  onReject: () => void;
}

export function ImagesReview({ outputData, onApprove, onReject }: ImagesReviewProps) {
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);
  const images = outputData.image_urls ?? [];

  return (
    <div className="space-y-4">
      <div className="text-xs text-muted-foreground">
        {images.length}개 이미지 생성됨
        {outputData.provider && ` (${outputData.provider})`}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {images.map((url, i) => (
          <Card
            key={i}
            className="cursor-pointer hover:ring-2 hover:ring-violet-500/50 transition-all"
            onClick={() => setLightboxIndex(i)}
          >
            <CardContent className="p-2">
              <div className="aspect-[9/16] relative rounded overflow-hidden bg-muted">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={url}
                  alt={`장면 ${i + 1}`}
                  className="object-cover w-full h-full"
                />
              </div>
              <p className="text-xs text-center text-muted-foreground mt-1.5">
                장면 {i + 1}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {lightboxIndex !== null && (
        <Dialog open onOpenChange={() => setLightboxIndex(null)}>
          <DialogContent className="max-w-2xl">
            <DialogTitle className="sr-only">
              장면 {lightboxIndex + 1} 이미지
            </DialogTitle>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={images[lightboxIndex]}
              alt={`장면 ${lightboxIndex + 1}`}
              className="w-full rounded"
            />
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">
                장면 {lightboxIndex + 1} / {images.length}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={lightboxIndex === 0}
                  onClick={() => setLightboxIndex((prev) => (prev ?? 1) - 1)}
                >
                  이전
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={lightboxIndex === images.length - 1}
                  onClick={() => setLightboxIndex((prev) => (prev ?? 0) + 1)}
                >
                  다음
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}

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
