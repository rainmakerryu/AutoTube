"use client";

import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { Film, Mail, Lock, Loader2, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function LoginPage() {
  const router = useRouter();
  const { session } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (session) {
      router.push("/dashboard");
    }
  }, [session, router]);

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
      router.push("/dashboard");
    } catch (err) {
      const errorStr = err instanceof Error ? err.message : String(err);
      setError(errorStr === "Invalid login credentials" ? "이메일 또는 비밀번호가 일치하지 않습니다." : errorStr);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      if (error) throw error;
      setSuccess("회원가입이 완료되었습니다! 이메일을 확인해 주세요 (또는 즉시 로그인이 가능할 수 있습니다).");
    } catch (err) {
      const errorStr = err instanceof Error ? err.message : String(err);
      setError(errorStr);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-950 p-4 selection:bg-violet-500/30">
      {/* Background decoration */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-violet-900/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-900/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative w-full max-w-[400px] space-y-8">
        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-lg shadow-violet-500/20">
            <Film className="h-8 w-8 text-white" />
          </div>
          <div className="text-center space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">AutoTube</h1>
            <p className="text-sm text-zinc-400">껌값으로 만나는 나만의 AI 유튜브 PD</p>
          </div>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-zinc-900/50 border border-zinc-800 p-1">
            <TabsTrigger value="login" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white">로그인</TabsTrigger>
            <TabsTrigger value="signup" className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white">회원가입</TabsTrigger>
          </TabsList>

          <div className="mt-6">
            {error && (
              <Alert variant="destructive" className="mb-4 bg-red-950/20 border-red-900/50 text-red-400">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {success && (
              <Alert className="mb-4 bg-emerald-950/20 border-emerald-900/50 text-emerald-400">
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}

            <TabsContent value="login">
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-zinc-400 text-xs font-medium">이메일</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 h-4.5 w-4.5 text-zinc-500" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="name@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 bg-zinc-900/50 border-zinc-800 text-white placeholder:text-zinc-600 focus-visible:ring-violet-500"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-zinc-400 text-xs font-medium">비밀번호</Label>
                    <button type="button" className="text-[10px] text-zinc-500 hover:text-violet-400 transition-colors">비밀번호를 잊으셨나요?</button>
                  </div>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 h-4.5 w-4.5 text-zinc-500" />
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 bg-zinc-900/50 border-zinc-800 text-white placeholder:text-zinc-600 focus-visible:ring-violet-500"
                      required
                    />
                  </div>
                </div>
                <Button 
                  type="submit" 
                  disabled={isLoading}
                  className="w-full bg-violet-600 hover:bg-violet-500 text-white h-11 font-semibold shadow-lg shadow-violet-600/20"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <ArrowRight className="h-4 w-4 mr-2" />}
                  로그인 하기
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-email" className="text-zinc-400 text-xs font-medium">이메일 주소</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="name@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-zinc-900/50 border-zinc-800 text-white placeholder:text-zinc-600 focus-visible:ring-violet-500"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-password" className="text-zinc-400 text-xs font-medium">비밀번호 설정</Label>
                  <Input
                    id="signup-password"
                    type="password"
                    placeholder="6자 이상 입력"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="bg-zinc-900/50 border-zinc-800 text-white placeholder:text-zinc-600 focus-visible:ring-violet-500"
                    required
                    minLength={6}
                  />
                </div>
                <Button 
                  type="submit" 
                  disabled={isLoading}
                  className="w-full bg-zinc-100 hover:bg-white text-zinc-950 h-11 font-semibold"
                >
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  새 계정 만들기
                </Button>
                <p className="text-[10px] text-center text-zinc-500 mt-4 leading-relaxed">
                  회원가입 시 서비스 이용약관 및 개인정보 처리방침에<br />동의하는 것으로 간주됩니다.
                </p>
              </form>
            </TabsContent>
          </div>
        </Tabs>

        <div className="pt-4 text-center">
            <p className="text-[11px] text-zinc-600 font-medium tracking-wide uppercase">
              Limited SaaS Alpha v0.1.0
            </p>
        </div>
      </div>
    </div>
  );
}
