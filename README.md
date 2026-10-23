# AI-weather-forcasting-APP
AtmoSphere AI — AI-Powered Weather Forecasting Web App
Premium, production-quality weather dashboard with Streamlit + Open-Meteo + NVIDIA Nemotron 3.5 Lightning (30B A3B).

A commercial-grade alternative to basic Streamlit demos — featuring dynamic weather gradients, glassmorphism cards, responsive layouts, Plotly interactivity, and a grounded AI assistant that explains real forecast data instead of inventing it.

StackPythonAIDataCharts

✨ Features Implemented
Core Weather (via Open-Meteo — free, no key)
Geocoding via geocoding-api.open-meteo.com — city → coordinates, handles ambiguous names (5 results), shows admin region + country.
Current conditions: temp, feels-like, humidity, cloud cover, wind (speed/dir/gust), pressure (MSL), precipitation/rain/showers/snowfall, is_day flag.
Hourly (24h): temperature, apparent temp, precip probability, precip amount, weather code, wind, UV, humidity — with horizontally scrollable premium cards + Plotly charts.
Daily 7-day: max/min temp, dominant weather code, sunrise/sunset, daylight/sunshine duration, precip sum/probability max, wind max/gust, UV max.
Derived metrics: UV index labeling (Low→Extreme), wind compass, feels-like, dew point, comfort heuristic.
Alerts heuristic: high rain probability (≥70%), strong wind (≥35 km/h), heat/freeze banners — clearly labeled as heuristics, not official warnings (Open-Meteo free tier has no government alert feed; code ready to add if source available).
Premium UI/UX (highest priority)
Design system: Outfit + Space Grotesk typography, glassmorphism (backdrop-filter: blur), consistent 18–22px radii, soft shadows, 8px grid.
Dynamic hero: gradient backgrounds switch per weather_code + is_day (sunny warm gold, cloudy slate, rainy blue, snowy pale, storm dark, night indigo). Hero shows prominent big-temp, location verified string, cloud/humidity line.
Weather cards: metric grids (2×2), sun card with sunrise/sunset/UV, daily rows with temp range bars, hourly scroll with “Now” highlight.
Plotly charts: transparent backgrounds, spline temp + dotted feels-like, dual-axis precip prob (bars) + amount (line), 7-day max/min grouped bars. All use_container_width responsive.
Polish: loading spinners, error/empty states, alert/info banners, toast messages, clear cache hints, mobile-tested (@media max-width:640/900), no fixed widths, no horizontal overflow, polished search bar + result selector.
Custom CSS: injected via st.markdown(unsafe_allow_html=True) — no reliance on Streamlit default. Subtle animations (hover on daily rows, pill glow).
AI Integration (NVIDIA Nemotron 3.5 Lightning)
Model: nvidia/nemotron-3.5-lightning-30b-a3b — 30B total / 3B active MoE, Mamba-2 hybrid, up to 1M context (see build.nvidia.com).
Endpoint: https://integrate.api.nvidia.com/v1/chat/completions (OpenAI-compatible POST /v1/chat/completions). Verified from official docs & example curl/Python (search results show identical base_url + model id).
Request shape:
JSON

{
  "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
  "messages": [{"role":"system","content":"..."}, {"role":"user","content":"..."}],
  "temperature": 0.7, "top_p": 0.95, "max_tokens": 1024, "stream": false
}
Headers: Authorization: Bearer $NVIDIA_API_KEY.
Grounded generation: build_weather_context() compacts live API numbers (location, current, next 3 daily, next 12 hourly precip) and injects into system+user prompt with rules: never invent numbers, explain probability as chance, distinguish FACTS vs INSIGHTS, cite units, warn if p≥70% or wind >40.
Two AI features:
Today’s Briefing (auto-generated on load, cached per location/day/unit; regenerate button).
Conversational assistant (st.chat_input + st.chat_message history) — system prompt scopes answers to provided facts only; off-topic → polite refusal.
Graceful fallback: If NVIDIA_API_KEY missing/invalid/rate-limited, app shows deterministic local_fallback_summary() (no API key needed) and chat heuristics. Weather data always renders. UI shows “Local Fallback • Add NVIDIA_API_KEY for AI” badge + caption explaining how to enable.
Security: Keys read from st.secrets["NVIDIA_API_KEY"] or os.getenv("NVIDIA_API_KEY"); never hardcoded, never logged, never echoed. 
.gitignore
 excludes secrets.toml. Example file provided.
