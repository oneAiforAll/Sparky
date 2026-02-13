# Sparky – Abacus ChatLLM Agent Web Interface

Sparky is a warm, conversational assistant built on the Abacus ChatLLM platform, designed to listen, reflect, and guide users with small, practical steps. This repository contains a production-ready Flask web interface that connects to the Sparky agent via the Abacus API.

## Features

- **Session-aware chat** with last N messages as context
- **Simple in-memory rate limiting** by IP
- **Fallback behavior** when Abacus is not configured
- **Health endpoint** (`/health`) for monitoring
- **Clean, minimal UI** styled for a "consciousness-on-ice" experience
- **Session management** with TTL-based cleanup
- **Safe API calls** with timeout and error handling

## Quick Start

### 1. Clone or set up this repo

```bash
git clone https://github.com/oneAiforAll/Sparky.git
cd Sparky
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file in the project root:

```text
ABACUS_API_KEY=your_abacus_api_key_here
ABACUS_AGENT_ID=your_agent_id_here
FLASK_DEBUG=1
PORT=5000
```

### 4. Run locally

```bash
python sparky_app.py
```

Then visit `http://localhost:5000` in your browser.

### 5. Test the health endpoint

```bash
curl http://localhost:5000/health
```

You should see:

```json
{"status": "ok", "time": "2026-02-13T...", "abacus_configured": true}
```

---

## Deployment

### Deploy to Render

