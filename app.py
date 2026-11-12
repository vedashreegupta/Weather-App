"""
Smart Weather & Travel Advisor - Glassmorphic Mobile & Desktop Web App
Powered by Open-Meteo (Free, No API Key Required)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from weather import (
    NoInternetError,
    c_to_f,
    detect_my_location,
    fetch_city_weather,
    fetch_multiple_cities,
    fetch_weather_by_coords,
    get_umbrella_and_alerts,
    reverse_geocode,
)


def fmt_temp(temp_c, unit="C"):
    """Format Celsius value in selected unit (°C or °F)."""
    val = c_to_f(temp_c) if unit == "F" else round(temp_c, 1)
    return f"{val}°{unit}"


def convert_val(temp_c, unit="C"):
    return c_to_f(temp_c) if unit == "F" else temp_c


@st.cache_data(ttl=600, show_spinner=False)
def cached_city_weather(city_key):
    return fetch_city_weather(city_key)


@st.cache_data(ttl=600, show_spinner=False)
def cached_coords_weather(lat_r, lon_r):
    city, country = reverse_geocode(lat_r, lon_r)
    return fetch_weather_by_coords(city, country, lat_r, lon_r)


@st.cache_data(ttl=600, show_spinner=False)
def cached_compare(cities_tuple):
    return fetch_multiple_cities(list(cities_tuple))


@st.cache_data(ttl=600, show_spinner=False)
def cached_ip_location():
    return detect_my_location()

st.set_page_config(
    page_title="SkyPulse Weather",
    page_icon="🌤️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def get_theme_gradient(art_key="sun"):
    """Dynamic atmospheric background gradient matching current weather."""
    themes = {
        "sun": "radial-gradient(circle at 80% 10%, rgba(251, 191, 36, 0.22), transparent 45%), linear-gradient(160deg, #0b132b 0%, #1c2541 50%, #0f172a 100%)",
        "partly": "radial-gradient(circle at 80% 10%, rgba(56, 189, 248, 0.22), transparent 45%), linear-gradient(160deg, #0f172a 0%, #1e293b 55%, #0b1120 100%)",
        "cloud": "radial-gradient(circle at 70% 10%, rgba(148, 163, 184, 0.20), transparent 50%), linear-gradient(160deg, #111827 0%, #1f2937 55%, #0f172a 100%)",
        "rain": "radial-gradient(circle at 75% 15%, rgba(14, 165, 233, 0.25), transparent 50%), linear-gradient(160deg, #090d16 0%, #172554 55%, #0f172a 100%)",
        "storm": "radial-gradient(circle at 75% 15%, rgba(168, 85, 247, 0.25), transparent 50%), linear-gradient(160deg, #09090b 0%, #1e1b4b 55%, #0f172a 100%)",
        "fog": "radial-gradient(circle at 50% 10%, rgba(203, 213, 225, 0.18), transparent 55%), linear-gradient(160deg, #1e293b 0%, #334155 55%, #0f172a 100%)",
        "snow": "radial-gradient(circle at 80% 10%, rgba(186, 230, 253, 0.25), transparent 50%), linear-gradient(160deg, #0c4a6e 0%, #1e293b 55%, #0f172a 100%)",
    }
    return themes.get(art_key, themes["partly"])


def inject_css(bg_gradient):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

#MainMenu, header, footer {{ visibility: hidden; height: 0; }}

html, body, [class*="css"] {{
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #f8fafc;
}}

.stApp {{
  background: {bg_gradient};
  background-attachment: fixed;
}}

.block-container {{
  padding: 1.2rem 1rem 3rem 1rem !important;
  max-width: 680px !important;
}}

/* App Top Bar */
.app-brand {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}}
.brand-title {{
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: linear-gradient(90deg, #ffffff 0%, #93c5fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.brand-badge {{
  font-size: 0.72rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.14);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #7dd3fc;
}}

/* Inputs & Buttons */
.stTextInput input {{
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  border-radius: 14px !important;
  color: #ffffff !important;
  padding: 10px 14px !important;
  font-size: 0.95rem !important;
}}
.stTextInput input:focus {{
  border-color: #60a5fa !important;
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.25) !important;
}}
.stButton > button {{
  background: rgba(255, 255, 255, 0.08) !important;
  color: #f1f5f9 !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 14px !important;
  min-height: 42px !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  transition: all 0.2s ease !important;
}}
.stButton > button:hover {{
  background: rgba(59, 130, 246, 0.28) !important;
  border-color: rgba(96, 165, 250, 0.55) !important;
  transform: translateY(-1px);
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  gap: 8px;
  background: rgba(255, 255, 255, 0.05);
  padding: 5px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}}
.stTabs [data-baseweb="tab"] {{
  border-radius: 12px;
  padding: 8px 16px;
  color: #94a3b8;
  font-weight: 600;
  flex: 1;
}}
.stTabs [aria-selected="true"] {{
  background: rgba(59, 130, 246, 0.28) !important;
  color: #ffffff !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}

/* Hero Weather Card */
.hero-glass {{
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.11) 0%, rgba(255, 255, 255, 0.04) 100%);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 24px;
  padding: 24px;
  margin: 14px 0;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.32);
}}
.hero-top {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}}
.city-name {{
  font-size: 1.45rem;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.02em;
}}
.city-sub {{
  font-size: 0.92rem;
  color: #cbd5e1;
  margin-top: 3px;
}}
.hero-icon {{
  font-size: 3.8rem;
  line-height: 1;
  filter: drop-shadow(0 6px 16px rgba(255, 255, 255, 0.22));
}}
.hero-temp {{
  font-size: 4rem;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.04em;
  margin: 14px 0 6px 0;
  background: linear-gradient(180deg, #ffffff 25%, #bae6fd 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}
.hero-feels {{
  font-size: 0.9rem;
  color: #94a3b8;
  font-weight: 500;
}}

/* 2x3 Glass Metric Tiles */
.tile-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin: 12px 0;
}}
@media (min-width: 540px) {{
  .tile-grid {{ grid-template-columns: repeat(3, 1fr); }}
}}
.stat-tile {{
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 18px;
  padding: 14px;
}}
.stat-label {{
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  font-weight: 600;
}}
.stat-val {{
  font-size: 1.25rem;
  font-weight: 700;
  color: #f8fafc;
  margin-top: 4px;
}}
.mini-bar-bg {{
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 99px;
  margin-top: 8px;
  overflow: hidden;
}}
.mini-bar-fill {{
  height: 100%;
  border-radius: 99px;
}}

/* Advisory & Alert Banners */
.advice-banner {{
  border-radius: 16px;
  padding: 13px 16px;
  margin: 8px 0;
  font-size: 0.94rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  backdrop-filter: blur(10px);
}}
.advice-ok {{
  background: rgba(34, 197, 94, 0.14);
  border: 1px solid rgba(34, 197, 94, 0.35);
  color: #bbf7d0;
}}
.advice-warn {{
  background: rgba(56, 189, 248, 0.16);
  border: 1px solid rgba(56, 189, 248, 0.4);
  color: #bae6fd;
}}
.advice-alert {{
  background: rgba(239, 68, 68, 0.16);
  border: 1px solid rgba(239, 68, 68, 0.42);
  color: #fecaca;
}}

/* Hourly Horizontal Scroll Strip */
.section-hdr {{
  font-size: 0.95rem;
  font-weight: 700;
  color: #e2e8f0;
  margin: 18px 0 10px 0;
  letter-spacing: 0.01em;
}}
.hour-strip {{
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 6px;
}}
.hour-pill {{
  flex: 1;
  min-width: 82px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 18px;
  padding: 12px 8px;
  text-align: center;
}}
.hour-time {{ font-size: 0.78rem; color: #94a3b8; font-weight: 600; }}
.hour-icon {{ font-size: 1.55rem; margin: 6px 0; }}
.hour-temp {{ font-size: 1.05rem; font-weight: 700; color: #ffffff; }}
.hour-rain {{ font-size: 0.75rem; color: #38bdf8; font-weight: 600; margin-top: 3px; }}

/* Comparison City Cards */
.cmp-card {{
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 14px 16px;
  margin-bottom: 10px;
}}
.cmp-top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
}}
.cmp-meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
  font-size: 0.84rem;
  color: #cbd5e1;
}}
.tag-pill {{
  padding: 3px 9px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  font-size: 0.78rem;
  font-weight: 600;
}}
</style>
""", unsafe_allow_html=True)