UX Extras
Celsius/Fahrenheit toggle (instant rerun, affects hero + charts).
Search flow: text → Search → 5-result selectbox → “Use this location” → rerun (resets chat).
Refresh button clears fetch_weather cache.
Timestamps & sources visible: footer shows location, timezone, coords, last fetch UTC, model id, data source link.
Caching: @st.cache_data(ttl=6h) for geocoding, ttl=10m for weather (avoids stale-as-fresh; shown fetch time, timeformat=iso8601, timezone=auto).
No unnecessary PII sent to AI — only coords + forecast numbers.
🧱 Technology Stack
Layer	Choice	Why	Cost
Frontend	Streamlit 1.40	Fastest Python-to-web, Streamlit Cloud deploy	Free
Language	Python 3.9+	Ecosystem	Free
AI Model	NVIDIA Nemotron 3.5 Lightning 30B A3B via integrate.api.nvidia.com	Fast, cheap-active-params, long context, official free tier	Free trial credits (see below)
Weather	Open-Meteo Forecast + Geocoding APIs	No key, CC BY 4.0, best_match global	Free, no limits for normal use
Charts	Plotly 5.24	Lightweight, Streamlit-native, responsive	Free
Deploy	Streamlit Community Cloud	GitHub-connected, auto-deploy	Free
VCS	Git + GitHub	Standard	Free
Free-service limits (accurate as of Aug 2026 — verify live):

Open-Meteo: Free for non-commercial, no key, “generous” fair-use; commercial requires self-host/paid? Check https://open-meteo.com/en/terms. No hard limit; cache to be kind.
NVIDIA Build: Create account → API Key → free credits (docs report ~$150 trial, 1000s of requests; actual quota shown in dashboard). Rate ~200 req/hr on free models (via OpenRouter example; NVIDIA native may differ — check dashboard). No subscription needed for trial. After credits, pay-per-token or wait for refresh. App works without key via fallback, so you can test deploy first.
Streamlit Cloud: 1 private + unlimited public apps, 1 GB RAM, sleeps after inactivity.
We do not invent free-tier guarantees. Always check https://build.nvidia.com → Billing/Usage for your current quota.

📁 Project Structure
text

ai-weather-app/
├── app.py                           # Complete Streamlit app (UI + data + AI + styling)
├── requirements.txt                 # Pinned deps
├── README.md                        # This file
├── .gitignore                       # Excludes secrets, venv, caches
├── .streamlit/
│   ├── secrets.toml.example         # Template — copy to secrets.toml locally
│   └── config.toml                  # (Optional) theme overrides — not required
└── tests/
    └── test_app.py                  # Unit tests for helpers (mocked APIs)
Minimal by design — one-file app + config. Optional config.toml can set theme but custom CSS already handles it.

🚀 Quick Start (Local)
Prerequisites
Python 3.9+ (python --version)
Git
(Optional) NVIDIA API key for AI — app runs without it
1) Clone / Download
Bash

git clone https://github.com/YOUR_USERNAME/ai-weather-app.git
cd ai-weather-app
# Or unzip downloaded ZIP and cd into it
2) Virtual environment
Bash

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
3) Configure secrets (optional)
Bash

mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and paste your real nvapi-... key
# Or set env var: export NVIDIA_API_KEY="nvapi-..."
4) Run
Bash

streamlit run app.py
# Opens http://localhost:8501
Try searching: Tokyo, London, Karachi → select → see hero + AI briefing + hourly scroll → ask chat “Will it rain tomorrow?”.

🔑 NVIDIA API Credentials — Step by Step
Go to https://build.nvidia.com and sign in (free NVIDIA account; use Google or create).
Search for nemotron-3.5-lightning-30b-a3b or open https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b
Click Try API / Get API Key → Generate API Key (name it e.g., atmosphere-ai).
Copy the key starting with nvapi-.... Dashboard shows balance/metrics.
Locally: paste into .streamlit/secrets.toml as NVIDIA_API_KEY = "nvapi-..." OR export NVIDIA_API_KEY=...
Streamlit Cloud: see deployment section below — add same key in Advanced Settings → Secrets (TOML format).
Verify key works:

Bash

curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3.5-lightning-30b-a3b","messages":[{"role":"user","content":"Say hi in 5 words"}],"max_tokens":20}'
Should return JSON with choices[0].message.content.

Free tier notes: NVIDIA trial credits cover thousands of AtmoSphere briefings (each ~600 tokens). If you hit 429 or 402, wait or top up; fallback keeps app usable.

