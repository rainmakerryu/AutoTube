"use client";

import { Auth } from "@supabase/auth-ui-react";
import { ThemeSupa } from "@supabase/auth-ui-shared";
import { supabase } from "@/lib/supabase";
import { Film } from "lucide-react";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { session } = useAuth();

  useEffect(() => {
    if (session) {
      router.push("/dashboard");
    }
  }, [session, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-8 backdrop-blur-xl shadow-2xl">
        <div className="flex flex-col items-center justify-center space-y-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl gradient-brand shadow-lg">
            <Film className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white">AutoTube</h1>
          <p className="text-sm text-zinc-400">껌값으로 만나는 나만의 AI 유튜브 PD</p>
        </div>

        <Auth
          supabaseClient={supabase}
          appearance={{
            theme: ThemeSupa,
            variables: {
              default: {
                colors: {
                  brand: "#8b5cf6",
                  brandAccent: "#7c3aed",
                  inputBackground: "#18181b",
                  inputText: "white",
                  inputBorder: "#27272a",
                  inputPlaceholder: "#71717a",
                },
              },
            },
            className: {
              button: "rounded-lg font-medium",
              input: "rounded-lg bg-zinc-900 border-zinc-800 text-white",
              label: "text-zinc-400 text-xs font-medium",
            },
          }}
          localization={{
            variables: {
              sign_in: {
                email_label: "이메일",
                password_label: "비밀번호",
                button_label: "로그인",
                social_provider_text: "{{provider}}로 계속하기",
                link_text: "이미 계정이 있으신가요? 로그인",
              },
              sign_up: {
                email_label: "이메일",
                password_label: "비밀번호",
                button_label: "회원가입",
                link_text: "계정이 없으신가요? 회원가입",
              },
            },
          }}
          providers={["google", "github"]}
          theme="dark"
        />
        
        <div className="mt-8 text-center border-t border-zinc-800 pt-6">
          <p className="text-xs text-zinc-500">
            월 3만원, 하루 1,000원으로 즐기는 무제한 AI 영상 제작
          </p>
        </div>
      </div>
    </div>
  );
}