def aqi_info(aqi):
    if aqi is None:
        return "N/A", "#94a3b8"
    if aqi <= 50:
        return f"{aqi} • Good", "#22c55e"
    if aqi <= 100:
        return f"{aqi} • Moderate", "#eab308"
    if aqi <= 150:
        return f"{aqi} • Sensitive", "#f97316"
    if aqi <= 200:
        return f"{aqi} • Unhealthy", "#ef4444"
    return f"{aqi} • Hazardous", "#a855f7"


def uv_label(uv):
    if uv is None:
        return "N/A"
    if uv < 3:
        return f"{uv} • Low"
    if uv < 6:
        return f"{uv} • Moderate"
    if uv < 8:
        return f"{uv} • High"
    return f"{uv} • Very High"


def render_single_city(w, unit="C"):
    if w.get("from_cache"):
        st.markdown(
            f'<div class="advice-banner advice-warn">📶 Offline mode — cached at {w.get("cached_at", "")}</div>',
            unsafe_allow_html=True,
        )

    aqi_txt, aqi_col = aqi_info(w.get("aqi"))
    uv_txt = uv_label(w.get("uv"))

    # Hero Glass Card
    st.markdown(f"""
<div class="hero-glass">
<div class="hero-top">
<div>
<div class="city-name">📍 {w['name']}, {w['country']}</div>
<div class="city-sub">{w['condition']}</div>
</div>
<div class="hero-icon">{w['icon']}</div>
</div>
<div class="hero-temp">{fmt_temp(w['temp'], unit)}</div>
<div class="hero-feels">Feels like {fmt_temp(w['feels_like'], unit)}  •  🌅 {w['sunrise']}  •  🌇 {w['sunset']}</div>
</div>
""", unsafe_allow_html=True)

    # Umbrella & Alerts
    umbrella, alerts = get_umbrella_and_alerts(w, color=False)
    cls = "advice-warn" if ("Carry an umbrella" in umbrella or "small umbrella" in umbrella) else "advice-ok"
    st.markdown(f'<div class="advice-banner {cls}">{umbrella}</div>', unsafe_allow_html=True)
    for alert in alerts:
        st.markdown(f'<div class="advice-banner advice-alert">🚨 {alert}</div>', unsafe_allow_html=True)

    # 2x3 Metric Tiles
    st.markdown(f"""
<div class="tile-grid">
<div class="stat-tile">
<div class="stat-label">💧 Humidity</div>
<div class="stat-val">{w['humidity']}%</div>
<div class="mini-bar-bg"><div class="mini-bar-fill" style="width:{min(100, w['humidity'])}%; background:#38bdf8;"></div></div>
</div>
<div class="stat-tile">
<div class="stat-label">🌧️ Rain Chance</div>
<div class="stat-val">{w['rain_prob']}%</div>
<div class="mini-bar-bg"><div class="mini-bar-fill" style="width:{min(100, w['rain_prob'])}%; background:#60a5fa;"></div></div>
</div>
<div class="stat-tile">
<div class="stat-label">💨 Wind Speed</div>
<div class="stat-val">{w['wind']} <span style="font-size:0.85rem; color:#94a3b8;">km/h</span></div>
</div>
<div class="stat-tile">
<div class="stat-label">😷 Air Quality</div>
<div class="stat-val" style="font-size:1.05rem; color:{aqi_col};">{aqi_txt}</div>
</div>
<div class="stat-tile">
<div class="stat-label">☀️ UV Index</div>
<div class="stat-val" style="font-size:1.05rem;">{uv_txt}</div>
</div>
<div class="stat-tile">
<div class="stat-label">🌅 Sun Cycle</div>
<div class="stat-val" style="font-size:0.9rem; line-height:1.4;">↑ {w['sunrise']}<br/>↓ {w['sunset']}</div>
</div>
</div>
""", unsafe_allow_html=True)

    # Hourly Strip + Sleek Chart
    hourly = w.get("hourly", [])
    if hourly:
        st.markdown('<div class="section-hdr">🕒 Upcoming Hours</div>', unsafe_allow_html=True)
        pills = "".join(
            f'<div class="hour-pill"><div class="hour-time">{h["time"]}</div>'
            f'<div class="hour-icon">{h["icon"]}</div>'
            f'<div class="hour-temp">{round(convert_val(h["temp"], unit))}°</div>'
            f'<div class="hour-rain">💧 {h["rain"]}%</div></div>'
            for h in hourly
        )
        st.markdown(f'<div class="hour-strip">{pills}</div>', unsafe_allow_html=True)

        df_hr = pd.DataFrame(hourly)
        df_hr["display_temp"] = [convert_val(t, unit) for t in df_hr["temp"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_hr["time"],
            y=df_hr["display_temp"],
            mode="lines+markers",
            name=f"Temp (°{unit})",
            line=dict(color="#fbbf24", width=3, shape="spline"),
            marker=dict(size=7, color="#fde68a"),
            fill="tozeroy",
            fillcolor="rgba(251, 191, 36, 0.12)",
        ))
        fig.add_trace(go.Bar(
            x=df_hr["time"],
            y=df_hr["rain"],
            name="Rain %",
            marker_color="rgba(56, 189, 248, 0.35)",
            yaxis="y2",
        ))
        fig.update_layout(
            template="plotly_dark",
            height=220,
            margin=dict(l=8, r=8, t=24, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=1.18, x=0),
            xaxis=dict(showgrid=False),
            yaxis=dict(title=f"°{unit}", showgrid=True, gridcolor="rgba(255,255,255,0.07)"),
            yaxis2=dict(title="Rain %", overlaying="y", side="right", range=[0, 100], showgrid=False),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    # 5-Day Forecast Strip
    daily = w.get("daily", [])
    if daily:
        st.markdown('<div class="section-hdr">📅 5-Day Forecast</div>', unsafe_allow_html=True)
        day_pills = "".join(
            f'<div class="hour-pill" style="min-width:105px;">'
            f'<div class="hour-time">{d["day"]} • {d["date"]}</div>'
            f'<div class="hour-icon">{d["icon"]}</div>'
            f'<div class="hour-temp">{round(convert_val(d["temp_max"], unit))}° <span style="font-size:0.82rem; color:#94a3b8; font-weight:500;">/ {round(convert_val(d["temp_min"], unit))}°</span></div>'
            f'<div class="hour-rain">💧 {d["rain_prob"]}%</div></div>'
            for d in daily
        )
        st.markdown(f'<div class="hour-strip">{day_pills}</div>', unsafe_allow_html=True)


# --- Session State ---
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Pune"
if "bg_art" not in st.session_state:
    st.session_state.bg_art = "sun"
if "temp_unit" not in st.session_state:
    st.session_state.temp_unit = "C"
if "recent_cities" not in st.session_state:
    st.session_state.recent_cities = ["Pune", "Mumbai", "Delhi", "London", "Tokyo"]
if "gps_pending" not in st.session_state:
    st.session_state.gps_pending = False
if "gps_coords" not in st.session_state:
    st.session_state.gps_coords = None
if "gps_source" not in st.session_state:
    st.session_state.gps_source = None

inject_css(get_theme_gradient(st.session_state.bg_art))

hdr_left, hdr_unit = st.columns([3.2, 0.85])
with hdr_left:
    st.markdown("""
<div class="app-brand" style="margin-bottom:0;">
<div class="brand-title">🌤️ SkyPulse Weather</div>
</div>
""", unsafe_allow_html=True)
with hdr_unit:
    next_unit = "F" if st.session_state.temp_unit == "C" else "C"
    if st.button(f"°{st.session_state.temp_unit} ⇄ °{next_unit}", width="stretch"):
        st.session_state.temp_unit = next_unit
        st.rerun()

tab_single, tab_compare = st.tabs(["📍 Forecast", "🌍 Compare (Max 5)"])

with tab_single:
    col_in, col_gps, col_ref = st.columns([2.05, 1.0, 0.42])
    with col_in:
        city_input = st.text_input(
            "City",
            value=st.session_state.selected_city,
            placeholder="Search any city (e.g. Pune, Tokyo)...",
            label_visibility="collapsed",
        )
    with col_gps:
        gps_clicked = st.button("📍 My Location", width="stretch")
    with col_ref:
        refresh_clicked = st.button("🔄", help="Refresh live weather (clear 10m cache)", width="stretch")

    chips = st.session_state.recent_cities[:5]
    p_cols = st.columns(len(chips))
    for i, name in enumerate(chips):
        if p_cols[i].button(name, key=f"chip_{i}_{name}", width="stretch"):
            st.session_state.selected_city = name
            st.session_state.gps_coords = None
            st.session_state.gps_source = None
            st.query_params.clear()
            st.rerun()

    if refresh_clicked:
        st.cache_data.clear()
        st.rerun()

    if gps_clicked:
        st.session_state.gps_pending = True
        st.query_params.clear()
        st.rerun()

    # Check if user manually typed a new city name
    typed_city = city_input.strip()
    if typed_city and typed_city != st.session_state.selected_city:
        st.session_state.selected_city = typed_city
        st.session_state.gps_coords = None
        st.session_state.gps_source = None
        st.query_params.clear()

    # Handle incoming browser GPS query params
    if "gps_lat" in st.query_params and "gps_lon" in st.query_params:
        try:
            g_lat = round(float(st.query_params["gps_lat"]), 4)
            g_lon = round(float(st.query_params["gps_lon"]), 4)
            st.session_state.gps_coords = (g_lat, g_lon)
            st.session_state.gps_source = "📡 Exact Browser GPS"
            st.query_params.clear()
        except ValueError:
            st.query_params.clear()
    elif "gps_fallback" in st.query_params:
        st.query_params.clear()
        loc = cached_ip_location()
        if loc:
            st.session_state.gps_coords = (round(loc["lat"], 4), round(loc["lon"], 4))
            st.session_state.gps_source = "🌐 Auto-Detected (IP)"
        else:
            st.markdown('<div class="advice-banner advice-alert">❌ Could not auto-detect location. Enter a city manually.</div>', unsafe_allow_html=True)

    # Trigger browser Geolocation popup once when requested
    if st.session_state.gps_pending:
        st.session_state.gps_pending = False
        st.markdown('<div class="advice-banner advice-warn">📡 Requesting browser GPS permission...</div>', unsafe_allow_html=True)
        components.html(
            """
            <script>
            (function() {
              const targetWin = (window.parent && window.parent !== window) ? window.parent : window;
              const geo = (targetWin.navigator && targetWin.navigator.geolocation) || navigator.geolocation;
              if (!geo) {
                targetWin.location.search = '?gps_fallback=1';
                return;
              }
              geo.getCurrentPosition(
                function(pos) {
                  const lat = pos.coords.latitude.toFixed(4);
                  const lon = pos.coords.longitude.toFixed(4);
                  targetWin.location.search = '?gps_lat=' + lat + '&gps_lon=' + lon;
                },
                function() {
                  targetWin.location.search = '?gps_fallback=1';
                },
                { enableHighAccuracy: false, timeout: 6000, maximumAge: 300000 }
              );
            })();
            </script>
            """,
            height=0,
        )

    try:
        weather_data = None
        if st.session_state.gps_coords:
            g_lat, g_lon = st.session_state.gps_coords
            with st.spinner("Loading GPS weather..."):
                weather_data = cached_coords_weather(g_lat, g_lon)
            if weather_data:
                st.session_state.selected_city = weather_data["name"]
                if st.session_state.gps_source:
                    st.caption(st.session_state.gps_source)
        elif st.session_state.selected_city:
            with st.spinner(f"Loading {st.session_state.selected_city}..."):
                weather_data = cached_city_weather(st.session_state.selected_city)
            if weather_data is None:
                st.markdown(f'<div class="advice-banner advice-alert">❌ City "{st.session_state.selected_city}" not found. Check spelling.</div>', unsafe_allow_html=True)

        if weather_data:
            city_found = weather_data["name"]
            if city_found not in st.session_state.recent_cities:
                st.session_state.recent_cities = [city_found] + st.session_state.recent_cities[:4]
            new_art = weather_data.get("art_key", "partly")
            if new_art != st.session_state.bg_art:
                st.session_state.bg_art = new_art
                st.markdown(f"<style>.stApp {{ background: {get_theme_gradient(new_art)}; background-attachment: fixed; }}</style>", unsafe_allow_html=True)
            render_single_city(weather_data, st.session_state.temp_unit)

    except NoInternetError:
        st.markdown('<div class="advice-banner advice-alert">❌ No internet connection and no offline cache found.</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div class="advice-banner advice-alert">❌ Error: {e}</div>', unsafe_allow_html=True)

with tab_compare:
    compare_raw = st.text_input(
        "Compare cities",
        value="Pune, Mumbai, Delhi, London, Tokyo",
        placeholder="Up to 5 cities separated by commas",
        label_visibility="collapsed",
    )
    if st.button("✨ Compare Weather", width="stretch"):
        city_list = [c.strip() for c in compare_raw.split(",") if c.strip()]
        if not city_list:
            st.warning("Enter at least one city.")
        else:
            if len(city_list) > 5:
                st.info("Showing first 5 cities (maximum allowed is 5).")
                city_list = city_list[:5]

            results = []
            try:
                with st.spinner("Fetching all cities in parallel..."):
                    results, missing = cached_compare(tuple(city_list))
                for m in missing:
                    st.warning(f"⚠️ '{m}' not found.")
            except NoInternetError:
                st.markdown('<div class="advice-banner advice-alert">❌ No internet connection while comparing cities.</div>', unsafe_allow_html=True)

            if results:
                warmest = max(results, key=lambda x: x["temp"])
                coolest = min(results, key=lambda x: x["temp"])
                humidest = max(results, key=lambda x: x["humidity"])

                unit = st.session_state.temp_unit
                st.markdown(f"""
<div class="tile-grid">
<div class="stat-tile">
<div class="stat-label">🔥 Warmest</div>
<div class="stat-val" style="color:#fbbf24;">{warmest['name']}</div>
<div style="font-size:0.85rem; color:#cbd5e1;">{fmt_temp(warmest['temp'], unit)}</div>
</div>
<div class="stat-tile">
<div class="stat-label">❄️ Coolest</div>
<div class="stat-val" style="color:#38bdf8;">{coolest['name']}</div>
<div style="font-size:0.85rem; color:#cbd5e1;">{fmt_temp(coolest['temp'], unit)}</div>
</div>
<div class="stat-tile">
<div class="stat-label">💧 Most Humid</div>
<div class="stat-val" style="color:#60a5fa;">{humidest['name']}</div>
<div style="font-size:0.85rem; color:#cbd5e1;">{humidest['humidity']}%</div>
</div>
</div>
""", unsafe_allow_html=True)

                for w in results:
                    aqi_txt, aqi_col = aqi_info(w.get("aqi"))
                    umbrella, alerts = get_umbrella_and_alerts(w, color=False)
                    alert_html = "".join(
                        f'<div style="color:#fca5a5; font-size:0.82rem; margin-top:4px;">🚨 {a}</div>'
                        for a in alerts
                    )
                    st.markdown(f"""
<div class="cmp-card">
<div class="cmp-top">
<div>
<div style="font-size:1.1rem; font-weight:700;">{w['icon']} {w['name']} <span style="font-size:0.82rem; color:#94a3b8; font-weight:500;">{w['country']}</span></div>
<div style="font-size:0.85rem; color:#cbd5e1;">{w['condition']} • {umbrella}</div>
</div>
<div style="font-size:1.65rem; font-weight:800; color:#f8fafc;">{fmt_temp(w['temp'], unit)}</div>
</div>
<div class="cmp-meta">
<span class="tag-pill">💧 {w['humidity']}%</span>
<span class="tag-pill">🌧️ {w['rain_prob']}%</span>
<span class="tag-pill" style="color:{aqi_col};">😷 AQI {aqi_txt}</span>
<span class="tag-pill">🌅 {w['sunrise']}</span>
<span class="tag-pill">🌇 {w['sunset']}</span>
</div>
{alert_html}
</div>
""", unsafe_allow_html=True)