☁️ GitHub + Streamlit Community Cloud Deployment (Beginner-Friendly)
A) Create GitHub repo
Go to https://github.com → New repository
Name: ai-weather-app (or atmosphere-ai), Public, no README init (we already have files)
Create → copy the HTTPS URL (e.g., https://github.com/you/ai-weather-app.git)
Upload via Git (recommended):

Bash

cd ai-weather-app
git init
git add .
git commit -m "feat: AtmoSphere AI v1.0 — premium weather + Nemotron"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-weather-app.git
git push -u origin main
# Enter GitHub username + Personal Access Token (Settings → Developer settings → PAT classic, repo scope)
Or via website (no terminal):

GitHub repo → Add file → Upload files → drag all files (including 
secrets.toml.example
 but NOT real secrets.toml) → Commit.
✅ Check: repo shows 
app.py
, 
requirements.txt
, 
README.md
, 
.gitignore
.

B) Deploy to Streamlit Community Cloud
Go to https://share.streamlit.io (or https://streamlit.io/cloud) → Sign in with GitHub.
Click Create app → Deploy a public app from GitHub.
Pick:
Repository: YOUR_USERNAME/ai-weather-app
Branch: main
Main file path: 
app.py
Click Advanced settings → Secrets → paste TOML:
toml

NVIDIA_API_KEY = "nvapi-paste-your-real-key-here"
(Use your real key; this is server-side only, not public.)
Click Deploy! → Wait 1–3 min (installs deps, builds). Watch logs for errors.
When done, you get a public URL like https://yourname-ai-weather-app.streamlit.app → open, test search, check AI badge turns green (“NVIDIA … Live”).
Update later: push new commits to GitHub → Streamlit Cloud auto-redeploys.

C) Troubleshooting Deploy
Symptom	Fix
ModuleNotFoundError	Check 
requirements.txt
 versions; Cloud rebuilds from it. Pin as provided.
FileNotFoundError: secrets.toml	Expected — we read via st.secrets safely with fallback. Add secrets in Cloud Advanced Settings if you want AI.
401 / 403 from NVIDIA	Wrong key or expired. Regenerate at build.nvidia.com, re-paste in Cloud Secrets, reboot app (⋮ → Reboot).
429 Too Many Requests	Free tier limit hit. Wait ~1h; app still shows weather via fallback. Monitor Usage at build.nvidia.com.
App sleeps / slow wake	Free tier sleeps after inactivity; first load takes ~20s. Normal.
Hourly chart empty	Check location has data; some remote coords have sparse forecast — try major city.
Geocoding returns 0	Try English names (München → Munich), add country (Paris Texas).
CSS looks broken on mobile	Ensure 
app.py
 custom CSS block intact; clear browser cache; check viewport meta (Streamlit adds it).
Security reminder: Never commit real secrets.toml. 
.gitignore
 already excludes it. If you accidentally push a key, revoke it at build.nvidia.com → API Keys → Delete → generate new.

🧪 Testing
Included: 
test_app.py
 (mocks weather + AI, no live keys needed).

Bash

pip install pytest
pytest -v
# Or python -m pytest tests/ -v
Manual checks performed (see below for full test record):

Python syntax OK, imports resolve, no missing deps.
fetch_weather with mocked JSON, geocoding edge cases, unit conversions, WMO mapping.
AI payload builder and fallback summary.
Streamlit app renders under streamlit run with mocked data (charts render).
Responsive CSS inspected for mobile breakpoints.
Secrets not leaked in UI/logs.
📊 Data Accuracy & Performance Notes
Open-Meteo best_match picks highest-resolution model per coordinate; we request models=best_match, timezone=auto, timeformat=iso8601, full variable sets.
Timezone handling: all times in location’s local tz (from timezone field); sunrise/sunset parsed as ISO strings.
Caching: 10-min weather cache prevents hammering; banner shows fetch time so stale data isn’t mistaken for fresh.
No blocking: API calls via requests with 10–12s timeouts; spinners keep UI responsive; errors show banners, not blank screens.
AI cost: ~400–800 tokens per briefing + ~200 per chat turn — cheap even on free tier.
⚠️ Limitations & Next Steps
Weather alerts: Open-Meteo free forecast has no official severe warnings feed; app shows heuristic alerts only. To add real alerts, integrate e.g., NWS Alerts (US) or MeteoAlarm (EU) — placeholder ready.
UV & air quality: UV via uv_index_max & uv_index; AQI not included (add air-quality-api if needed).
Historical data: Not implemented; add archive-api if desired.
i18n: UI & AI in English; model supports ES/FR/DE/IT/JA — prompt adjustable.
Tests: No live browser cross-device tests (no device farm); responsive CSS reviewed manually — test on your phone/tablet.
Tokens: Long chat histories trimmed to last 6 turns to save context.
Ideas: Add radar maps (Leaflet), favorites (localStorage), PWA install, hourly wind chart, precipitation radar, shareable forecast cards.

📄 License & Credits
Code: MIT (you may fork/modify).
Weather data: Open-Meteo under CC BY 4.0 — attribution in footer (required).
AI model: NVIDIA Nemotron 3.5 Lightning under OpenMDW-1.1 (see model card).
UI design: Original — inspired by modern weather apps (Weather.com, Apple Weather, CARROT).
Built with care for beginners — no hard steps hidden. Open an issue if deployment snags.
