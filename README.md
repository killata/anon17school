# 🎭 Anonymous School Confessions & Opinions Platform (Unnamed Project)

## 📖 Project Overview

This is an unnamed hybrid Telegram Bot and Telegram Mini App (TMA) platform designed for broadcasting anonymous messages to a dedicated Telegram channel. It provides an uncensored, free-speech environment where students can openly share their thoughts, confessions, memes, and unfiltered opinions about school life, classmates, teachers, and administration—restricted **only** by the hard boundaries of the national law of the Republic of Kazakhstan, rather than subjective moral policing.

### ✨ Key Features

* **100% Sender Anonymity:** Public channel posts contain zero metadata linking back to the author.
* **Creator Operational Security (OpSec):** Architected from the ground up to prevent school administration or third parties from identifying the creator/maintainer, while remaining strictly law-abiding so law enforcement has no legal grounds for intervention.
* **Rich Mini App Interface (Next.js):** A sleek, native-feeling WebView interface for composing posts, selecting categories (e.g., *#Crush*, *#Rant*, *#Classmates*, *#Administration*), attaching media, and previewing messages before submission.
* **Law-Only Moderation:** Submissions are routed to a private moderation group equipped with inline action buttons (`✅ Approve`, `❌ Reject`, `🚫 Ban Hash`) to filter out strictly illegal content while allowing sharp criticism, satire, and free expression.
* **Anti-Spam & Rate Limiting:** Built-in throttling via Redis to prevent flood attacks while maintaining privacy.

---

## 🏗️ System Architecture

The application follows a modern **Monorepo / Service-Oriented Architecture**, combining the Telegram Bot (`aiogram 3`) and the REST API (`FastAPI`) into a unified asynchronous Python backend, paired with a `Next.js` frontend for the Telegram Mini App.

### Data Flow Diagram

```
+-------------------------------------------------------------------+
|                        TELEGRAM ECOSYSTEM                         |
|                                                                   |
|  +--------------------+                   +--------------------+  |
|  |   Telegram User    |                   |  Public TG Channel |  |
|  +---------+----------+                   +---------+----------+  |
|            |                                        ^             |
|            | 1. Opens Mini App / Sends Cmd          | 6. Publishes|
|            v                                        |    Approved |
|  +--------------------+                             |    Post     |
|  |  Next.js Mini App  |                             |             |
|  |  (@telegram-apps)  |                             |             |
|  +---------+----------+                             |             |
+------------|----------------------------------------|-------------+
             | 2. HTTPS Request (Cloudflare Proxy)    |
             | (Header: X-Telegram-Init-Data)         |
             v                                        |
+-----------------------------------------------------|-------------+
|                        UNIFIED BACKEND              |             |
|                                                     |             |
|  +--------------------------------------------------+----------+  |
|  |                        FastAPI Server                       |  |
|  |  - Validates HMAC-SHA256 `initData` via aiogram utilities   |  |
|  |  - Strips EXIF metadata & hashes user IDs in memory         |  |
|  |  - Receives Telegram Webhook updates (`/webhook/bot`)       |  |
|  +---------+----------------------------------------+----------+  |
|            |                                        |             |
|            | 3. Saves Submission                    | 4. Triggers |
|            v                                        v             |
|  +--------------------+                   +--------------------+  |
|  |  PostgreSQL & Redis|                   |   aiogram 3 Core   |  |
|  |  (SQLAlchemy 2.0)  |                   |  (Routers & FSM)   |  |
|  +--------------------+                   +---------+----------+  |
|                                                     |             |
+-----------------------------------------------------|-------------+
                                                      | 5. Moderation
                                                      v
                                            +--------------------+
                                            |  Admin Mod Group   |
                                            | (Creator Anon Mode)|
                                            | [Approve] [Reject] |
                                            +--------------------+
```

### Recommended Directory Structure

```
anonymous-school-bot/
├── backend/                     # Python Backend (FastAPI + aiogram 3)
│   ├── app/
│   │   ├── api/                 # FastAPI routers for the Mini App
│   │   │   ├── deps.py          # Dependency Injection (DB session, initData auth)
│   │   │   └── v1/
│   │   │       └── posts.py     # Endpoints for creating/fetching anonymous posts
│   │   ├── bot/                 # aiogram 3 Telegram Bot
│   │   │   ├── filters/         # Custom filters (Admin check, legal regex filters)
│   │   │   ├── handlers/        # Modular routers (user.py, moderation.py)
│   │   │   ├── keyboards/       # Inline & Reply builders (WebApp buttons)
│   │   │   └── middlewares/     # Throttling, DB session injection, No-IP Logging
│   │   ├── core/                # Config (pydantic-settings), security, constants
│   │   ├── db/                  # SQLAlchemy 2.0 async models & Alembic migrations
│   │   ├── services/            # Business logic (EXIF scrubber, PostService)
│   │   └── main.py              # Entrypoint mounting FastAPI & aiogram Webhook
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                    # Next.js 14+ Telegram Mini App (App Router)
│   ├── src/
│   │   ├── app/                 # Pages & Layouts
│   │   ├── components/          # UI Components (PostForm, TagSelector, LegalNotice)
│   │   ├── hooks/               # Custom hooks (useTelegram, useHapticFeedback)
│   │   └── lib/                 # API client (automatically attaches initData)
│   ├── Dockerfile
│   └── package.json
│
└── docker-compose.yml           # Orchestrates Backend, Frontend, Postgres, Redis, Nginx
```

---

## 🕵️‍♂️ Creator Operational Security (OpSec) & Anti-Deanonymization

To ensure the school administration, IT staff, or peers can **never** identify the creator of the platform, the project enforces strict technical and behavioral isolation:

### 1. Telegram Account & Bot Ownership Isolation
* **Burner Creation Account:** The bot (`@BotFather`), the public channel, and the admin moderation group must be created and owned by a dedicated Telegram account registered on a virtual/anonymous number (e.g., Fragment `+888` anonymous number or an external SIM not linked to the creator's student records) accessed exclusively via VPN/Proxy.
* **Anonymous Admin Mode:** Inside the moderation group and public channel, the creator's account has the **"Remain Anonymous" (`Send as Group/Channel`)** permission enabled, hiding the account from the member list.
* **Zero Cross-Contamination:** Never forward messages from the personal student account to the bot's admin group, and never grant admin rights to your real Telegram account.

### 2. Infrastructure & Domain Privacy
* **WHOIS & DNS Masking:** The domain used for the Mini App and Webhook must be registered via a privacy-first registrar (e.g., Njalla, Porkbun, or Cloudflare Registrar) with full WHOIS redaction.
* **Cloudflare Reverse Proxy:** Both the Next.js frontend and FastAPI backend sit behind **Cloudflare Proxy (Orange Cloud)** with `Strict SSL`. If school IT administrators run `nslookup` or `traceroute` on the Mini App URL, they only see Cloudflare anycast IPs, never the origin VPS IP.
* **Decoupled Hosting & Payment:** The VPS is hosted outside local school networks and paid for via methods that do not expose personal school-linked details, with SSH password authentication disabled in favor of Ed25519 keys.

### 3. Code & Repository Hygiene
* **Anonymous Git Commits:** Before making any commit, configure local Git credentials to prevent leaking your real name or personal email in the commit history:
  ```
  git config user.name "core-maintainer"
  git config user.email "noreply@localhost"
  ```
* **Never Code on School Wi-Fi:** Never access the VPS via SSH or push to the repository using school Wi-Fi or school-managed devices without an encrypted tunnel, preventing local network traffic inspection (DPI/SNI logging).
* **Automatic EXIF Stripping:** Any image uploaded via the Mini App or Bot has its EXIF metadata (GPS coordinates, phone model, creation timestamp) stripped in memory via `Pillow` before being forwarded to the channel.

---

## ⚖️ Legal Framework (Republic of Kazakhstan) & Free-Speech Policy

### Core Philosophy: Law Over Morality
To protect the creator from legal liability while maximizing freedom of speech:
1. **Why Law-Abiding Matters for OpSec:** School administration has **zero legal authority** to demand user data from Telegram or Cloudflare on their own. The *only* way they can escalate is by filing a police report. By strictly complying with the laws of the Republic of Kazakhstan (RK), police complaints from offended teachers or principals will be rejected due to the absence of *corpus delicti* (состав правонарушения).
2. **Rejection of Moral Censorship:** Subjective opinions, harsh criticism of teaching quality, complaints about school conditions, gossip, sarcasm, irony, and unpopular views about classmates or staff are **100% permitted**, provided they are framed as *value judgments* (оценочные суждения) rather than illegal acts.

### Strictly Prohibited Content (Per RK Legislation)

Moderation filters out **only** content that violates the Criminal Code (УК РК) or the Code of Administrative Offenses (КоАП РК):

| Legal Category | RK Legal Reference | What is Blocked (Hard Line) | What is Allowed (Free Speech) |
| :--- | :--- | :--- | :--- |
| **Personal Data & Privacy (Doxxing)** | **Art. 147 УК РК** & **Art. 79 КоАП РК** (*Law on Personal Data*) | Publishing private phone numbers, home addresses, IIN (ИИН), leaked private photos from closed accounts without consent, or medical secrets. | Discussing public actions at school, mentioning first names/classes in the context of school events, or discussing public staff roles. |
| **Defamation (Клевета)** | **Art. 73-3 КоАП РК** | Knowingly false *factual accusations* of crimes or corrupt acts (e.g., *"Teacher X stole 500,000 KZT from the budget"* without proof). | **Value judgments & opinions** (e.g., *"I think Teacher X explains the subject terribly and grades unfairly"*). Opinions cannot be proven true or false and are not defamation under RK law. |
| **Direct Insults (Оскорбление)** | **Art. 131 УК РК** | Direct degradation of a specific named individual's honor using obscene/profane language (*непристойная форма*) aimed specifically at their person. | Criticizing behavior, outfits, school policies, or general rants/memes that do not target a specific person with direct obscenities. |
| **Bullying of Minors (Травля / Буллинг)** | **Art. 127-2 КоАП РК** | Systematic humiliation, calls to boycott/harass a specific student, or cyberstalking. | Single critical opinions, confessing dislikes, or discussing interpersonal drama without inciting harassment. |
| **Threats, Extremism & Swatting** | **Art. 115, 174, 273 УК РК** | Threats of physical violence, false reports of terrorism/school attacks (Art. 273), or inciting ethnic/religious/social hatred (Art. 174). | Heated debates on school topics, dark humor that does not constitute a threat or extremist call. |
| **Pornography & Illegal Substances** | **Art. 299-1, 311, 312 УК РК** | Any intimate/NSFW imagery (especially involving minors), or promotion/links related to narcotics, vapes, or illegal substances. | Discussing relationships, crushes, or healthy lifestyle topics. |

### Safe Harbor & Takedown Mechanism
To further shield the platform under the **Law of the RK "On Online Platforms and Online Advertising"**:
* Every post footer or channel bio includes a `/report` mechanism.
* If a post inadvertently contains personal data or violates RK law, any user or administrator can submit its Post ID via the bot with a legal justification for immediate removal—neutralizing any claim of malicious intent by the platform creator.

---

## 🏆 Engineering Best Practices

This project strictly adheres to industry best practices for building scalable, secure Telegram Bots and Mini Apps:

### 1. Security & Cryptographic Validation
* **Zero-Trust Frontend:** The backend never trusts raw `user_id` parameters passed from the frontend. Every request from the Next.js Mini App includes the raw `window.Telegram.WebApp.initData` string in the `Authorization` header.
* **Native Signature Verification:** FastAPI validates the `HMAC-SHA256` signature using `aiogram.utils.web_app.safe_parse_webapp_init_data` and the bot's secret token before executing any endpoint logic.
* **Salted Ephemeral Hashing:** To allow moderators to block spammers or illegal posters without knowing *who* the student is, user IDs are never stored in plain text. They are hashed with a daily/monthly rotating cryptographic salt (`HMAC-SHA256(user_id, SECRET_SALT)`). Even if the database is compromised, student identities cannot be reversed.

### 2. Separation of Concerns (Service Layer Pattern)
* **Thin Handlers & Endpoints:** Neither `aiogram` handlers nor `FastAPI` routes contain direct database queries or complex business logic.
* **Unified Service Layer:** Both the bot and the Mini App call the same `PostService` (e.g., `await PostService.create_anonymous_post(...)`). Whether a student submits a confession via the bot chat or via the Mini App form, it flows through the exact same legal pre-check and moderation pipeline.

### 3. Asynchronous Non-Blocking I/O
* **100% Async Stack:** Blocking synchronous libraries (`requests`, `time.sleep`, standard `psycopg2`) are strictly prohibited in the event loop. The project uses `httpx` / `aiohttp` for external calls and `SQLAlchemy 2.0 (asyncpg)` for database operations.
* **Dependency Injection via Middlewares:** Database sessions are managed per-request/per-update using `aiogram` outer middlewares and FastAPI `Depends()`, ensuring zero connection leaks.

### 4. Webhooks Over Long Polling in Production
* While Long Polling (`dp.start_polling()`) is supported for local development, production runs exclusively on **Webhooks** mounted directly onto the FastAPI application (`app.post("/webhook/bot")`) using a secret token header (`X-Telegram-Bot-Api-Secret-Token`).

### 5. Native Telegram Mini App UX
* **Theme Synchronization:** The Next.js frontend uses Telegram's CSS variables (`--tg-theme-bg-color`, `--tg-theme-button-color`) to seamlessly adapt to the user's dark or light mode.
* **Native Controls & Haptics:** The app utilizes Telegram's native `MainButton`, `BackButton`, and `HapticFeedback` API via `@telegram-apps/sdk-react` to feel like an organic part of the messenger.

---

## 🚀 Getting Started (Local Development)

### Prerequisites
* **Python 3.11+** & **Node.js 20+**
* **Docker & Docker Compose** (for PostgreSQL and Redis)
* **Cloudflare Tunnel (`cloudflared`)** (Telegram Mini Apps require an `HTTPS` URL even during local testing)

### 1. Environment Variables
Create a `.env` file in the root directory:

```
# Telegram Configuration
BOT_TOKEN=1234567890:AAF_your_bot_token_here
WEBHOOK_SECRET=super_secret_webhook_token
PUBLIC_CHANNEL_ID=-1001234567890
ADMIN_MOD_GROUP_ID=-1009876543210
ANONYMITY_SALT=random_cryptographic_salt_string_min_32_chars

# Database & Redis
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/anon_db
REDIS_URL=redis://localhost:6379/0

# URLs (Update with your HTTPS tunnel URL for local dev)
MINI_APP_URL=https://your-tunnel-url.trycloudflare.com
NEXT_PUBLIC_API_URL=https://your-api-tunnel.trycloudflare.com/api/v1
```

### 2. Run Backend (FastAPI + aiogram)
```
cd backend
pip install poetry
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload --port 8000
```

### 3. Run Frontend (Next.js Mini App)
```
cd frontend
npm install
npm run dev
```

## 📄 License
This project is released into the public domain under the Unlicense / MIT License.