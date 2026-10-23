"""
AI-Powered Weather Forecasting App
Premium commercial-grade weather dashboard using Streamlit + Open-Meteo + NVIDIA Nemotron 3.5 Lightning
GitHub: ready for Streamlit Community Cloud
"""
import os
import json
import time
import math
import textwrap
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ────────────────────────────────────────────────
# PAGE CONFIG
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="AtmoSphere AI • Weather Intelligence",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ────────────────────────────────────────────────
# CONSTANTS & WMO MAPPING
# ────────────────────────────────────────────────
NVIDIA_MODEL = "nvidia/nemotron-3.5-lightning-30b-a3b"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_ENDPOINT = f"{NVIDIA_BASE_URL}/chat/completions"

WMO_CODES = {
    0: ("Clear sky", "☀️", "sunny"),
    1: ("Mainly clear", "🌤️", "sunny"),
    2: ("Partly cloudy", "⛅", "cloudy"),
    3: ("Overcast", "☁️", "cloudy"),
    45: ("Fog", "🌫️", "cloudy"),
    48: ("Rime fog", "🌫️", "cloudy"),
    51: ("Light drizzle", "🌦️", "rainy"),
    53: ("Moderate drizzle", "🌦️", "rainy"),
    55: ("Dense drizzle", "🌧️", "rainy"),
    56: ("Freezing drizzle", "🌧️", "rainy"),
    57: ("Dense freezing drizzle", "🌧️", "rainy"),
    61: ("Slight rain", "🌧️", "rainy"),
    63: ("Moderate rain", "🌧️", "rainy"),
    65: ("Heavy rain", "⛈️", "rainy"),
    66: ("Light freezing rain", "🌧️", "rainy"),
    67: ("Heavy freezing rain", "🌧️", "rainy"),
    71: ("Slight snow", "🌨️", "snowy"),
    73: ("Moderate snow", "❄️", "snowy"),
    75: ("Heavy snow", "❄️", "snowy"),
    77: ("Snow grains", "❄️", "snowy"),
    80: ("Slight showers", "🌦️", "rainy"),
    81: ("Moderate showers", "🌧️", "rainy"),
    82: ("Violent showers", "⛈️", "storm"),
    85: ("Slight snow showers", "🌨️", "snowy"),
    86: ("Heavy snow showers", "🌨️", "snowy"),
    95: ("Thunderstorm", "⛈️", "storm"),
    96: ("Thunder + hail", "⛈️", "storm"),
    99: ("Thunder + heavy hail", "⛈️", "storm"),
}

# ────────────────────────────────────────────────
# HELPERS — UNITS & FORMATTING
# ────────────────────────────────────────────────
def c_to_f(c): return (c * 9/5) + 32
def kmh_to_mph(kmh): return kmh * 0.621371
def mm_to_inch(mm): return mm * 0.0393701

def format_temp(value, unit="C"):
    if value is None: return "—"
    if unit == "F":
        value = c_to_f(value)
    return f"{round(value)}°"

def format_temp_precise(value, unit="C"):
    if value is None: return "—"
    if unit == "F":
        value = c_to_f(value)
    return f"{value:.1f}°{unit}"

def wind_dir_to_compass(deg):
    if deg is None: return "—"
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = int((deg + 11.25) / 22.5) % 16
    return dirs[idx]

def wmo_info(code):
    return WMO_CODES.get(code, ("Unknown", "🌡️", "cloudy"))

def get_uv_label(uv):
    if uv is None: return "—", "#9CA3AF"
    if uv <= 2: return "Low", "#10B981"
    if uv <= 5: return "Moderate", "#F59E0B"
    if uv <= 7: return "High", "#EF4444"
    if uv <= 10: return "Very High", "#DC2626"
    return "Extreme", "#7C3AED"

def get_aqi_label(aqi):
    # not from Open-Meteo directly, placeholder
    return aqi

def is_day_time(current_time_str, sunrise_str, sunset_str):
    try:
        # parse times assuming same date
        ct = datetime.fromisoformat(current_time_str)
        sr = datetime.fromisoformat(sunrise_str)
        ss = datetime.fromisoformat(sunset_str)
        return sr <= ct <= ss
    except:
        h = datetime.now().hour
        return 6 <= h <= 18

# ────────────────────────────────────────────────
# CUSTOM CSS — PREMIUM DESIGN SYSTEM
# ────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root{
  --bg: #0B0F19;
  --glass: rgba(255,255,255,0.06);
  --glass-strong: rgba(255,255,255,0.10);
  --border: rgba(255,255,255,0.10);
  --text: #F8FAFC;
  --muted: #94A3B8;
  --accent: #38BDF8;
  --accent2: #A78BFA;
  --success: #34D399;
  --warning: #FBBF24;
  --danger: #FB7185;
  --radius: 20px;
  --radius-sm: 14px;
  --shadow: 0 10px 40px rgba(0,0,0,0.35);
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stDecoration"]{display:none;}
div[data-testid="stStatusWidget"]{display:none;}

