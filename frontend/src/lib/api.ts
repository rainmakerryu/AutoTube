import { supabase } from "@/lib/supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiClient(path: string, options: RequestInit = {}) {
  const url = `${API_URL}${path}`;
  
  // Get current session for authentication
  const { data: { session } } = await supabase.auth.getSession();
  const token = session?.access_token;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add Authorization header if session exists
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const API_TIMEOUT_MS = 30000;
  const id = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    
    clearTimeout(id);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      const detail = errorData.detail;
      const message =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join("; ")
            : `API request failed with status ${res.status}`;
      throw new Error(message);
    }

    return await res.json();
  } catch (error: unknown) {
    clearTimeout(id);
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error("요청 시간이 초과되었습니다. 서버 연결 상태를 확인해 주세요.");
    }
    throw error;
  }
}

// ─── 파이프라인 단계별 API 헬퍼 ───

export function runStep(
  projectId: string,
  step: string,
  provider: string,
  config?: Record<string, unknown>,
) {
  return apiClient(`/api/pipeline/${projectId}/steps/${step}/run`, {
    method: "POST",
    body: JSON.stringify({ provider, config }),
  });
}

export function getStepOutput(projectId: string, step: string) {
  return apiClient(`/api/pipeline/${projectId}/steps/${step}/output`);
}

export function approveStep(
  projectId: string,
  step: string,
  editedData?: Record<string, unknown>,
) {
  return apiClient(`/api/pipeline/${projectId}/steps/${step}/approve`, {
    method: "POST",
    body: JSON.stringify({ edited_data: editedData ?? null }),
  });
}

export function rejectStep(
  projectId: string,
  step: string,
  feedback?: string,
) {
  return apiClient(`/api/pipeline/${projectId}/steps/${step}/reject`, {
    method: "POST",
    body: JSON.stringify({ feedback: feedback ?? null }),
  });
}
