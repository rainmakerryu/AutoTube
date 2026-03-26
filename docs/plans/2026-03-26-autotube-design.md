# AutoTube - YouTube Video Automation SaaS Design

## Overview

YouTube video automation platform. Users input a topic, select pipeline steps, and the system generates a complete video (Shorts or Long-form) ready for upload.

**Business Model**: SaaS subscription (Free / Pro $29 / Enterprise $99) with BYO API Key.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Vercel (Frontend)                 │
│  Next.js 16 (App Router)                            │
│  - Dashboard UI (projects, settings, progress)      │
│  - Auth (Clerk)                                     │
│  - Payments (Stripe)                                │
│  - SSE for real-time pipeline progress              │
└──────────────┬──────────────────────────────────────┘
               │ REST API
┌──────────────▼──────────────────────────────────────┐
│              Railway (Backend)                       │
│  FastAPI                                            │
│  - /api/projects    Project CRUD                    │
│  - /api/pipeline    Pipeline execute/control        │
│  - /api/settings    API key management              │
│  - /api/billing     Subscription/usage              │
│  - /api/stream      SSE progress stream             │
│                                                     │
│  Celery Worker (video processing)                   │
│  - Script → TTS → Images → Video → Subtitle        │
│  - Thumbnail → Metadata → Upload                   │
└──────┬────────┬────────┬────────────────────────────┘
       │        │        │
┌──────▼──┐ ┌──▼───┐ ┌──▼──────────┐
│PostgreSQL│ │Redis │ │Cloudflare R2│
│- Users   │ │- Queue│ │- Videos     │
│- Projects│ │- Cache│ │- Audio      │
│- Usage   │ │- SSE  │ │- Images     │
│- Subs    │ │       │ │- Thumbnails │
└──────────┘ └──────┘ └────────────┘
```

**Scaling strategy**: Start monolithic (Option A), extract heavy services as needed (Option B).

---

## 2. Pipeline Design

Each step is an independent module. Users toggle ON/OFF per step.

```
[Topic] → ① Script → ② TTS → ③ Images → ④ Video → ⑤ Subtitle → ⑥ Thumbnail → ⑦ Metadata → ⑧ Upload
```

### Step Details

| Step | Input | Output | Tool | When OFF |
|------|-------|--------|------|----------|
| ① Script | topic + settings | text | Claude/GPT API | User pastes script |
| ② TTS | script text | MP3 | ElevenLabs/OpenAI TTS | User uploads audio |
| ③ Images | script keywords | N images | Gemini/DALL-E/Pexels | User uploads images |
| ④ Video | audio + images | MP4 | MoviePy + FFmpeg | Required (always ON) |
| ⑤ Subtitle | audio file | SRT + overlay | Whisper API | User uploads SRT |
| ⑥ Thumbnail | script + keywords | PNG | Pillow + AI image | User uploads image |
| ⑦ Metadata | script content | title/desc/tags | Claude/GPT API | User inputs manually |
| ⑧ Upload | MP4 + metadata | YouTube URL | YouTube Data API v3 | Download only |

### Format Specs

| Item | Shorts | Long-form |
|------|--------|-----------|
| Resolution | 1080x1920 (9:16) | 1920x1080 (16:9) |
| Duration | 30-60s | 5-15min |
| Images | 3-5 | 15-30 |
| Subtitle style | Large, centered | Bottom |
| Transitions | Fast cuts | Fade/slide |

### Pipeline Rules

- Output of each step feeds into the next (chain)
- Step OFF → user must provide that output manually
- Step failure → pause, user can retry or skip
- Step ④ (Video) is always required

---

## 3. Data Model

### User
- id, email, name, avatar
- plan: free | pro | enterprise
- created_at, updated_at

### ApiKey
- id, user_id
- provider: claude | openai | elevenlabs | youtube | gemini | pexels
- encrypted_key (AES-256-GCM)
- is_valid, last_verified_at

### Project
- id, user_id, title
- type: shorts | longform
- topic
- status: draft | processing | completed | failed
- pipeline_config (JSON — step ON/OFF + settings)

### PipelineStep
- id, project_id
- step: script | tts | images | video | subtitle | thumbnail | metadata | upload
- status: pending | running | completed | failed | skipped
- input_data (JSON), output_url (S3 path)
- error_message, duration_ms
- started_at, completed_at

### Asset
- id, project_id, step
- type: script | audio | image | video | subtitle | thumbnail
- storage_url (S3 path)
- file_size, mime_type

### Subscription
- id, user_id
- plan: free | pro | enterprise
- stripe_subscription_id
- status: active | canceled | past_due
- current_period_start, current_period_end

### UsageLog
- id, user_id
- action: video_generated | upload | tts_call | ai_call
- credits_used, month (YYYY-MM)

### Subscription Plans

| Item | Free | Pro ($29/mo) | Enterprise ($99/mo) |
|------|------|-------------|---------------------|
| Videos/month | 3 | 30 | Unlimited |
| Shorts | O | O | O |
| Long-form | X | O | O |
| YouTube upload | X | O | O |
| Thumbnail gen | X | O | O |
| Concurrent | 1 | 3 | 10 |
| Storage | 7 days | 30 days | 90 days |

---

## 4. API Key Management & Security

### Flow
1. User enters API key in web UI
2. Frontend → HTTPS → FastAPI
3. AES-256-GCM encryption → PostgreSQL
4. Pipeline execution → decrypt → API call → purge from memory

### Security Principles
- Transport: HTTPS only (TLS 1.3)
- Storage: AES-256-GCM, never plaintext
- Display: Masked `sk-...****1234`
- Usage: Decrypt only during pipeline, purge after
- Validation: Test call before saving
- Deletion: User can delete anytime

### Supported Providers
- OpenAI or Claude (script/metadata) — one required
- ElevenLabs (TTS) — required when TTS ON
- OpenAI Whisper (subtitle) — required when subtitle ON
- Gemini / DALL-E (images) — required when images ON
- Pexels (free stock) — optional
- YouTube (OAuth 2.0) — required when upload ON

### YouTube OAuth
- User clicks "Connect YouTube" → Google OAuth consent
- Store refresh_token (encrypted)
- Auto-refresh access_token on upload

---

## 5. Frontend Pages

```
/ (Landing)
├── /login, /signup              — Clerk auth
├── /dashboard                   — Project list + usage summary
├── /projects/new                — New video wizard
│   ├── Step 1: Type (shorts/longform)
│   ├── Step 2: Topic + settings
│   ├── Step 3: Pipeline ON/OFF
│   ├── Step 4: Upload files (for OFF steps)
│   └── Step 5: Preview + start
├── /projects/[id]               — Project detail
│   ├── Pipeline progress (real-time SSE)
│   ├── Step results preview/download
│   ├── Retry/edit
│   └── YouTube upload trigger
├── /settings
│   ├── API key management
│   ├── YouTube account (OAuth)
│   ├── Default video settings
│   └── Profile
├── /billing
│   ├── Current plan + usage
│   ├── Plan change (Stripe Checkout)
│   └── Payment history
└── /templates (Phase 3)
    ├── Preset styles
    └── Custom template save/load