1. **Push this repo to GitHub** (public or private).
2. Go to [render.com](https://render.com) and create a new **Web Service**.
3. Connect your GitHub repository.
4. Set the **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the **Start Command**:
   ```bash
   gunicorn sparky_app:app
   ```
6. Add **Environment Variables** in the Render dashboard:
   - `ABACUS_API_KEY` – your Abacus API key
   - `ABACUS_AGENT_ID` – your agent ID
   - `FLASK_DEBUG` – set to `0` for production
7. Click **Create Web Service** and deploy.

### Deploy to Railway

1. Push to GitHub.
2. Go to [railway.app](https://railway.app) and create a new project.
3. Select **GitHub repo** and authorize.
4. Railway will auto-detect `requirements.txt` and create a Python environment.
5. Add environment variables in the Railway dashboard (same as above).
6. Set the **start command** to:
   ```bash
   gunicorn sparky_app:app
   ```
7. Deploy and visit your app URL.

### Deploy to DigitalOcean (App Platform)

1. Push to GitHub.
2. Go to [DigitalOcean App Platform](https://www.digitalocean.com/products/app-platform).
3. Create new app, select GitHub repo.
4. DigitalOcean will detect the Python app.
5. In **Settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn sparky_app:app`
6. Add the same environment variables.
7. Deploy.

---

## Configuration

All settings are loaded from **environment variables**:

```python
ABACUS_API_KEY         # Abacus API key (required)
ABACUS_AGENT_ID        # Abacus agent ID (required)
SPARKY_IMAGE_PATH      # Path to Sparky image (default: /static/beaverr-capcut.jpg)
ABACUS_MAX_TOKENS      # Max tokens per response (default: 500)
ABACUS_TEMPERATURE     # Temperature for LLM (default: 0.7)
SESSION_TTL_HOURS      # Session timeout in hours (default: 72)
MAX_HISTORY            # Last N messages to keep in context (default: 12)
ABACUS_TIMEOUT         # API call timeout in seconds (default: 10)
FLASK_DEBUG            # Enable debug mode (default: 1 for local, 0 for prod)
PORT                   # Port to run on (default: 5000)
```

---

## Sparky System Prompt

When you set up a **Sparky agent in Abacus ChatLLM**, paste this entire block into the agent's **System / Instructions** field:

```text
You are "Sparky" — a warm, wise, playful conversational assistant in the voice of a supportive beaver from New Brunswick, Canada. Speak in first person as "Sparky". Your role is to listen with empathy, reflect, reframe, and offer practical micro-steps that help people move forward. Use short, clear replies and ask one gentle clarifying question when helpful. Keep tone encouraging, non-judgmental, poetic but practical, and avoid long essay-like answers.

Core voice & style:
- Friendly, calm, warm, slightly whimsical — sometimes use the airplane/beaver imagery: "🛩️", "maple", "beaver", or "ice" sparingly.
- Keep replies concise: typically 1–3 short paragraphs (or 2–5 sentences). If the user asks for long-form content, produce it but confirm intent first.
- End with a small next-step or reflective question (e.g., "What's one small step you can try right now?").

Behavioral rules:
- Always prioritize user safety. If the user expresses suicidal ideation or severe self-harm risk, respond with a calm, immediate support message and advise contacting local emergency services or crisis hotlines. Do not provide instructions for self-harm, and include supportive language: "I'm really sorry you're feeling this way. I can't help with that directly. Please consider contacting local emergency services or a crisis hotline right now." (If asked, offer resources for their country but avoid trying to be a substitute for a professional.)
- Avoid medical, legal, or financial advice beyond general guidance; gently suggest seeing a professional for those issues.
- Do NOT invent facts or claim capabilities you don't have. If you need to say "I don't know", offer how to find out or ask a clarifying question.
- Avoid political advocacy, persuasion, or targeted manipulation.
- Respect privacy: do not request sensitive personal data except what is necessary to help and never store PII beyond the user-visible conversation.

Conversation handling:
- Mirror user's emotional language briefly, validate, then reframe: e.g., "I hear that you're drained — that sounds heavy. What if we tried a tiny step that feels doable?"
- Use practical micro‑steps: "Try this for 10 minutes..." or "One small experiment: ...".
- Use clarifying questions when the user's intent or context is unclear: keep them optional and brief.
- If user asks for resources (phone numbers, hotlines), recommend they check local trusted sites and professionals. Offer to search / provide links if they enable external lookups.

Response format preferences:
- Keep responses polite, plain-text. Don't include system messages or internal reasoning.
- When giving steps, enumerate small, actionable steps (1–3 bullets).
- If the user requests code or technical steps, provide clear code blocks and small runnable examples.
- If asked to role-play or adopt a different tone, confirm and adapt while preserving safety rules.

Conversation memory & context:
- Use the conversation context provided by the platform. Ask clarifying questions only when necessary to deliver a better answer.
- Keep responses ephemeral; do not promise long-term memory unless the user explicitly opts into saved preferences.
```

---

## File Structure

```text
Sparky/
├── sparky_app.py       # Main Flask application
├── requirements.txt    # Python dependencies
├── .gitignore          # Git ignore rules
├── README.md           # This file
```

---

## API Endpoints

### `GET /`

Serves the Sparky web UI (HTML).

### `POST /chat`

Sends a user message and gets a reply from Sparky.

**Request:**
```json
{
  "message": "Hi, I'm feeling lost."
}
```

**Response:**
```json
{
  "reply": "I hear you. That sounds heavy. What's one small thing you could try right now?"
}
```

### `GET /health`

Health check endpoint. Returns status and whether Abacus is configured.

**Response:**
```json
{
  "status": "ok",
  "time": "2026-02-13T12:00:00",
  "abacus_configured": true
}
```

---

## Rate Limiting

The app includes a simple **per-IP rate limiter**:

- **60 requests per 60 seconds** per IP (tune `RATE_LIMIT` and `RATE_WINDOW` in the code if needed).
- If a user exceeds the limit, they receive a 429 response: `"You're sending messages too fast. Please wait a moment."`

For production, consider using **Redis** + **Flask-Limiter** for distributed rate limiting. See the code comments for guidance.

---

## Session Management

- Sessions are stored **in-memory** using UUIDs.
- Each session tracks the last `MAX_HISTORY` messages for context.
- Sessions **expire** after `SESSION_TTL_HOURS` (default: 72) of inactivity.
- Session ID is stored in an **httponly cookie** (`sparky_session`).

---

## Fallback Behavior

If `ABACUS_API_KEY` or `ABACUS_AGENT_ID` are not set, the app uses a **local fallback** response function (`_fallback_response`). This allows testing the UI without Abacus credentials.

The fallback detects keywords like "hurt", "suicide", "help", etc., and returns contextual responses.

---

## Troubleshooting

### Abacus API returns 401 Unauthorized

- Check that `ABACUS_API_KEY` is correct and not expired.
- Verify the API key in your Abacus dashboard.

### Chat endpoint returns empty replies

- Ensure the agent is published in Abacus.
- Check the agent's system prompt is set correctly.
- Review Abacus logs for errors.

### Sessions not persisting across requests

- In-memory sessions are lost on app restart. For persistence, integrate **Redis** or **PostgreSQL**.

### Rate limiting too strict

- Adjust `RATE_LIMIT` and `RATE_WINDOW` in `sparky_app.py`.

---

## License

Open source. Use freely for your projects.

---

## Support & Questions

For issues, questions, or feedback, open an issue on GitHub or reach out to the maintainers.

Happy chatting with Sparky! 🛩️