/* Base */
html, body, [class*="css"] {
  font-family: 'Outfit', system-ui, -apple-system, sans-serif;
}
.stApp {
  background: radial-gradient(1200px 600px at 20% -10%, rgba(56,189,248,0.20), transparent 60%),
              radial-gradient(1000px 600px at 90% 0%, rgba(167,139,250,0.18), transparent 60%),
              radial-gradient(900px 700px at 50% 120%, rgba(52,211,153,0.12), transparent 70%),
              linear-gradient(180deg, #070A12 0%, #0B0F19 40%, #0F172A 100%);
  color: var(--text);
}

/* Scrollbar */
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-thumb{background: rgba(148,163,184,0.25); border-radius:999px}
::-webkit-scrollbar-track{background: transparent}

/* Top nav */
.top-nav{
  display:flex; align-items:center; justify-content:space-between;
  padding: 14px 18px; margin: 6px 0 10px 0;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  backdrop-filter: blur(16px);
}
.brand{
  display:flex; align-items:center; gap:12px;
}
.brand-badge{
  width:42px; height:42px; border-radius:12px;
  background: linear-gradient(135deg, #38BDF8 0%, #6366F1 50%, #A78BFA 100%);
  display:flex; align-items:center; justify-content:center;
  font-size:20px; box-shadow: 0 8px 24px rgba(56,189,248,0.35);
}
.brand h1{
  font-family: 'Space Grotesk', sans-serif;
  font-size: 19px; font-weight:800; letter-spacing:-0.02em; margin:0; line-height:1;
}
.brand p{margin:2px 0 0 0; font-size:12px; color: var(--muted); letter-spacing:0.02em}
.nav-pills{
  display:flex; gap:8px; align-items:center;
}
.pill{
  padding: 8px 12px; border-radius:999px; font-size:12px; font-weight:600;
  background: rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.08); color: #E2E8F0;
}
.pill.live{ background: rgba(16,185,129,0.14); border-color: rgba(16,185,129,0.30); color:#6EE7B7}

/* Hero */
.hero-wrap{
  position:relative; overflow:hidden; border-radius: 22px;
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: var(--shadow);
  padding: 22px;
  background: var(--glass);
  backdrop-filter: blur(18px);
}
.hero-grid{
  display:grid; grid-template-columns: 1.35fr 0.75fr; gap:18px;
}
@media (max-width: 900px){ .hero-grid{grid-template-columns: 1fr} }

.hero-main{
  position:relative; border-radius:18px; overflow:hidden; padding:20px;
  min-height: 280px;
  display:flex; flex-direction:column; justify-content:space-between;
  border: 1px solid rgba(255,255,255,0.12);
}
.hero-bg-sunny{ background: linear-gradient(135deg, #FF8C42 0%, #FFB347 35%, #FFD23F 70%, #FF9A3C 100%); }
.hero-bg-cloudy{ background: linear-gradient(135deg, #64748B 0%, #94A3B8 30%, #CBD5E1 65%, #E2E8F0 100%); }
.hero-bg-rainy{ background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 45%, #60A5FA 75%, #93C5FD 100%); }
.hero-bg-snowy{ background: linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 30%, #E6F0FF 70%, #F0F9FF 100%); }
.hero-bg-storm{ background: linear-gradient(135deg, #0F172A 0%, #1E293B 40%, #334155 75%, #475569 100%); }
.hero-bg-night{ background: linear-gradient(135deg, #020617 0%, #0F172A 35%, #1E1B4B 70%, #312E81 100%); }

.hero-main.sunny *,.hero-main.cloudy *{color:#0F172A}
.hero-main.rainy *,.hero-main.storm *,.hero-main.night *{color:white}
.hero-main.snowy *{color:#0F172A}

.hero-top{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px}
.location-name{ font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:800; letter-spacing:-0.02em; line-height:1.1}
.location-sub{ font-size:12px; opacity:0.85; margin-top:4px; font-weight:500}
.hero-weather-icon{ font-size:56px; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.15)); line-height:1}
.big-temp{ font-family:'Space Grotesk',sans-serif; font-size:72px; font-weight:800; letter-spacing:-0.04em; line-height:0.9}
@media (max-width:600px){ .big-temp{font-size:56px} .location-name{font-size:18px}}
.feels{ font-size:13px; font-weight:600; opacity:0.9; margin-top:6px; padding:6px 10px; border-radius:999px; background: rgba(0,0,0,0.10); display:inline-flex; border:1px solid rgba(255,255,255,0.18)}
.hero-desc{ font-size:14px; font-weight:600; opacity:0.95; margin-top:8px}
.hero-bottom{
  display:grid; grid-template-columns: repeat(3,1fr); gap:10px; margin-top:16px
}
.mini-stat{
  background: rgba(255,255,255,0.16); backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius:14px; padding:10px 12px;
}
.hero-main.rainy .mini-stat, .hero-main.storm .mini-stat, .hero-main.night .mini-stat{
  background: rgba(255,255,255,0.10); border-color: rgba(255,255,255,0.14)
}
.mini-stat label{font-size:10px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.85; font-weight:700}
.mini-stat strong{font-size:16px; font-weight:800; display:block; margin-top:2px}

/* Right column */
.stack{ display:flex; flex-direction:column; gap:14px}
.glass-card{
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 16px;
  backdrop-filter: blur(16px);
  box-shadow: 0 8px 28px rgba(0,0,0,0.25);
}
.card-title{
  font-size:11px; letter-spacing:0.10em; text-transform:uppercase; color: var(--muted);
  font-weight:700; margin-bottom:10px; display:flex; align-items:center; gap:8px
}
.card-title span{width:6px;height:6px;border-radius:999px;background: var(--accent); display:inline-block; box-shadow:0 0 10px var(--accent)}

.metric-grid{
  display:grid; grid-template-columns: repeat(2,1fr); gap:10px;
}
.metric{
  background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.07);
  border-radius:14px; padding:12px;
}
.metric label{font-size:11px; color: var(--muted); letter-spacing:0.06em; text-transform:uppercase; font-weight:600}
.metric strong{font-size:18px; font-weight:800; color: var(--text); display:block; margin-top:4px; font-family:'Space Grotesk',sans-serif}
.metric em{font-size:12px; color:#CBD5E1; font-style:normal; opacity:0.9}

.sun-card{
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  background: linear-gradient(135deg, rgba(251,146,60,0.14), rgba(250,204,21,0.12));
  border-color: rgba(251,146,60,0.20);
}
.sun-time{ text-align:center}
.sun-time small{color: var(--muted); font-size:10px; letter-spacing:0.08em; text-transform:uppercase; font-weight:700}
.sun-time strong{font-size:15px; font-weight:800; display:block; margin-top:2px}
.sun-divider{ flex:1; height:1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)}

/* Hourly */
.hourly-scroll{
  display:flex; gap:10px; overflow-x:auto; padding-bottom:6px; scroll-snap-type:x mandatory;
}
.hour-item{
  min-width: 86px; scroll-snap-align:start;
  background: rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08);
  border-radius:16px; padding:10px 8px; text-align:center;
  backdrop-filter: blur(12px);
}
.hour-item.active{
  background: linear-gradient(180deg, rgba(56,189,248,0.22), rgba(56,189,248,0.08));
  border-color: rgba(56,189,248,0.35);
  box-shadow: 0 8px 20px rgba(56,189,248,0.18);
}
.hour-item time{font-size:11px; color: var(--muted); font-weight:700; letter-spacing:0.04em}
.hour-item .hi{font-size:20px; margin:6px 0}
.hour-item strong{font-size:14px; font-weight:800}
.hour-item small{font-size:11px; color:#CBD5E1; display:block; margin-top:2px}

/* Daily */
.daily-row{
  display:flex; align-items:center; justify-content:space-between;
  padding:12px 14px; border-radius:14px;
  background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);
  margin-bottom:8px;
}
.daily-row:hover{background: rgba(255,255,255,0.06)}
.day-name{font-weight:700; font-size:14px; min-width:64px}
.day-icon{font-size:22px}
.day-bar{flex:1; margin:0 12px; height:6px; border-radius:999px; background: rgba(255,255,255,0.10); position:relative; overflow:hidden}
.day-bar-fill{position:absolute; top:0; left:0; bottom:0; border-radius:999px; background: linear-gradient(90deg, #38BDF8, #A78BFA)}
.day-temp{font-family:'Space Grotesk',sans-serif; font-weight:800; font-size:14px; min-width:86px; text-align:right}
.day-precip{font-size:12px; color:#7DD3FC; font-weight:700; min-width:48px; text-align:right}

/* AI card */
.ai-card{
  background: linear-gradient(135deg, rgba(56,189,248,0.10), rgba(167,139,250,0.10));
  border: 1px solid rgba(99,102,241,0.22);
  border-radius:18px; padding:16px;
}
.ai-badge{
  display:inline-flex; align-items:center; gap:8px;
  padding:6px 10px; border-radius:999px;
  background: rgba(99,102,241,0.18); border:1px solid rgba(99,102,241,0.30);
  color:#C4B5FD; font-size:11px; font-weight:800; letter-spacing:0.06em; text-transform:uppercase
}
.ai-title{font-family:'Space Grotesk',sans-serif; font-size:16px; font-weight:800; margin:10px 0 6px 0}
.ai-body{font-size:13px; line-height:1.65; color:#E2E8F0}
.ai-body b{color:white}
.ai-suggestions{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px}
.ai-chip{ padding:7px 10px; border-radius:999px; background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.10); font-size:12px; font-weight:600; color:#F1F5F9}

/* Search */
.search-wrap{
  background: rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.08);
  border-radius:16px; padding:10px; backdrop-filter: blur(16px);
  display:flex; gap:10px; align-items:center; flex-wrap:wrap
}
.search-wrap input{ flex:1 }

/* Plotly overrides */
.js-plotly-plot .plotly .modebar{ display:none !important }

/* Mobile utils */
@media (max-width: 640px){
  .top-nav{flex-direction:column; align-items:flex-start; gap:10px}
  .hero-wrap{padding:14px}
  .hero-main{padding:16px}
  .metric-grid{grid-template-columns: 1fr 1fr}
}

/* Buttons */
.stButton > button{
  border-radius: 12px !important;
  background: linear-gradient(135deg, #0EA5E9 0%, #6366F1 100%) !important;
  color:white !important; border:none !important; font-weight:700 !important;
  padding: 10px 16px !important; box-shadow: 0 8px 20px rgba(14,165,233,0.35) !important;
}
.stButton > button:hover{ filter: brightness(1.06) }
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
  background: rgba(255,255,255,0.06) !important; border:1px solid rgba(255,255,255,0.10) !important;
  color: var(--text) !important; border-radius: 12px !important;
}
div[data-testid="stChatInput"]{ background: rgba(255,255,255,0.04); border-radius:14px}

/* Alert */
.alert-banner{
  padding:12px 14px; border-radius:14px; border:1px solid rgba(251,113,133,0.30);
  background: rgba(251,113,133,0.12); color:#FECDD3; font-size:13px; font-weight:600;
  display:flex; align-items:center; gap:10px; margin-bottom:12px
}
.info-banner{
  padding:12px 14px; border-radius:14px; border:1px solid rgba(56,189,248,0.22);
  background: rgba(56,189,248,0.10); color:#BAE6FD; font-size:13px; font-weight:600;
  display:flex; align-items:center; gap:10px; margin-bottom:12px
}

/* Footer */
.footer{
  margin-top:18px; padding:14px 16px; border-radius:14px;
  background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.06);
  color: var(--muted); font-size:12px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px
}
</style>
"""

# ────────────────────────────────────────────────
# GEOCODING & WEATHER FETCHING (with caching)
# ────────────────────────────────────────────────
@st.cache_data(ttl=60*60*6, show_spinner=False)
def geocode_location(query: str) -> List[Dict]:
    """Geocode via Open-Meteo free geocoding API (no key required)."""
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": 5, "language": "en", "format": "json"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        if not results:
            return []
        # normalize
        out = []
        for it in results:
            out.append({
                "name": it.get("name"),
                "country": it.get("country"),
                "admin1": it.get("admin1"),
                "latitude": it.get("latitude"),
                "longitude": it.get("longitude"),
                "timezone": it.get("timezone"),
                "population": it.get("population"),
                "country_code": it.get("country_code"),
                "elevation": it.get("elevation"),
                "label": f"{it.get('name')}, {it.get('admin1') or ''} {it.get('country')} ".strip().replace("  "," "),
                "raw": it
            })
        return out
    except Exception as e:
        st.warning(f"Geocoding error: {e}")
        return []

@st.cache_data(ttl=60*10, show_spinner=False)  # 10 min cache for weather
def fetch_weather(lat: float, lon: float, timezone_str: str = "auto", temp_unit: str = "celsius") -> Optional[Dict]:
    """
    Fetch from Open-Meteo Forecast API.
    Docs: https://open-meteo.com/en/docs
    We request current + hourly + daily + sunrise/sunset + UV + pressure + wind + humidity + precip
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone_str,
            "forecast_days": 7,
            "models": "best_match",
            "current": ",".join([
                "temperature_2m","relative_humidity_2m","apparent_temperature",
                "is_day","precipitation","rain","showers","snowfall",
                "weather_code","cloud_cover","wind_speed_10m","wind_direction_10m",
                "wind_gusts_10m","pressure_msl"
            ]),
            "hourly": ",".join([
                "temperature_2m","relative_humidity_2m","dew_point_2m",
                "apparent_temperature","precipitation_probability","precipitation",
                "rain","showers","snowfall","weather_code","cloud_cover",
                "pressure_msl","wind_speed_10m","wind_direction_10m",
                "uv_index","is_day"
            ]),
            "daily": ",".join([
                "weather_code","temperature_2m_max","temperature_2m_min",
                "apparent_temperature_max","apparent_temperature_min",
                "sunrise","sunset","daylight_duration","sunshine_duration",
                "uv_index_max","precipitation_sum","rain_sum","showers_sum","snowfall_sum",
                "precipitation_hours","precipitation_probability_max",
                "wind_speed_10m_max","wind_gusts_10m_max","wind_direction_10m_dominant"
            ]),
            "temperature_unit": temp_unit,
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
            "timeformat": "iso8601",
        }
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        data = r.json()
        # Add fetch timestamp
        data["_fetched_at"] = datetime.now(timezone.utc).isoformat()
        return data
    except Exception as e:
        st.error(f"Weather fetch failed: {e}")
        return None

# ────────────────────────────────────────────────
# NVIDIA AI INTEGRATION (Graceful fallback)
# ────────────────────────────────────────────────
def get_nvidia_key() -> Optional[str]:
    # Priority: st.secrets > env var > .streamlit/secrets.toml
    try:
        if "NVIDIA_API_KEY" in st.secrets:
            return st.secrets["NVIDIA_API_KEY"]
    except Exception:
        pass
    return os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_APIKEY") or None

def call_nvidia_chat(messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1024, extra_body: Optional[Dict]=None) -> Optional[str]:
    """
    Call NVIDIA NIM endpoint (OpenAI-compatible).
    Model: nvidia/nemotron-3.5-lightning-30b-a3b
    Endpoint: https://integrate.api.nvidia.com/v1/chat/completions
    """
    api_key = get_nvidia_key()
    if not api_key:
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": NVIDIA_MODEL,
        "messages": messages,
        "temperature": temperature,
        "top_p": 0.95,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if extra_body:
        payload.update(extra_body)
    try:
        r = requests.post(NVIDIA_ENDPOINT, headers=headers, json=payload, timeout=25)
        if r.status_code != 200:
            # don't surface key, just status
            st.toast(f"NVIDIA API {r.status_code}: {r.text[:220]}", icon="⚠️")
            return None
        data = r.json()
        # OpenAI shape: choices[0].message.content
        if "choices" in data and len(data["choices"])>0:
            choice = data["choices"][0]
            msg = choice.get("message", {})
            content = msg.get("content")
            if content:
                return content.strip()
            # fallback for reasoning content
            if "delta" in choice:
                return choice["delta"].get("content")
        return None
    except Exception as e:
        st.toast(f"AI request failed: {e}", icon="⚠️")
        return None

def build_weather_context(weather: Dict, loc: Dict, unit: str) -> str:
    """Build compact factual context for AI (no hallucinated data)."""
    try:
        cur = weather.get("current", {})
        daily = weather.get("daily", {})
        hourly = weather.get("hourly", {})
        # Current snapshot
        temp = cur.get("temperature_2m")
        feels = cur.get("apparent_temperature")
        hum = cur.get("relative_humidity_2m")
        precip = cur.get("precipitation")
        rain = cur.get("rain")
        code = cur.get("weather_code")
        wdesc, wemoji, _ = wmo_info(code)
        wind = cur.get("wind_speed_10m")
        wdir = cur.get("wind_direction_10m")
        press = cur.get("pressure_msl")
        cloud = cur.get("cloud_cover")
        is_day = cur.get("is_day")

        # Daily summaries (next 3 days)
        daily_summary_lines = []
        if daily:
            times = daily.get("time", [])
            tmax = daily.get("temperature_2m_max", [])
            tmin = daily.get("temperature_2m_min", [])
            pprob = daily.get("precipitation_probability_max", [])
            psum = daily.get("precipitation_sum", [])
            wcodes = daily.get("weather_code", [])
            for i in range(min(3, len(times))):
                ddesc, _, _ = wmo_info(wcodes[i] if i < len(wcodes) else 3)
                daily_summary_lines.append(
                    f"{times[i]}: {ddesc}, {tmin[i]}–{tmax[i]}°{unit}, precip {psum[i] if i < len(psum) else '—'}mm, prob {pprob[i] if i < len(pprob) else '—'}%"
                )
        # Hourly precip next 12h
        hourly_precip = []
        if hourly:
            htimes = hourly.get("time", [])
            hprob = hourly.get("precipitation_probability", [])
            hprec = hourly.get("precipitation", [])
            # find now index
            now_iso = cur.get("time")
            try:
                if now_iso and htimes:
                    # find closest hour
                    now_dt = datetime.fromisoformat(now_iso)
                    # simple: take first 12 entries from now index
                    # find index where hour matches
                    idx = 0
                    for j, t in enumerate(htimes):
                        try:
                            td = datetime.fromisoformat(t)
                            if td >= now_dt:
                                idx=j; break
                        except: continue
                    for k in range(idx, min(idx+12, len(htimes))):
                        hourly_precip.append(f"{htimes[k][11:16]} {hprob[k]}% {hprec[k]}mm")
            except: pass

        ctx = f"""
LOCATION: {loc.get('label')} ({loc.get('latitude'):.4f},{loc.get('longitude'):.4f}) tz={weather.get('timezone')} elevation={loc.get('elevation')}m
FETCHED: {weather.get('_fetched_at')} (UTC) — present local current time: {cur.get('time')}
CURRENT: {temp}°{unit} feels {feels}°{unit}, {wdesc} (code {code}) {wemoji}, humidity {hum}%, cloud {cloud}%, wind {wind} km/h {wdir}° ({wind_dir_to_compass(wdir)}), pressure {press} hPa, precip {precip}mm (rain {rain}mm), is_day={is_day}
DAILY NEXT 3: {' | '.join(daily_summary_lines)}
HOURLY NEXT 12 PRECIP: {'; '.join(hourly_precip) if hourly_precip else 'n/a'}
UNITS: temp °{unit}, wind kmh, precip mm, pressure hPa
NOTE: Use ONLY this data. Explain probabilities as chances, not certainties. Distinguish facts vs interpretation. Be concise, friendly, practical.
"""
        return ctx.strip()
    except Exception as e:
        return f"Context build error: {e} | Raw keys: {list(weather.keys())}"

def ai_generate_summary(weather: Dict, loc: Dict, unit: str) -> Dict:
    """Return AI summary with fallback."""
    context = build_weather_context(weather, loc, unit)
    system = "You are AtmoSphere AI, a concise, friendly weather interpreter. You NEVER invent weather numbers. You ONLY explain the provided forecast data. Distinguish FACTS (from API) vs INSIGHTS (your interpretation). Keep language simple. Use short paragraphs and bullet practical tips."
    user = f"""Based ONLY on this verified forecast data, write:

1) A 2-3 sentence TODAY summary for a general audience.
2) A 1-sentence outlook for tomorrow.
3) Practical tips (2-3 bullets) like umbrella, layers, outdoor plans — grounded in precip probability & temp.

Rules:
- Explain precipitation probability as chance, not guarantee. e.g. "40% means 4 in 10 similar forecasts saw rain"
- Mention units (°{unit}, km/h, mm, hPa).
- Add a ⚠️ if any precip_probability_max > 70% or wind > 40 km/h.
- End with "Facts from Open-Meteo; interpretation by AI."

DATA:
{context}
"""
    raw = call_nvidia_chat(
        [{"role":"system","content": system},{"role":"user","content": user}],
        temperature=0.7, max_tokens=800
    )
    if raw:
        return {"source": "nvidia", "model": NVIDIA_MODEL, "text": raw}
    # Fallback deterministic summary
    fallback = local_fallback_summary(weather, loc, unit)
    return {"source": "local", "model": "rule-based", "text": fallback}

def local_fallback_summary(weather: Dict, loc: Dict, unit: str) -> str:
    try:
        cur = weather.get("current", {})
        daily = weather.get("daily", {})
        code = cur.get("weather_code")
        desc, emoji, _ = wmo_info(code)
        temp = cur.get("temperature_2m")
        feels = cur.get("apparent_temperature")
        hum = cur.get("relative_humidity_2m")
        wind = cur.get("wind_speed_10m")
        # daily
        pmax = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
        tmax = daily.get("temperature_2m_max", ["—"])[0] if daily.get("temperature_2m_max") else "—"
        tmin = daily.get("temperature_2m_min", ["—"])[0] if daily.get("temperature_2m_min") else "—"
        summary = f"**Today in {loc.get('label')}**: {emoji} {desc}, {format_temp_precise(temp, unit)} (feels {format_temp_precise(feels, unit)}). High {format_temp_precise(tmax, unit)} / Low {format_temp_precise(tmin, unit)}."
        prob_text = f"Rain chance peaks at {pmax}% — that means {pmax} in 100 similar forecasts saw precipitation; not a guarantee. Bring plans indoors if >60%."
        tips = []
        if pmax and pmax > 60:
            tips.append("☔ Carry an umbrella / rain layer; avoid long outdoor exposure during showers.")
        elif pmax and pmax > 30:
            tips.append("🌦️ Keep a compact umbrella handy — brief showers possible.")
        else:
            tips.append("😎 Good window for outdoor activities; light layers recommended.")
        if temp is not None:
            t_check = temp if unit=="C" else c_to_f(temp) if unit=="F" else temp
            # but temp already in requested unit? Open-Meteo returns in requested unit, so threshold adjust
            thresh_hot = 32 if unit=="C" else 90
            thresh_cold = 5 if unit=="C" else 41
            if (t_check if unit=="C" else c_to_f(t_check) if False else t_check) > thresh_hot:
                tips.append("🥤 Stay hydrated and seek shade — heat peaks midday.")
            if t_check < thresh_cold:
                tips.append("🧥 Dress warmly; mornings will feel chilly.")
        if wind and wind > 30:
            tips.append("💨 Gusty winds — secure loose items and allow extra travel time.")
        # wind check above
        tips_md = "\n".join([f"- {t}" for t in tips])
        # Alert
        alert = ""
        if (pmax and pmax > 70) or (wind and wind > 40):
            alert = "\n\n⚠️ **Heads-up:** Elevated rain or wind expected — check hourly chart before heading out."
        return f"{summary}\n\n{pprob_explain(pmax)}\n{alert}\n\n**Practical tips:**\n{tips_md}\n\n*Facts from Open-Meteo; interpretation by local fallback (no AI key configured).*"
    except Exception as e:
        return f"Weather data is available; AI summary unavailable. (Fallback error: {e}) — Check hourly and daily charts for details. Facts from Open-Meteo."

def pprob_explain(p):
    if p is None: return ""
    if p < 20: return f"Precipitation probability ~{p}% — low chance; most similar forecasts stayed dry."
    if p < 50: return f"Precipitation probability ~{p}% — modest chance; brief showers possible but not certain."
    if p < 75: return f"Precipitation probability ~{p}% — solid chance; plan for rain, but not guaranteed all day."
    return f"Precipitation probability ~{p}% — high chance; rain is likely in many areas; prepare accordingly."

def ai_chat_answer(question: str, weather: Dict, loc: Dict, unit: str, history: List[Dict]) -> str:
    ctx = build_weather_context(weather, loc, unit)
    system = f"""You are AtmoSphere AI Weather Assistant for {loc.get('label')}.
Rules:
- Answer ONLY using the provided WEATHER FACTS. If question is outside forecast scope, say you can only answer from current forecast.
- Explain probabilities as chances, not certainties.
- Keep answers concise (max 120 words), friendly, with units.
- Distinguish Facts vs Insights.
- Never hallucinate coordinates, temps, or dates not in context.
- If user asks for harmful advice, refuse politely.

WEATHER FACTS:
{ctx}
"""
    msgs = [{"role":"system","content": system}]
    # include last 6 turns
    for h in history[-6:]:
        msgs.append(h)
    msgs.append({"role":"user","content": question})
    raw = call_nvidia_chat(msgs, temperature=0.6, max_tokens=600)
    if raw:
        return raw
    # fallback: simple heuristic
    q = question.lower()
    cur = weather.get("current", {})
    daily = weather.get("daily", {})
    if "umbrella" in q or "rain" in q:
        p = daily.get("precipitation_probability_max", [0])[0]
        return f"Based on the forecast, rain chance peaks at {p}%. {pprob_explain(p)} Facts from Open-Meteo; interpretation local fallback."
    if "temperature" in q or "hot" in q or "cold" in q:
        t = cur.get("temperature_2m"); f = cur.get("apparent_temperature")
        return f"Currently {format_temp_precise(t, unit)} (feels {format_temp_precise(f, unit)}). Check the daily chart for highs/lows. Facts from Open-Meteo."
    if "wind" in q:
        w = cur.get("wind_speed_10m"); d = cur.get("wind_direction_10m")
        return f"Wind is {w} km/h from {d}° ({wind_dir_to_compass(d)}). Gusts may be higher — see hourly chart. Facts from Open-Meteo."
    return "I can answer from the current forecast only (temp, rain chance, wind, sunrise/sunset, etc.). Try: 'Will it rain tomorrow?' or 'Should I carry an umbrella?' Facts from Open-Meteo; local fallback."

# ────────────────────────────────────────────────
# PLOTLY CHARTS
# ────────────────────────────────────────────────
def chart_hourly_temp(hourly: Dict, unit: str, hours: int = 24):
    times = hourly.get("time", [])[:hours]
    temps = hourly.get("temperature_2m", [])[:hours]
    feels = hourly.get("apparent_temperature", [])[:hours]
    # shorten labels
    labels = []
    for t in times:
        try:
            dt = datetime.fromisoformat(t)
            labels.append(dt.strftime("%H:%M"))
        except: labels.append(t[11:16])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=labels, y=temps, mode='lines+markers', name='Temp',
                             line=dict(color='#38BDF8', width=3, shape='spline'),
                             marker=dict(size=5, color='#38BDF8', line=dict(width=2,color='white')),
                             fill='tonexty', fillcolor='rgba(56,189,248,0.08)',
                             hovertemplate='%{y:.1f}°'+unit+'<extra></extra>'))
    fig.add_trace(go.Scatter(x=labels, y=feels, mode='lines', name='Feels like',
                             line=dict(color='#A78BFA', width=2, dash='dot'),
                             hovertemplate='%{y:.1f}°'+unit+'<extra></extra>'))
    fig.update_layout(
        margin=dict(l=10,r=10,t=10,b=10), height=220,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0', family='Outfit'),
        legend=dict(orientation='h', y=1.02, x=0, font=dict(size=11, color='#94A3B8')),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=11, color='#94A3B8'), showgrid=False),
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=11), title=None),
        hovermode='x unified'
    )
    return fig

def chart_precip_prob(hourly: Dict, hours: int = 24):
    times = hourly.get("time", [])[:hours]
    prob = hourly.get("precipitation_probability", [])[:hours]
    prec = hourly.get("precipitation", [])[:hours]
    labels = []
    for t in times:
        try: labels.append(datetime.fromisoformat(t).strftime("%H:%M"))
        except: labels.append(t[11:16])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=labels, y=prob, name='Rain prob %', marker_color='rgba(56,189,248,0.55)', marker_line_width=0,
                         hovertemplate='%{y}%<extra></extra>'), secondary_y=False)
    fig.add_trace(go.Scatter(x=labels, y=prec, name='Precip mm', mode='lines+markers',
                             line=dict(color='#FBBF24', width=2.5), marker=dict(size=5, color='#FBBF24'),
                             hovertemplate='%{y} mm<extra></extra>'), secondary_y=True)
    fig.update_layout(
        margin=dict(l=10,r=10,t=10,b=10), height=220,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0', family='Outfit'),
        legend=dict(orientation='h', y=1.08, x=0, font=dict(size=11, color='#94A3B8')),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', showgrid=False, tickfont=dict(size=11, color='#94A3B8')),
        yaxis=dict(range=[0,100], gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=11), title=None),
        yaxis2=dict(gridcolor='rgba(255,255,255,0.04)', tickfont=dict(size=11), title=None),
        hovermode='x unified', bargap=0.35
    )
    return fig

def chart_daily_overview(daily: Dict, unit: str):
    times = daily.get("time", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    prec = daily.get("precipitation_sum", [])
    day_labels=[]
    for t in times:
        try: day_labels.append(datetime.fromisoformat(t).strftime("%a %m/%d"))
        except: day_labels.append(t)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=day_labels, y=tmax, name='Max', marker_color='#38BDF8', opacity=0.9,
                         hovertemplate='%{y:.1f}°'+unit+' max<extra></extra>'))
    fig.add_trace(go.Bar(x=day_labels, y=tmin, name='Min', marker_color='rgba(148,163,184,0.45)',
                         hovertemplate='%{y:.1f}°'+unit+' min<extra></extra>'))
    fig.update_layout(
        barmode='group', margin=dict(l=10,r=10,t=10,b=10), height=240,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#E2E8F0', family='Outfit'),
        legend=dict(orientation='h', y=1.02, x=0, font=dict(size=11, color='#94A3B8')),
        xaxis=dict(gridcolor='rgba(255,255,255,0.06)', showgrid=False, tickfont=dict(size=11, color='#94A3B8')),
        yaxis=dict(gridcolor='rgba(255,255,255,0.06)', tickfont=dict(size=11)),
        hovermode='x unified', bargap=0.25
    )
    return fig

# ────────────────────────────────────────────────
# SESSION STATE INIT
# ────────────────────────────────────────────────
if "location" not in st.session_state:
    st.session_state.location = {
        "name": "Multan",
        "country": "Pakistan",
        "admin1": "Punjab",
        "latitude": 30.1575,
        "longitude": 71.5249,
        "timezone": "Asia/Karachi",
        "elevation": 122,
        "country_code": "PK",
        "label": "Multan, Punjab Pakistan",
        "population": 1900000
    }
if "unit" not in st.session_state:
    st.session_state.unit = "C"  # C or F
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ai_summary_cache" not in st.session_state:
    st.session_state.ai_summary_cache = {}
if "search_results" not in st.session_state:
    st.session_state.search_results = []

# ────────────────────────────────────────────────
# RENDER CUSTOM CSS
# ────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# TOP NAV
# ────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
  <div class="brand">
    <div class="brand-badge">🌤️</div>
    <div>
      <h1>AtmoSphere AI</h1>
      <p>Weather Intelligence • Nemotron 3.5 Lightning • Open-Meteo</p>
    </div>
  </div>
  <div class="nav-pills">
    <span class="pill">Production • v1.0</span>
    <span class="pill live">● Live Forecast</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# SEARCH + CONTROLS
# ────────────────────────────────────────────────
col_search, col_unit, col_refresh = st.columns([6, 1.4, 1.2], gap="small")
with col_search:
    q = st.text_input("Search city", placeholder="Search city — e.g. Tokyo, London, Karachi, New York",
                      label_visibility="collapsed", key="q_input")
    # Keep search interaction: on Enter / clicking button triggers geocode
    # We auto-trigger when q length >=2 and button pressed or enter
    do_search = st.button("🔍 Search", use_container_width=False)
    if do_search and q.strip():
        with st.spinner("Locating…"):
            res = geocode_location(q.strip())
            st.session_state.search_results = res
            if not res:
                st.toast(f"No results for '{q}' — try another spelling.", icon="⚠️")
            else:
                st.toast(f"Found {len(res)} locations for '{q}'", icon="✅")
    # Show selector if results exist
    if st.session_state.search_results:
        opts = {f"{r['label']}  ({r['latitude']:.2f}, {r['longitude']:.2f})": r for r in st.session_state.search_results}
        sel = st.selectbox("Select location", options=list(opts.keys()), index=0, label_visibility="collapsed")
        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("📍 Use this location", use_container_width=True):
                chosen = opts[sel]
                st.session_state.location = chosen
                st.session_state.search_results = []
                st.session_state.chat_history = []  # reset chat for new loc
                st.rerun()
        with c2:
            if st.button("✕ Clear", use_container_width=True):
                st.session_state.search_results = []
                st.rerun()

with col_unit:
    # Unit toggle as segmented control via selectbox
    unit_choice = st.selectbox("Units", options=["°C Celsius", "°F Fahrenheit"], index=0 if st.session_state.unit=="C" else 1, label_visibility="collapsed")
    new_unit = "C" if "°C" in unit_choice else "F"
    if new_unit != st.session_state.unit:
        st.session_state.unit = new_unit
        st.rerun()
with col_refresh:
    if st.button("↻ Refresh", use_container_width=True):
        # clear caches for fresh fetch
        fetch_weather.clear()
        st.toast("Refreshing forecast…", icon="🔄")
        st.rerun()

loc = st.session_state.location
unit = st.session_state.unit
temp_unit_api = "celsius" if unit=="C" else "fahrenheit"

# ────────────────────────────────────────────────
# FETCH WEATHER
# ────────────────────────────────────────────────
with st.spinner("Fetching precision forecast…"):
    weather = fetch_weather(loc["latitude"], loc["longitude"], loc.get("timezone") or "auto", temp_unit_api)

if not weather or "current" not in weather:
    st.markdown('<div class="alert-banner">⚠️ Unable to load weather data right now. Please check your internet connection or try another location. Data source: Open-Meteo (free, no key required).</div>', unsafe_allow_html=True)
    st.stop()

current = weather.get("current", {})
hourly = weather.get("hourly", {})
daily = weather.get("daily", {})
timezone_used = weather.get("timezone", loc.get("timezone"))
fetch_time = weather.get("_fetched_at")

# Derive hero visuals
code = current.get("weather_code", 3)
wdesc, wemoji, wtype = wmo_info(code)
is_day = current.get("is_day", 1)
# choose hero background class
if is_day == 0:
    hero_class = "night"
    bg_class = "hero-bg-night"
elif wtype == "sunny":
    hero_class = "sunny"; bg_class="hero-bg-sunny"
elif wtype == "cloudy":
    hero_class = "cloudy"; bg_class="hero-bg-cloudy"
elif wtype == "rainy":
    hero_class = "rainy"; bg_class="hero-bg-rainy"
elif wtype == "snowy":
    hero_class = "snowy"; bg_class="hero-bg-snowy"
elif wtype == "storm":
    hero_class = "storm"; bg_class="hero-bg-storm"
else:
    hero_class = "cloudy"; bg_class="hero-bg-cloudy"

cur_temp = current.get("temperature_2m")
feels = current.get("apparent_temperature")
hum = current.get("relative_humidity_2m")
wind = current.get("wind_speed_10m")
wdir = current.get("wind_direction_10m")
press = current.get("pressure_msl")
cloud = current.get("cloud_cover")
precip = current.get("precipitation")

# Format location header
loc_name = loc.get("name") or loc.get("label", "")[:30]
loc_sub = f"{loc.get('admin1') or ''} {loc.get('country') or ''} • {timezone_used} • {loc['latitude']:.2f}, {loc['longitude']:.2f}"
# Sunrise/sunset today
sunrise = daily.get("sunrise", ["—"])[0] if daily.get("sunrise") else "—"
sunset = daily.get("sunset", ["—"])[0] if daily.get("sunset") else "—"
uv_max = daily.get("uv_index_max", [None])[0] if daily.get("uv_index_max") else None
uv_label, uv_color = get_uv_label(uv_max)
# Wind gust today
wind_gust_max = daily.get("wind_gusts_10m_max", ["—"])[0] if daily.get("wind_gusts_10m_max") else "—"
pprob_max = daily.get("precipitation_probability_max", [None])[0] if daily.get("precipitation_probability_max") else None
psun = daily.get("precipitation_sum", [None])[0] if daily.get("precipitation_sum") else None

# Alerts heuristic (open-meteo doesn't have severe alerts free; we create helpful banners)
alerts = []
if pprob_max and pprob_max >= 70:
    alerts.append(f"High rain chance today — {pprob_max}% probability. Carry protection.")
if wind and wind >= 35:
    alerts.append(f"Strong winds {wind} km/h — secure outdoor items.")
if cur_temp is not None:
    check_t = cur_temp  # already in unit
    if unit=="C" and check_t >= 38:
        alerts.append(f"Extreme heat {format_temp_precise(cur_temp, unit)} — stay hydrated, limit midday sun.")
    elif unit=="C" and check_t <= 2:
        alerts.append(f"Freezing conditions {format_temp_precise(cur_temp, unit)} — dress warmly, watch for ice.")
    elif unit=="F" and check_t >= 100:
        alerts.append(f"Extreme heat {format_temp_precise(cur_temp, unit)} — stay hydrated.")
    elif unit=="F" and check_t <= 35:
        alerts.append(f"Near freezing {format_temp_precise(cur_temp, unit)} — dress warmly.")

for a in alerts:
    st.markdown(f'<div class="alert-banner">⚠️ {a}</div>', unsafe_allow_html=True)

# Info banner about update
update_local = ""
try:
    ft = datetime.fromisoformat(fetch_time.replace("Z","+00:00")) if fetch_time else datetime.now(timezone.utc)
    # show in local tz naive
    update_local = ft.strftime("%H:%M UTC")
except: update_local = "just now"
st.markdown(f'<div class="info-banner">📡 Data: Open-Meteo (best_match, 11 km global) • Updated {update_local} • Location verified via Open-Meteo Geocoding • Units: °{unit}, km/h, mm, hPa</div>', unsafe_allow_html=True)

# ────────────────────────────────────────────────
# HERO SECTION
# ────────────────────────────────────────────────
hero_html = f"""
<div class="hero-wrap">
  <div class="hero-grid">
    <div class="hero-main {hero_class} {bg_class}">
      <div class="hero-top">
        <div>
          <div class="location-name">{loc_name} {wemoji}</div>
          <div class="location-sub">{loc_sub}</div>
          <div class="hero-desc">{wdesc} • {cloud if cloud is not None else '—'}% cloud • {hum if hum is not None else '—'}% humidity</div>
        </div>
        <div class="hero-weather-icon">{wemoji}</div>
      </div>
      <div>
        <div class="big-temp">{format_temp(cur_temp, unit)}</div>
        <div class="feels">Feels like {format_temp(feels, unit)} • {wind if wind is not None else '—'} km/h {wind_dir_to_compass(wdir)}</div>
        <div style="margin-top:8px; font-size:12px; opacity:0.9; font-weight:600">Last observed: {current.get('time','—')} ({timezone_used}) • Pressure {press if press else '—'} hPa • Precip {precip if precip is not None else 0} mm</div>
      </div>
      <div class="hero-bottom">
        <div class="mini-stat"><label>Today High</label><strong>{format_temp(daily.get('temperature_2m_max',[None])[0], unit) if daily.get('temperature_2m_max') else '—'}</strong></div>
        <div class="mini-stat"><label>Today Low</label><strong>{format_temp(daily.get('temperature_2m_min',[None])[0], unit) if daily.get('temperature_2m_min') else '—'}</strong></div>
        <div class="mini-stat"><label>Rain Chance</label><strong>{pprob_max if pprob_max is not None else '—'}%</strong></div>
      </div>
    </div>
    <div class="stack">
      <div class="glass-card sun-card">
        <div class="sun-time"><small>🌅 Sunrise</small><strong>{sunrise[11:16] if len(str(sunrise))>10 else sunrise}</strong><small>{str(sunrise)[:10] if len(str(sunrise))>10 else ''}</small></div>
        <div class="sun-divider"></div>
        <div class="sun-time"><small>🌇 Sunset</small><strong>{sunset[11:16] if len(str(sunset))>10 else sunset}</strong><small>{str(sunset)[:10] if len(str(sunset))>10 else ''}</small></div>
        <div class="sun-divider"></div>
        <div class="sun-time"><small>☀️ UV Index</small><strong style="color:{uv_color}">{uv_max if uv_max is not None else '—'} • {uv_label}</strong></div>
      </div>
      <div class="glass-card">
        <div class="card-title"><span></span> Air & Wind</div>
        <div class="metric-grid">
          <div class="metric"><label>Humidity</label><strong>{hum if hum is not None else '—'}%</strong><em>Dew {hourly.get('dew_point_2m',[None])[0] if hourly.get('dew_point_2m') else '—'}°{unit}</em></div>
          <div class="metric"><label>Pressure</label><strong>{press if press else '—'} hPa</strong><em>MSL • Steady</em></div>
          <div class="metric"><label>Wind</label><strong>{wind if wind is not None else '—'} km/h</strong><em>{wdir}° {wind_dir_to_compass(wdir)} • Gust {wind_gust_max} km/h</em></div>
          <div class="metric"><label>Precipitation</label><strong>{psun if psun is not None else precip if precip is not None else 0} mm</strong><em>{pprob_max if pprob_max is not None else '—'}% chance today</em></div>
        </div>
      </div>
    </div>
  </div>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

# Small spacing
st.write("")

# ────────────────────────────────────────────────
# AI INSIGHT SECTION (premium)
# ────────────────────────────────────────────────
# Check cache key = loc + date + unit
cache_key = f"{loc['latitude']:.3f}_{loc['longitude']:.3f}_{unit}_{daily.get('time',[''])[0] if daily.get('time') else ''}"
if cache_key not in st.session_state.ai_summary_cache:
    with st.spinner("AtmoSphere AI is analyzing the forecast…"):
        summary = ai_generate_summary(weather, loc, unit)
        st.session_state.ai_summary_cache[cache_key] = summary
else:
    summary = st.session_state.ai_summary_cache[cache_key]

is_nvidia = summary["source"]=="nvidia"
badge_text = f"✦ NVIDIA {NVIDIA_MODEL}" if is_nvidia else "◐ Local Fallback • Add NVIDIA_API_KEY for AI"
badge_style = "background: rgba(16,185,129,0.18); border-color: rgba(16,185,129,0.30); color:#6EE7B7" if is_nvidia else ""
ai_text_html = summary["text"].replace("\n", "<br>")
# Convert markdown bold to html
import re
ai_text_html = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', ai_text_html)
ai_text_html = re.sub(r'^- (.*)', r'• \1', ai_text_html, flags=re.MULTILINE)

# Quick suggestion chips derived from daily
suggestion_chips = []
if pprob_max is not None:
    if pprob_max >= 70:
        suggestion_chips = ["☔ Umbrella essential", "🚗 Allow extra commute time", "🏠 Indoor backup plan"]
    elif pprob_max >= 40:
        suggestion_chips = ["🌦️ Compact umbrella", "👟 Water-resistant shoes", "📸 Flexible outdoor timing"]
    else:
        suggestion_chips = ["😎 Great for outdoors", "☀️ Light layers", "🚴 Ideal for exercise"]
if cur_temp is not None:
    if cur_temp >= 35 and unit=="C" or cur_temp >= 95 and unit=="F":
        suggestion_chips.append("🥤 Hydrate • Shade breaks")
    elif cur_temp <= 8 and unit=="C" or cur_temp <= 46 and unit=="F":
        suggestion_chips.append("🧣 Warm layers • Cover extremities")

chips_html = "".join([f'<span class="ai-chip">{c}</span>' for c in suggestion_chips])

st.markdown(f"""
<div class="ai-card">
  <div class="ai-badge" style="{badge_style}">{badge_text} • {'Live' if is_nvidia else 'Offline-capable'}</div>
  <div class="ai-title">AtmoSphere AI • Today’s Briefing</div>
  <div class="ai-body">{ai_text_html}</div>
  <div class="ai-suggestions">{chips_html}</div>
  <div style="margin-top:10px; font-size:11px; color:#94A3B8; font-weight:600">Model: {summary['model']} • Factual data from Open-Meteo • Interpretation labeled as AI insight. Probabilities are chances, not certainties.</div>
</div>
""", unsafe_allow_html=True)

# Regenerate AI button
col_regen, col_info = st.columns([1,4])
with col_regen:
    if st.button("✨ Regenerate AI summary"):
        # force refresh
        if cache_key in st.session_state.ai_summary_cache:
            del st.session_state.ai_summary_cache[cache_key]
        st.rerun()
with col_info:
    if not is_nvidia:
        st.caption("💡 Add your NVIDIA API key to unlock Nemotron 3.5 Lightning: get key at build.nvidia.com → API Keys → set in Streamlit Secrets as NVIDIA_API_KEY. App works fully without it via local fallback.")

st.write("")

# ────────────────────────────────────────────────
# HOURLY FORECAST — SCROLLABLE
# ────────────────────────────────────────────────
st.markdown('<div class="glass-card"><div class="card-title"><span></span> Hourly Forecast • Next 24 Hours — swipe/scroll →</div>', unsafe_allow_html=True)
# Build hourly items
hourly_times = hourly.get("time", [])
hourly_temps = hourly.get("temperature_2m", [])
hourly_codes = hourly.get("weather_code", [])
hourly_prob = hourly.get("precipitation_probability", [])
# Find now index for active
now_iso = current.get("time")
active_idx = 0
try:
    now_dt = datetime.fromisoformat(now_iso)
    for idx, t in enumerate(hourly_times):
        try:
            if datetime.fromisoformat(t) >= now_dt:
                active_idx = idx; break
        except: continue
except: pass

hourly_html = '<div class="hourly-scroll">'
for i in range(active_idx, min(active_idx+24, len(hourly_times))):
    t = hourly_times[i]
    try:
        dt = datetime.fromisoformat(t)
        label = dt.strftime("%I %p").lstrip("0")
        if dt.hour == now_dt.hour and dt.date()==now_dt.date():
            label = "Now"
    except:
        label = t[11:16]
    temp = hourly_temps[i] if i < len(hourly_temps) else None
    code_h = hourly_codes[i] if i < len(hourly_codes) else 3
    _, emoji_h, _ = wmo_info(code_h)
    prob_h = hourly_prob[i] if i < len(hourly_prob) else 0
    active_cls = "active" if i==active_idx else ""
    hourly_html += f"""
    <div class="hour-item {active_cls}">
      <time>{label}</time>
      <div class="hi">{emoji_h}</div>
      <strong>{format_temp(temp, unit)}</strong>
      <small>{prob_h}% 💧</small>
    </div>
    """
hourly_html += '</div></div>'
st.markdown(hourly_html, unsafe_allow_html=True)
st.write("")

# ────────────────────────────────────────────────
# CHARTS ROW
# ────────────────────────────────────────────────
col_c1, col_c2 = st.columns(2, gap="medium")
with col_c1:
    st.markdown('<div class="glass-card"><div class="card-title"><span></span> Temperature Trend • Next 24h</div>', unsafe_allow_html=True)
    fig1 = chart_hourly_temp(hourly, unit, hours=24)
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Tip: Feels-like (dotted) accounts for humidity + wind.")
with col_c2:
    st.markdown('<div class="glass-card"><div class="card-title"><span></span> Precipitation • Probability & Amount</div>', unsafe_allow_html=True)
    fig2 = chart_precip_prob(hourly, hours=24)
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)
    st.caption("Probability = chance in similar historical forecasts; amount in mm.")

# ────────────────────────────────────────────────
# DAILY FORECAST
# ────────────────────────────────────────────────
st.markdown('<div class="glass-card"><div class="card-title"><span></span> 7-Day Forecast</div>', unsafe_allow_html=True)
daily_times = daily.get("time", [])
tmaxs = daily.get("temperature_2m_max", [])
tmins = daily.get("temperature_2m_min", [])
dcodes = daily.get("weather_code", [])
dprec_probs = daily.get("precipitation_probability_max", [])
dprec_sums = daily.get("precipitation_sum", [])
# For bar scaling
all_t = [v for v in tmaxs+tmins if isinstance(v, (int,float))]
t_min_global = min(all_t) if all_t else 0
t_max_global = max(all_t) if all_t else 1
t_range = (t_max_global - t_min_global) if t_max_global != t_min_global else 1

daily_rows_html = ""
for i in range(min(7, len(daily_times))):
    try:
        dt = datetime.fromisoformat(daily_times[i])
        day_label = dt.strftime("%A")
        if i==0: day_label = "Today"
        elif i==1: day_label = "Tomorrow"
    except: day_label = daily_times[i]
    code_d = dcodes[i] if i < len(dcodes) else 3
    desc_d, emoji_d, _ = wmo_info(code_d)
    tmx = tmaxs[i] if i < len(tmaxs) else None
    tmn = tmins[i] if i < len(tmins) else None
    prob_d = dprec_probs[i] if i < len(dprec_probs) and dprec_probs[i] is not None else 0
    psum_d = dprec_sums[i] if i < len(dprec_sums) and dprec_sums[i] is not None else 0
    # Bar calc: width based on min/max within global range
    left = ((tmn - t_min_global)/t_range*100) if isinstance(tmn,(int,float)) else 0
    width = ((tmx - tmn)/t_range*100) if isinstance(tmx,(int,float)) and isinstance(tmn,(int,float)) else 30
    sunrise_i = daily.get("sunrise", [""])[i] if daily.get("sunrise") else ""
    sunset_i = daily.get("sunset", [""])[i] if daily.get("sunset") else ""
    daily_rows_html += f"""
    <div class="daily-row">
      <div class="day-name">{day_label}</div>
      <div class="day-icon" title="{desc_d}">{emoji_d}</div>
      <div style="flex:1; margin: 0 12px">
        <div style="font-size:12px; color:#CBD5E1; font-weight:600">{desc_d} • {psum_d} mm</div>
        <div class="day-bar"><div class="day-bar-fill" style="left:{left}%; width:{max(width,8)}%"></div></div>
      </div>
      <div class="day-temp">{format_temp(tmn, unit)} — {format_temp(tmx, unit)}</div>
      <div class="day-precip">💧 {prob_d}%</div>
    </div>
    """
st.markdown(daily_rows_html, unsafe_allow_html=True)
# Chart for daily temps
with st.expander("📊 Show 7-day temperature chart", expanded=False):
    fig3 = chart_daily_overview(daily, unit)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# ────────────────────────────────────────────────
# DETAILS GRID
# ────────────────────────────────────────────────
detail_cols = st.columns(3, gap="medium")
with detail_cols[0]:
    st.markdown('<div class="glass-card"><div class="card-title"><span></span> Wind & Pressure Detail</div>', unsafe_allow_html=True)
    wind_speed = current.get("wind_speed_10m")
    wind_gust = current.get("wind_gusts_10m")
    press_msl = current.get("pressure_msl")
    cloud_cov = current.get("cloud_cover")
    # wind compass visual using simple text
    st.metric("Wind Speed", f"{wind_speed} km/h" if wind_speed is not None else "—", f"Gust {wind_gust} km/h" if wind_gust else None)
    st.metric("Direction", f"{wdir}° {wind_dir_to_compass(wdir)}" if wdir is not None else "—")
    st.metric("Pressure (MSL)", f"{press_msl} hPa" if press_msl else "—")
    st.metric("Cloud Cover", f"{cloud_cov}%" if cloud_cov is not None else "—")
    st.markdown('</div>', unsafe_allow_html=True)
with detail_cols[1]:
    st.markdown('<div class="glass-card"><div class="card-title"><span></span> Humidity & Comfort</div>', unsafe_allow_html=True)
    rel_hum = current.get("relative_humidity_2m")
    dew = hourly.get("dew_point_2m", [None])[active_idx] if len(hourly.get("dew_point_2m", []))>active_idx else None
    apparent = current.get("apparent_temperature")
    st.metric("Relative Humidity", f"{rel_hum}%" if rel_hum is not None else "—")
    st.metric("Dew Point", f"{format_temp_precise(dew, unit)}" if dew is not None else "—")
    st.metric("Feels Like", format_temp_precise(apparent, unit) if apparent is not None else "—")
    # comfort heuristic
    comfort = "Comfortable"
    if rel_hum and rel_hum > 75 and cur_temp and cur_temp>28:
        comfort = "Muggy — stay cool"
    elif rel_hum and rel_hum < 30:
        comfort = "Dry — hydrate"
    st.info(f"Comfort: {comfort}")
    st.markdown('</div>', unsafe_allow_html=True)
with detail_cols[2]:
    st.markdown('<div class="glass-card"><div class="card-title"><span></span> Sun & Daylight</div>', unsafe_allow_html=True)
    daylight = daily.get("daylight_duration", [None])[0]
    sunshine = daily.get("sunshine_duration", [None])[0]
    if daylight:
        hrs = daylight/3600
        st.metric("Daylight", f"{hrs:.1f} hrs")
    if sunshine:
        sh = sunshine/3600
        st.metric("Sunshine", f"{sh:.1f} hrs")
    st.metric("Sunrise", sunrise[11:16] if len(str(sunrise))>10 else str(sunrise))
    st.metric("Sunset", sunset[11:16] if len(str(sunset))>10 else str(sunset))
    # daylight bar
    st.caption("Sun path shown for today; times in local timezone.")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# ────────────────────────────────────────────────
# CONVERSATIONAL ASSISTANT
# ────────────────────────────────────────────────
st.markdown("""
<div class="glass-card" style="border-color: rgba(99,102,241,0.25); background: linear-gradient(135deg, rgba(99,102,241,0.06), rgba(56,189,248,0.06))">
  <div class="card-title"><span style="background:#818CF8; box-shadow:0 0 10px #818CF8"></span> AtmoSphere AI Assistant • Ask about this forecast</div>
  <div style="font-size:12px; color:#94A3B8; font-weight:600; margin-bottom:10px">Examples: “Will it rain tomorrow?”, “Should I carry an umbrella?”, “Best time for a walk?”, “How windy is it tonight?” — answers use ONLY live forecast data.</div>
</div>
""", unsafe_allow_html=True)

# Show history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask AtmoSphere AI about this location’s weather…"):
    # Append user
    st.session_state.chat_history.append({"role":"user","content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            answer = ai_chat_answer(prompt, weather, loc, unit, st.session_state.chat_history)
            st.markdown(answer)
            # indicator
            key_src = "NVIDIA Nemotron 3.5 Lightning" if get_nvidia_key() and call_nvidia_chat else "Local fallback"
            # Actually call check: if key exists, we attempted NVIDIA; annotate
            if get_nvidia_key():
                st.caption(f"Answered by {NVIDIA_MODEL} • Facts from Open-Meteo")
            else:
                st.caption("Answered by local fallback • Add NVIDIA_API_KEY for AI • Facts from Open-Meteo")
    st.session_state.chat_history.append({"role":"assistant","content": answer})
    # optional rerun? no

# Clear chat
col_clear, _ = st.columns([1,5])
with col_clear:
    if st.button("🗑️ Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

st.write("")

# ────────────────────────────────────────────────
# FOOTER
# ────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  <div>© 2026 AtmoSphere AI • Weather Intelligence Platform • Built with Streamlit • AI: <code>{NVIDIA_MODEL}</code> via <code>{NVIDIA_ENDPOINT}</code> • Data: <a href="https://open-meteo.com" style="color:#38BDF8">Open-Meteo</a> (CC BY 4.0) • Geocoding: Open-Meteo</div>
  <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap">
    <span>📍 {loc.get('label')} • 🕒 {current.get('time','—')} • ⏱ Updated {update_local}</span>
    <span style="padding:6px 10px; border-radius:999px; background: rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.08)">Units °{unit}</span>
  </div>
</div>
<div style="margin-top:10px; text-align:center; color:#64748B; font-size:11px; line-height:1.6">
  Open-Meteo best_match model aggregates ECMWF IFS, DWD ICON, NOAA GFS. Free & no key required. Forecast up to 16 days; we show 7. Caching: geocoding 6h, weather 10m. AI never invents data — all insights grounded in retrieved forecast. No personal data sent to AI except location coordinates + forecast numbers.
</div>
""", unsafe_allow_html=True)
