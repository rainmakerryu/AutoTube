"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, X, FileAudio, FileVideo, Image } from "lucide-react";

const ICON_MAP: Record<string, typeof Upload> = {
  audio: FileAudio,
  video: FileVideo,
  image: Image,
};

interface FileUploadProps {
  /** 허용 MIME 타입 (예: "audio/*", "video/mp4,video/webm") */
  accept: string;
  /** 최대 파일 크기 (bytes) */
  maxSize: number;
  /** 파일 종류 (아이콘 선택용): "audio" | "video" | "image" */
  fileType?: "audio" | "video" | "image";
  /** 안내 텍스트 */
  placeholder?: string;
  /** 업로드 완료 콜백 — URL 반환 */
  onUpload: (file: File) => Promise<string>;
  /** 삭제 콜백 */
  onRemove: () => void;
  /** 현재 업로드된 파일 URL (있으면 미리보기 표시) */
  value?: string;
  /** 현재 업로드된 파일명 */
  fileName?: string;
  /** 비활성화 */
  disabled?: boolean;
}

export function FileUpload({
  accept,
  maxSize,
  fileType = "audio",
  placeholder = "파일을 드래그하거나 클릭하여 업로드",
  onUpload,
  onRemove,
  value,
  fileName,
  disabled = false,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const maxSizeMB = Math.round(maxSize / (1024 * 1024));
  const Icon = ICON_MAP[fileType] ?? Upload;

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (file.size > maxSize) {
        setError(`파일 크기가 ${maxSizeMB}MB를 초과합니다.`);
        return;
      }

      setIsUploading(true);
      try {
        await onUpload(file);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "파일 업로드에 실패했습니다.",
        );
      } finally {
        setIsUploading(false);
      }
    },
    [maxSize, maxSizeMB, onUpload],
  );

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled || isUploading) return;
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    // 같은 파일 재선택 가능하도록 리셋
    e.target.value = "";
  }

  // 업로드된 파일이 있으면 미리보기
  if (value) {
    return (
      <div className="flex items-center gap-3 rounded-lg border border-zinc-700 bg-zinc-900/50 p-3">
        <Icon className="h-5 w-5 shrink-0 text-violet-400" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm text-zinc-200">
            {fileName || "업로드된 파일"}
          </p>
          <p className="truncate text-xs text-zinc-500">{value}</p>
        </div>
        <button
          type="button"
          onClick={onRemove}
          disabled={disabled}
          className="shrink-0 rounded-md p-1 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    );
  }

  return (
    <div>
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled && !isUploading) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && !isUploading && inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          isDragOver
            ? "border-violet-500 bg-violet-950/20"
            : "border-zinc-700 bg-zinc-900/30 hover:border-zinc-600"
        } ${disabled || isUploading ? "pointer-events-none opacity-50" : ""}`}
      >
        <Icon
          className={`h-8 w-8 ${isDragOver ? "text-violet-400" : "text-zinc-600"}`}
        />
        <p className="text-sm text-zinc-400">
          {isUploading ? "업로드 중..." : placeholder}
        </p>
        <p className="text-xs text-zinc-600">최대 {maxSizeMB}MB</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="hidden"
      />
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  );
}
