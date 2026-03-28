"use client";

import { Check, Zap, CreditCard } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { useRouter } from "next/navigation";

export default function PricingPage() {
  const [currentPlan, setCurrentPlan] = useState<string>("free");
  const [isUpgrading, setIsUpgrading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    async function fetchProfile() {
      try {
        const profile = await apiClient("/api/users/me");
        setCurrentPlan(profile.plan);
      } catch (error) {
        console.error("Failed to fetch profile", error);
      }
    }
    fetchProfile();
  }, []);

  async function handleUpgrade() {
    setIsUpgrading(true);
    try {
      await apiClient("/api/users/upgrade", { method: "POST" });
      setCurrentPlan("pro");
      // Redirect or show success
      router.refresh();
    } catch (_) {
      alert("업그레이드에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsUpgrading(false);
    }
  }

  return (
    <div className="flex flex-col items-center justify-center space-y-12 py-12">
      <div className="max-w-3xl text-center space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight text-zinc-50 sm:text-5xl">
          유튜브 자동화, <span className="text-indigo-500">껌값</span>으로 시작하세요.
        </h1>
        <p className="text-xl text-zinc-400">
          하루 1,000원. 담배 한 갑보다 싼 가격으로 당신의 채널을 성장시키세요.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl w-full px-4">
        {/* Free Plan */}
        <Card className="border-zinc-800 bg-zinc-900/50 flex flex-col">
          <CardHeader>
            <CardTitle className="text-zinc-50">Free</CardTitle>
            <CardDescription className="text-zinc-400">학습용 및 기초 테스트</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-6">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-zinc-50">0원</span>
              <span className="text-zinc-500 text-sm">/월</span>
            </div>
            <ul className="space-y-3 text-sm text-zinc-300">
              <FeatureItem>기본 짧은 영상 생성 (5개/월)</FeatureItem>
              <FeatureItem>기본 음성 합성 (Edge TTS)</FeatureItem>
              <FeatureItem>Pexels 스톡 미디어 연동</FeatureItem>
              <FeatureItem>워터마크 포함</FeatureItem>
            </ul>
          </CardContent>
          <CardFooter>
            <Button 
                variant="outline" 
                className="w-full border-zinc-700 bg-zinc-800 text-zinc-400 cursor-not-allowed"
                disabled
            >
              현재 플랜
            </Button>
          </CardFooter>
        </Card>

        {/* Pro Plan */}
        <Card className="relative border-indigo-500/50 bg-zinc-900/50 flex flex-col ring-1 ring-indigo-500/50">
          <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-4 py-1 text-xs font-semibold text-white">
            인기 메뉴 🚀
          </div>
          <CardHeader>
            <CardTitle className="text-zinc-50 flex items-center gap-2">
              Pro <Zap className="h-5 w-5 text-indigo-400 fill-indigo-400" />
            </CardTitle>
            <CardDescription className="text-zinc-400">본격적인 채널 운영을 위한 최고의 선택</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 space-y-6">
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-zinc-50">30,000원</span>
              <span className="text-zinc-500 text-sm">/월</span>
            </div>
            <ul className="space-y-3 text-sm text-zinc-300">
              <FeatureItem bold>무제한 영상 생성</FeatureItem>
              <FeatureItem bold>프리미엄 AI 모델 연동 (GPT-4o, Claude 3.5)</FeatureItem>
              <FeatureItem bold>고품질 ElevenLabs 음성 지원</FeatureItem>
              <FeatureItem bold>전용 ComfyUI 서버 연동</FeatureItem>
              <FeatureItem bold>워터마크 삭제 & 4K 지원</FeatureItem>
              <FeatureItem bold>우선 기술 지원</FeatureItem>
            </ul>
          </CardContent>
          <CardFooter>
            {currentPlan === "pro" ? (
                <Button className="w-full bg-green-600 hover:bg-green-700 text-white cursor-default">
                    현재 프로 사용중
                </Button>
            ) : (
                <Button 
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white shadow-[0_0_20px_rgba(79,70,229,0.3)] transition-all hover:scale-[1.02]"
                    onClick={handleUpgrade}
                    disabled={isUpgrading}
                >
                    {isUpgrading ? (
                        <>
                            <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent mr-2" />
                            업그레이드 중...
                        </>
                    ) : (
                        <>
                            <CreditCard className="mr-2 h-4 w-4" />
                            업그레이드 (껌값 결제)
                        </>
                    )}
                </Button>
            )}
          </CardFooter>
        </Card>
      </div>

      <div className="max-w-xl text-center">
        <p className="text-xs text-zinc-500">
          * 이 데모 버전에서는 실제로 결제가 이뤄지지 않으며, 버튼 클릭 시 즉시 프로 기능을 체험하실 수 있습니다.
          결제 시스템은 향후 업데이트에서 정식 도입될 예정입니다.
        </p>
      </div>
    </div>
  );
}

function FeatureItem({ children, bold }: { children: React.ReactNode; bold?: boolean }) {
  return (
    <li className="flex items-start gap-3">
      <Check className="mt-0.5 h-4 w-4 text-emerald-500 shrink-0" />
      <span className={bold ? "font-medium text-zinc-100" : ""}>{children}</span>
    </li>
  );
}
