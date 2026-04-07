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
  // 기존 6종
  { id: "realistic", name: "사실적", description: "실사 느낌의 고품질 이미지" },
  { id: "cinematic", name: "시네마틱", description: "영화같은 조명과 구도" },
  { id: "anime", name: "애니메이션", description: "일본 애니메이션 스타일" },
  { id: "watercolor", name: "수채화", description: "부드러운 수채화 느낌" },
  { id: "3d", name: "3D 렌더링", description: "3D 그래픽 스타일" },
  { id: "minimal", name: "미니멀", description: "깔끔한 미니멀 디자인" },
  // 신규 14종
  { id: "kwebtoon", name: "K-웹툰", description: "한국 웹툰 스타일" },
  { id: "kwebtoon_realistic", name: "K-웹툰 실사", description: "실사풍 한국 웹툰" },
  { id: "american_comic", name: "미국 코믹북", description: "마블/DC 스타일 코믹" },
  { id: "pencil_sketch", name: "연필 스케치", description: "연필 드로잉 스타일" },
  { id: "cyberpunk", name: "사이버펑크", description: "네온빛 미래 도시 스타일" },
  { id: "clay", name: "클레이 애니", description: "클레이메이션 스타일" },
  { id: "stopmotion", name: "스톱모션", description: "기괴한 스톱모션 스타일" },
  { id: "oil_painting", name: "유화", description: "클래식 유화 스타일" },
  { id: "pixel_art", name: "픽셀 아트", description: "레트로 8bit 스타일" },
  { id: "storybook", name: "동화 일러스트", description: "그림책 스타일" },
  { id: "noir", name: "느와르", description: "흑백 필름 느와르 스타일" },
  { id: "pop_art", name: "팝 아트", description: "워홀 스타일 팝 아트" },
  { id: "pastel", name: "파스텔", description: "부드러운 파스텔 톤" },
  { id: "vintage", name: "빈티지", description: "레트로 빈티지 필름" },
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
  customAudioUrl: string;
  customAudioName: string;
}

// ── Subtitle ──────────────────────────────────────────────
export interface SubtitleConfig {
  enabled: boolean;
  style: string;
  fontSize: number;
  position: string;
  outlineWidth: number;
  opacity: number;
}

export const SUBTITLE_STYLES = [
  { id: "youtube", name: "유튜브 기본", description: "흰색 텍스트 + 검정 배경", color: "#FFFFFF", bg: "#000000CC" },
  { id: "yellow_bold", name: "노란 볼드", description: "노란색 굵은 텍스트", color: "#FFD700", bg: "none" },
  { id: "white_outline", name: "흰색 외곽", description: "흰색 텍스트 + 검정 외곽", color: "#FFFFFF", bg: "none" },
  { id: "neon_green", name: "네온 그린", description: "네온 초록색 + 글로우", color: "#39FF14", bg: "none" },
  { id: "cinema", name: "시네마", description: "영화자막 스타일", color: "#FFFFFF", bg: "#00000080" },
  { id: "none", name: "자막 미사용", description: "자막을 표시하지 않음", color: "", bg: "" },
] as const;

export const SUBTITLE_FONT_SIZE_MIN = 24;
export const SUBTITLE_FONT_SIZE_MAX = 72;
export const SUBTITLE_FONT_SIZE_STEP = 2;
export const SUBTITLE_FONT_SIZE_DEFAULT = 36;

export const SUBTITLE_POSITIONS = [
  { id: "bottom", label: "하단" },
  { id: "center", label: "중앙" },
  { id: "top", label: "상단" },
] as const;

export const SUBTITLE_OUTLINE_MIN = 0;
export const SUBTITLE_OUTLINE_MAX = 5;
export const SUBTITLE_OUTLINE_STEP = 1;
export const SUBTITLE_OUTLINE_DEFAULT = 2;

export const SUBTITLE_OPACITY_MIN = 0.5;
export const SUBTITLE_OPACITY_MAX = 1.0;
export const SUBTITLE_OPACITY_STEP = 0.1;
export const SUBTITLE_OPACITY_DEFAULT = 1.0;

// ── Video Sync ────────────────────────────────────────────
export type SyncMode = "normal" | "speed" | "cut" | "loop";

export const SYNC_MODES = [
  { id: "normal", name: "기본", description: "이미지를 오디오에 맞춰 균등 배분" },
  { id: "speed", name: "속도 조절", description: "이미지 전환 속도를 빠르게/느리게" },
  { id: "cut", name: "컷 편집", description: "이미지를 빠르게 전환 (빠른 컷)" },
  { id: "loop", name: "루프", description: "이미지를 부드럽게 반복 재생" },
] as const;

