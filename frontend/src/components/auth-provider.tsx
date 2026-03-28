"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import { Session, User } from "@supabase/supabase-js";
import { apiClient } from "@/lib/api";

type AuthContextType = {
  session: Session | null;
  user: User | null;
  plan: string;
  isLoading: boolean;
  signOut: () => Promise<void>;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType>({
  session: null,
  user: null,
  plan: "free",
  isLoading: true,
  signOut: async () => {},
  refreshProfile: async () => {},
});

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [plan, setPlan] = useState<string>("free");
  const [isLoading, setIsLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    try {
      const profile = await apiClient("/api/users/me");
      console.log("[AuthProvider] Profile update:", profile);
      if (profile && profile.plan) {
        setPlan(profile.plan);
      }
    } catch {
      // 백엔드 미실행 시 조용히 free plan 폴백
      setPlan("free");
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    // 1. 초기 세션 가져오기
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!mounted) return;
      
      setSession(session);
      setUser(session?.user ?? null);
      
      if (session?.user) {
        refreshProfile().finally(() => {
          if (mounted) setIsLoading(false);
        });
      } else {
        setIsLoading(false);
      }
    });

    // 2. 인증 상태 변화 구독
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (!mounted) return;

        setSession(session);
        setUser(session?.user ?? null);
        
        if (session?.user) {
          // If already loading, we wait for profile. If not, we might want to show loading again?
          // For now, we just ensure we clear it.
          try {
            await refreshProfile();
          } finally {
            if (mounted) setIsLoading(false);
          }
        } else {
          setPlan("free");
          setIsLoading(false);
        }
      }
    );

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, [refreshProfile]);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  return (
    <AuthContext.Provider value={{ session, user, plan, isLoading, signOut, refreshProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
