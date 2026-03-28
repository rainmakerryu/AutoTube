"use client";

import { useState, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

const TITLE_MAX_LENGTH = 100;
const DESCRIPTION_MAX_LENGTH = 5000;
const TAG_MAX_LENGTH = 100;
const TAGS_MAX_COUNT = 30;

interface MetadataReviewProps {
  outputData: {
    title?: string;
    description?: string;
    tags?: string[];
  };
  onApprove: (editedData?: Record<string, unknown>) => void;
  onReject: () => void;
}

export function MetadataReview({ outputData, onApprove, onReject }: MetadataReviewProps) {
  const [title, setTitle] = useState(outputData.title ?? "");
  const [description, setDescription] = useState(outputData.description ?? "");
  const [tags, setTags] = useState<string[]>(outputData.tags ?? []);
  const [newTag, setNewTag] = useState("");
  const [isEdited, setIsEdited] = useState(false);

  const markEdited = useCallback(() => setIsEdited(true), []);

  const addTag = useCallback(() => {
    const trimmed = newTag.trim();
    if (!trimmed || tags.length >= TAGS_MAX_COUNT) return;
    if (trimmed.length > TAG_MAX_LENGTH) return;
    if (tags.includes(trimmed)) return;
    setTags((prev) => [...prev, trimmed]);
    setNewTag("");
    setIsEdited(true);
  }, [newTag, tags]);

  const removeTag = useCallback((index: number) => {
    setTags((prev) => prev.filter((_, i) => i !== index));
    setIsEdited(true);
  }, []);

  const handleApprove = () => {
    if (isEdited) {
      onApprove({ title, description, tags });
    } else {
      onApprove();
    }
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="pt-4 space-y-4">
          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <Label>제목</Label>
              <span className="text-xs text-muted-foreground">
                {title.length}/{TITLE_MAX_LENGTH}
              </span>
            </div>
            <Input
              value={title}
              onChange={(e) => { setTitle(e.target.value); markEdited(); }}
              maxLength={TITLE_MAX_LENGTH}
              placeholder="YouTube 동영상 제목"
            />
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center">
              <Label>설명</Label>
              <span className="text-xs text-muted-foreground">
                {description.length}/{DESCRIPTION_MAX_LENGTH}
              </span>
            </div>
            <Textarea
              value={description}
              onChange={(e) => { setDescription(e.target.value); markEdited(); }}
              maxLength={DESCRIPTION_MAX_LENGTH}
              rows={6}
              placeholder="YouTube 동영상 설명"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label>태그</Label>
              <span className="text-xs text-muted-foreground">
                {tags.length}/{TAGS_MAX_COUNT}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {tags.map((tag, i) => (
                <Badge
                  key={i}
                  variant="secondary"
                  className="cursor-pointer hover:bg-destructive/20"
                  onClick={() => removeTag(i)}
                >
                  {tag} &times;
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag();
                  }
                }}
                placeholder="태그 입력 후 Enter"
                maxLength={TAG_MAX_LENGTH}
                className="flex-1"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={addTag}
                disabled={tags.length >= TAGS_MAX_COUNT || !newTag.trim()}
              >
                추가
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

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