export interface VideoSyncConfig {
  mode: SyncMode;
  speedFactor: number;
}

export const SYNC_SPEED_MIN = 0.5;
export const SYNC_SPEED_MAX = 2.0;
export const SYNC_SPEED_STEP = 0.1;
export const SYNC_SPEED_DEFAULT = 1.0;

// ── Intro / Logo ─────────────────────────────────────────
export interface IntroConfig {
  introVideoUrl: string;
  introVideoName: string;
  logoUrl: string;
  logoName: string;
  logoPosition: string;
  logoOpacity: number;
}

export const LOGO_POSITIONS = [
  { id: "top-left", label: "좌측 상단" },
  { id: "top-right", label: "우측 상단" },
  { id: "bottom-left", label: "좌측 하단" },
  { id: "bottom-right", label: "우측 하단" },
] as const;

export const LOGO_OPACITY_MIN = 0.3;
export const LOGO_OPACITY_MAX = 1.0;
export const LOGO_OPACITY_STEP = 0.1;
export const LOGO_OPACITY_DEFAULT = 0.8;

// ── Audio Post-processing ─────────────────────────────────
export interface AudioPostConfig {
  enabled: boolean;
  mode: string;
}

export const AUDIO_POST_MODES = [
  { id: "normalize", name: "음량 정규화", description: "전체 음량을 일정하게 조정" },
  { id: "compress_normalize", name: "압축 + 정규화", description: "동적 범위 압축 후 음량 정규화" },
  { id: "dynamic_normalize", name: "동적 정규화", description: "구간별 음량을 자동 조정" },
  { id: "band_limit_normalize", name: "대역 제한 + 정규화", description: "불필요한 저/고주파 제거" },
  { id: "dereverb_eq", name: "잔향 제거 (EQ)", description: "EQ 기반 잔향 제거" },
  { id: "dereverb_complex", name: "잔향 제거 (복합)", description: "복합 필터 기반 잔향 제거" },
] as const;

// ── Thumbnail ────────────────────────────────────────────
export interface ThumbnailConfig {
  enabled: boolean;
}

// ── BGM ───────────────────────────────────────────────────
export interface BgmConfig {
  enabled: boolean;
  mood: string;
  volume: number;
}

export const BGM_MOODS = [
  { id: "calm", label: "차분한" },
  { id: "happy", label: "밝은" },
  { id: "dramatic", label: "극적인" },
  { id: "corporate", label: "비즈니스" },
  { id: "cinematic", label: "시네마틱" },
  { id: "upbeat", label: "에너지틱" },
] as const;

export const BGM_VOLUME_MIN = 0;
export const BGM_VOLUME_MAX = 0.5;
export const BGM_VOLUME_STEP = 0.05;
export const BGM_VOLUME_DEFAULT = 0.15;

// ── Form Data ──────────────────────────────────────────────
export interface FormData {
  type: string;
  script: ScriptConfig;
  imageStyle: ImageConfig;
  voice: VoiceConfig;
  audioPost: AudioPostConfig;
  subtitle: SubtitleConfig;
  videoSync: VideoSyncConfig;
  intro: IntroConfig;
  thumbnail: ThumbnailConfig;
  bgm: BgmConfig;
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
    customAudioUrl: "",
    customAudioName: "",
  },
  audioPost: {
    enabled: false,
    mode: "normalize",
  },
  subtitle: {
    enabled: true,
    style: "youtube",
    fontSize: 36,
    position: "bottom",
    outlineWidth: 2,
    opacity: 1.0,
  },
  videoSync: {
    mode: "normal",
    speedFactor: 1.0,
  },
  intro: {
    introVideoUrl: "",
    introVideoName: "",
    logoUrl: "",
    logoName: "",
    logoPosition: "top-right",
    logoOpacity: 0.8,
  },
  thumbnail: {
    enabled: false,
  },
  bgm: {
    enabled: true,
    mood: "calm",
    volume: 0.15,
  },
  steps: {
    script: true,
    tts: true,
    audio_post: false,
    images: true,
    video: true,
    bgm: true,
    subtitle: true,
    metadata: true,
    thumbnail: false,
    seo: true,
    sns: true,
  },
};

// ── Step Labels ────────────────────────────────────────────
export const STEP_LABELS = [
  "영상 타입",
  "대본 설정",
  "이미지 스타일",
  "AI 보이스",
  "자막 스타일",
  "최종 확인",
] as const;

export const TOTAL_STEPS = STEP_LABELS.length;