```

### UI Style
- Dark mode default
- shadcn/ui + Geist font
- Pipeline progress: step indicator + progress bar
- Video preview: inline player

---

## 6. Infrastructure & Deployment

| Service | Role | Cost |
|---------|------|------|
| Vercel | Next.js frontend | $0 (Hobby) |
| Railway | FastAPI + Celery + Redis + PostgreSQL | $10-25/mo |
| Cloudflare R2 | File storage (S3-compatible, free egress) | ~$0.15/10GB |
| Domain | Custom domain | ~$1/mo |
| **Total** | | **~$15-30/mo** |

### Scaling Path
- Add Worker instances on Railway (horizontal)
- R2 auto-scales
- Upgrade Vercel to Pro ($20/mo) when needed

---

## 7. Tech Stack Summary

### Frontend
- Next.js 16 (App Router, TypeScript)
- shadcn/ui + Tailwind CSS
- Clerk (auth)
- Stripe (payments)
- Geist font (dark mode)

### Backend
- Python 3.12+ / FastAPI
- Celery + Redis (task queue)
- PostgreSQL (SQLAlchemy/Alembic)
- MoviePy + FFmpeg (video processing)
- Pillow (image/thumbnail)
- cryptography (AES-256-GCM for API keys)

### External APIs (user-provided)
- Claude / OpenAI (script, metadata)
- ElevenLabs / OpenAI TTS (voice)
- Gemini / DALL-E / Pexels (images)
- OpenAI Whisper (subtitles)
- YouTube Data API v3 (upload)

### Storage
- Cloudflare R2 (videos, audio, images)
- PostgreSQL (structured data)
- Redis (queue, cache, SSE pub/sub)
