# 🌤️ Project 4: Weather App with API (Open-Meteo)

> A fast, zero-configuration Python CLI tool that fetches real-time weather, 5-day forecasts, and multi-city comparisons using live internet APIs.

---

## 🎯 What This Project Actually Is
A clean Python script where you type:
```text
Enter city: Pune
```
And it prints:
```text
Pune: 25.0°C, Clear sky, Humidity 48%, Wind 3.4 km/h
```

It does this by calling a free weather API (**Open-Meteo**) over the internet, receiving JSON back, and parsing it.

---

## 💡 What Problem Does It Solve?
1. **The Learning Problem (Core Skill):**
   - Teaches the fundamental industry skill: **API Integration**.
   - Connects two real APIs: **Geocoding API** (City Name → Latitude & Longitude) and **Forecast API** (Coordinates → Live Weather & Forecast JSON).
   - Handles network timeouts, HTTP status errors, and invalid inputs gracefully.
2. **The Automation / Customization Problem:**
   - **Compare Mode:** Compare weather across multiple cities side-by-side (`py weather.py Pune Mumbai Delhi`) — saving multiple clicks compared to manual web browsing.
   - **Travel Packer:** Automatically analyzes rain chance and temperature to advise if you should carry an umbrella, raincoat, or warm jacket.
   - **Fast & Ad-Free:** Zero bloat, lightweight terminal tool designed for developers.
3. **The Portfolio Problem:**
   - Shows employers you understand HTTP requests, JSON parsing, dictionary manipulation, and CLI tools.

---

## 🚀 How to Run

### Method 1: Double-Click
Simply double-click `run.bat` in this folder!

### Method 2: From Terminal
Make sure `requests` is installed:
```bash
pip install -r requirements.txt
```

#### 1. Interactive Mode
```bash
py weather.py
```
```text
Enter city: Pune
👉 Pune: 25.0°C, Clear sky, Humidity 48%, Wind 3.4 km/h
```

#### 2. Direct Single City Search
```bash
py weather.py Pune
```

#### 3. Compare Multiple Cities Side-by-Side
```bash
py weather.py Pune Mumbai Delhi
```
*Outputs an ASCII comparison table with temperature, condition, humidity, and wind!*

#### 4. 5-Day Forecast & Travel Packing Advice
```bash
py weather.py Pune --forecast --pack
```

---

## 📂 Project Structure

```
weather_app/
├── weather.py          # Main application (API calls, parsing, CLI modes)
├── requirements.txt    # Dependencies (requests)
├── run.bat             # 1-click Windows launcher
└── README.md           # Documentation & learning notes
```

---

## 🛠️ Concepts Learned & Used
- `requests.get()` for sending HTTP GET requests
- Parsing nested JSON dictionaries & lists
- Error handling: `try/except` for network errors, 404/503 status codes, and invalid inputs
- WMO Weather Code decoding (translating numbers like `0`, `45`, `61` into readable weather descriptions & emojis)
- `argparse` for clean command-line arguments and flags
