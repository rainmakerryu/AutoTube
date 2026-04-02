// ── Video Type ──────────────────────────────────────────────
export const VIDEO_TYPES = [
  {
    value: "shorts" as const,
    label: "Shorts",
    description: "60초 세로 숏폼 영상",
    ratio: "9:16",
  },
  {
    value: "longform" as const,
    label: "Long-form",
    description: "5-15분 가로 영상",
    ratio: "16:9",
  },
];

// ── Script Settings ────────────────────────────────────────
export type ScriptMode = "basic" | "ai" | "manual";

export const LANGUAGES = [
  { id: "ko", label: "한국어" },
  { id: "en", label: "영어" },
] as const;

export const PURPOSES = [
  { id: "auto", label: "AI 자동" },
  { id: "sales", label: "판매" },
  { id: "promotion", label: "홍보" },
  { id: "daily", label: "일상" },
] as const;

export const TONES = [
  { id: "auto", label: "AI 자동" },
  { id: "humor", label: "가벼운 유머" },
  { id: "honest", label: "솔직한 톤" },
  { id: "persuasive", label: "설득하는 톤" },
  { id: "calm", label: "차분한 톤" },
  { id: "friendly", label: "친절한 톤" },
] as const;

export const SPEECH_STYLES = [
  { id: "auto", label: "AI 자동" },
  { id: "formal", label: "존댓말 (합니다체)" },
  { id: "polite", label: "존댓말 (해요체)" },
  { id: "casual", label: "반말" },
] as const;

export const OPENING_CLOSING_MAX_LENGTH = 50;

// ── Image Style ────────────────────────────────────────────
export const IMAGE_PROVIDERS = [
  { id: "pexels", name: "Pexels (스톡)", free: true },
  { id: "gemini", name: "Gemini", free: false },
  { id: "openai", name: "DALL-E", free: false },
  { id: "comfyui", name: "ComfyUI (로컬)", free: true },
] as const;

export const IMAGE_STYLES = [
  { id: "realistic", name: "사실적", description: "실사 느낌의 고품질 이미지" },
  { id: "cinematic", name: "시네마틱", description: "영화같은 조명과 구도" },
  { id: "anime", name: "애니메이션", description: "일본 애니메이션 스타일" },
  { id: "watercolor", name: "수채화", description: "부드러운 수채화 느낌" },
  { id: "3d", name: "3D 렌더링", description: "3D 그래픽 스타일" },
  { id: "minimal", name: "미니멀", description: "깔끔한 미니멀 디자인" },
] as const;

// ── Voice ──────────────────────────────────────────────────
export interface VoiceOption {
  id: string;
  name: string;
  gender: "male" | "female";
  tags: string;
  provider: "edgetts" | "openai";
  free: boolean;
}

export const VOICE_OPTIONS: VoiceOption[] = [
  // Edge TTS (무료)
  { id: "ko-KR-SunHiNeural", name: "선희", gender: "female", tags: "#여성 #밝음 #자연스러움", provider: "edgetts", free: true },
  { id: "ko-KR-InJoonNeural", name: "인준", gender: "male", tags: "#남성 #차분함 #뉴스", provider: "edgetts", free: true },
  { id: "ko-KR-BongJinNeural", name: "봉진", gender: "male", tags: "#남성 #성숙함", provider: "edgetts", free: true },
  { id: "ko-KR-GookMinNeural", name: "국민", gender: "male", tags: "#남성 #편안함", provider: "edgetts", free: true },
  { id: "ko-KR-JiMinNeural", name: "지민", gender: "female", tags: "#여성 #또박또박", provider: "edgetts", free: true },
  { id: "ko-KR-SeoHyeonNeural", name: "서현", gender: "female", tags: "#여성 #부드러움", provider: "edgetts", free: true },
  { id: "ko-KR-SoonBokNeural", name: "순복", gender: "female", tags: "#여성 #중년 #따뜻함", provider: "edgetts", free: true },
  { id: "ko-KR-YuJinNeural", name: "유진", gender: "female", tags: "#여성 #청년 #활발함", provider: "edgetts", free: true },
  // 영어 Edge TTS
  { id: "en-US-JennyNeural", name: "Jenny", gender: "female", tags: "#female #bright #natural", provider: "edgetts", free: true },
  { id: "en-US-GuyNeural", name: "Guy", gender: "male", tags: "#male #calm #news", provider: "edgetts", free: true },
  // OpenAI TTS (유료)
  { id: "alloy", name: "Alloy", gender: "female", tags: "#여성 #다큐 #차분함", provider: "openai", free: false },
  { id: "echo", name: "Echo", gender: "male", tags: "#남성 #내레이션 #신뢰감", provider: "openai", free: false },
  { id: "fable", name: "Fable", gender: "male", tags: "#남성 #동화 #포근함", provider: "openai", free: false },
  { id: "nova", name: "Nova", gender: "female", tags: "#여성 #AI비서 #평온함", provider: "openai", free: false },
  { id: "onyx", name: "Onyx", gender: "male", tags: "#남성 #중년 #묵직함", provider: "openai", free: false },
  { id: "shimmer", name: "Shimmer", gender: "female", tags: "#여성 #나레이션 #잔잔함", provider: "openai", free: false },
];

export const EMOTIONS = [
  { id: "normal", label: "일반" },
  { id: "excited", label: "흥분" },
  { id: "happy", label: "기쁨" },
  { id: "calm", label: "차분함" },
  { id: "whisper", label: "속삭임" },
] as const;

export const VOICE_SPEED_MIN = 0.5;
export const VOICE_SPEED_MAX = 2.0;
export const VOICE_SPEED_STEP = 0.1;
export const VOICE_SPEED_DEFAULT = 1.0;

// ── Form Data ──────────────────────────────────────────────
export interface ScriptConfig {
  mode: ScriptMode;
  title: string;
  topic: string;
  language: string;
  purpose: string;
  tone: string;
  speechStyle: string;
  openingComment: string;
  closingComment: string;
  productName: string;
  requiredInfo: string;
  referenceScript: string;
  manualScript: string;
}

export interface ImageConfig {
  provider: string;
  style: string;
}

export interface VoiceConfig {
  enabled: boolean;
  provider: string;
  voiceId: string;
  voiceName: string;
  emotion: string;
  speed: number;
}

export interface FormData {
  type: string;
  script: ScriptConfig;
  imageStyle: ImageConfig;
  voice: VoiceConfig;
  steps: Record<string, boolean>;
}

export const DEFAULT_FORM_DATA: FormData = {
  type: "shorts",
  script: {
    mode: "basic",
    title: "",
    topic: "",
    language: "ko",
    purpose: "auto",
    tone: "auto",
    speechStyle: "auto",
    openingComment: "",
    closingComment: "",
    productName: "",
    requiredInfo: "",
    referenceScript: "",
    manualScript: "",
  },
  imageStyle: {
    provider: "pexels",
    style: "cinematic",
  },
  voice: {
    enabled: true,
    provider: "edgetts",
    voiceId: "ko-KR-SunHiNeural",
    voiceName: "선희",
    emotion: "normal",
    speed: 1.0,
  },
  steps: {
    script: true,
    tts: true,
    images: true,
    video: true,
    subtitle: true,
    metadata: true,
  },
};

// ── Step Labels ────────────────────────────────────────────
export const STEP_LABELS = [
  "영상 타입",
  "대본 설정",
  "이미지 스타일",
  "AI 보이스",
  "최종 확인",
] as const;

export const TOTAL_STEPS = STEP_LABELS.length;
