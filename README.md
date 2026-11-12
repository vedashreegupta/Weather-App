# 🌤️ SkyPulse Weather (Mobile PWA + Streamlit + CLI)

A fast, free Python weather app powered by the **Open-Meteo API** — **zero API key required**!

## ✨ Features
- **📱 Zero-Flicker Mobile PWA (`pwa_app.py` + `static/`):** Installable on Android/iOS Home Screen (`manifest.json` + `sw.js`), smooth glassmorphic UI, instant API calls with zero page reload flicker.
- **📍 Real Browser GPS + IP Fallback:** Exact `navigator.geolocation` with reverse geocoding and automatic IP fallback.
- **🕒 Hourly Strip + 📅 5-Day Forecast:** Next 12 hours in 2-hour slots plus 5-day High/Low forecast cards.
- **°C / °F Toggle & ⭐ Recent Cities:** Switch units anytime and tap recent cities quickly.
- **😷 AQI & ☀️ UV Index:** Live US Air Quality Index and UV levels.
- **🌍 Compare up to 5 Cities (Parallel):** Fast concurrent fetching with Warmest / Coolest / Most Humid highlights.
- **☔ Umbrella & 🚨 Weather Alerts:** Smart rain advice plus storm, heat, cold, wind, humidity, fog, AQI, and UV alerts.
- **📶 Retry & Offline Cache:** Automatically retries and saves the last result in `.weather_cache.json`.

---

## 🚀 How to Run

### Option 1: Zero-Flicker Mobile PWA (Recommended ⚡)
Double-click **`run_pwa.bat`**, or run in terminal:
```bash
python pwa_app.py
```
Open `http://localhost:8000` (or the local network IP on your phone over Wi-Fi, then tap **Add to Home Screen**).

### Option 2: Streamlit Web Dashboard (`app.py`)
Double-click **`run_web.bat`**, or run:
```bash
python -m streamlit run app.py
```
*(Great for 1-click free hosting at [share.streamlit.io](https://share.streamlit.io).)*

### Option 3: Terminal CLI (`weather.py`)
Open **`weather.py`** in VS Code and click **▶ Run** (or double-click **`run.bat`**).

---

## 🧪 Run Unit Tests
```bash
python -m unittest test_weather.py -v
```
