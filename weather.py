from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
import re
import sys
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".weather_cache.json")

# ANSI Colors for a vibrant terminal UI
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"

# Weather codes: code -> (label, emoji, art_key)
WEATHER_CODES = {
    0: ("Clear sky", "☀️", "sun"),
    1: ("Mainly clear", "🌤️", "sun"),
    2: ("Partly cloudy", "⛅", "partly"),
    3: ("Overcast", "☁️", "cloud"),
    45: ("Fog", "🌫️", "fog"),
    48: ("Haze", "🌫️", "fog"),
    51: ("Light drizzle", "🌦️", "rain"),
    53: ("Moderate drizzle", "🌦️", "rain"),
    55: ("Dense drizzle", "🌧️", "rain"),
    61: ("Light rain", "🌧️", "rain"),
    63: ("Moderate rain", "🌧️", "rain"),
    65: ("Heavy rain", "🌧️", "rain"),
    71: ("Light snow", "❄️", "snow"),
    73: ("Moderate snow", "❄️", "snow"),
    75: ("Heavy snow", "❄️", "snow"),
    80: ("Rain showers", "🌦️", "rain"),
    81: ("Moderate showers", "🌧️", "rain"),
    82: ("Heavy showers", "⛈️", "storm"),
    95: ("Thunderstorm", "⛈️", "storm"),
    96: ("Thunderstorm + hail", "⛈️", "storm"),
    99: ("Severe thunderstorm", "⛈️", "storm"),
}

WEATHER_ART = {
    "sun": [
        f"{YELLOW}    \\   /    {RESET}",
        f"{YELLOW}     .-.     {RESET}",
        f"{YELLOW}  ― (   ) ―  {RESET}",
        f"{YELLOW}     `-'     {RESET}",
        f"{YELLOW}    /   \\    {RESET}",
    ],
    "partly": [
        f"{YELLOW}   \\  /      {RESET}",
        f"{YELLOW} _ /\"\"{WHITE}.-.    {RESET}",
        f"{YELLOW}   \\_{WHITE}(   ).  {RESET}",
        f"{WHITE}   /(___(__) {RESET}",
        "             ",
    ],
    "cloud": [
        "             ",
        f"{WHITE}     .--.    {RESET}",
        f"{WHITE}  .-(    ).  {RESET}",
        f"{WHITE} (___.__)__) {RESET}",
        "             ",
    ],
    "rain": [
        f"{WHITE}     .--.    {RESET}",
        f"{WHITE}  .-(    ).  {RESET}",
        f"{WHITE} (___.__)__) {RESET}",
        f"{CYAN}  ʻ‚ʻ‚ʻ‚ʻ‚   {RESET}",
        "             ",
    ],
    "storm": [
        f"{WHITE}     .--.    {RESET}",
        f"{WHITE}  .-(    ).  {RESET}",
        f"{WHITE} (___.__)__) {RESET}",
        f"{YELLOW}   ⚡{CYAN}ʻ‚{YELLOW}⚡{CYAN}‚    {RESET}",
        "             ",
    ],
    "fog": [
        "             ",
        f"{DIM} _ - _ - _ - {RESET}",
        f"{DIM}  _ - _ - _  {RESET}",
        f"{DIM} _ - _ - _ - {RESET}",
        "             ",
    ],
    "snow": [
        f"{WHITE}     .--.    {RESET}",
        f"{WHITE}  .-(    ).  {RESET}",
        f"{WHITE} (___.__)__) {RESET}",
        f"{CYAN}  *  *  *  * {RESET}",
        "             ",
    ],
}


class NoInternetError(Exception):
    """Raised when network/internet connection is unavailable."""


def fetch_json(url, retries=2):
    """Fetch JSON data from an API URL with simple retry logic."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SmartWeatherCLI/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                return json.loads(response.read().decode())
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            if attempt < retries:
                time.sleep(0.5)
    raise NoInternetError(f"Network unreachable ({last_err})")


CACHE_LOCK = threading.Lock()


def save_cache(key, weather_obj):
    """Save last successful weather report locally for offline fallback."""
    try:
        with CACHE_LOCK:
            cache = {}
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            weather_copy = dict(weather_obj)
            weather_copy["cached_at"] = datetime.now().strftime("%d %b, %I:%M %p")
            cache[key.lower()] = weather_copy
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
    except Exception:
        pass


def load_cache(key):
    """Load cached weather if offline."""
    try:
        with CACHE_LOCK:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                return cache.get(key.lower())
    except Exception:
        pass
    return None


def detect_my_location():
    """Auto-detect approximate GPS coordinates & city via IP geolocation (no key needed)."""
    for url in ("https://ipwho.is/", "https://ipapi.co/json/"):
        try:
            data = fetch_json(url, retries=1)
            lat = data.get("latitude")
            lon = data.get("longitude")
            city = data.get("city")
            country = data.get("country") or data.get("country_name") or ""
            if lat is not None and lon is not None and city:
                return {"name": city, "country": country, "lat": lat, "lon": lon}
        except Exception:
            continue
    return None


def format_time(iso_str):
    """Convert '2026-11-12T06:42' to '06:42 AM'."""
    if not iso_str:
        return "N/A"
    return datetime.fromisoformat(iso_str).strftime("%I:%M %p")


def temp_color(temp):
    """Pick an ANSI color based on temperature."""
    if temp >= 35:
        return RED
    if temp >= 25:
        return YELLOW
    if temp >= 15:
        return GREEN
    return CYAN


def aqi_badge(aqi):
    """Return (label, color) for US AQI value."""
    if aqi is None:
        return "N/A", DIM
    if aqi <= 50:
        return "Good", GREEN
    if aqi <= 100:
        return "Moderate", YELLOW
    if aqi <= 150:
        return "Sensitive", YELLOW
    if aqi <= 200:
        return "Unhealthy", RED
    return "Hazardous", MAGENTA


def make_bar(percent, width=8, fill_color=CYAN):
    """Create a visual progress bar like '████░░░░'."""
    clamped = max(0, min(100, int(percent)))
    filled = round((clamped / 100) * width)
    return f"{fill_color}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"


def visible_len(text):
    """Display column width of text (ignoring ANSI codes and handling wide emojis)."""
    clean = re.sub(r"\033\[[0-9;]*m", "", text)
    width = 0
    prev_narrow = False
    for ch in clean:
        if ch == "\ufe0f":
            if prev_narrow:
                width += 1
                prev_narrow = False
            continue
        if unicodedata.combining(ch):
            continue
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
            prev_narrow = False
        else:
            width += 1
            prev_narrow = True
    return width


def pad_ansi(text, width):
    """Pad colored text to a fixed visible column width."""
    padding = max(0, width - visible_len(text))
    return text + (" " * padding)


def build_hourly_strip(data):
    """Extract next 6 upcoming 2-hour forecast slots starting from current hour."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    probs = hourly.get("precipitation_probability", [])
    codes = hourly.get("weather_code", [])
    curr_time = data.get("current", {}).get("time", "")[:13]

    start_idx = 0
    for idx, t in enumerate(times):
        if t[:13] >= curr_time:
            start_idx = idx
            break

    strip = []
    for idx in range(start_idx, min(len(times), start_idx + 12), 2):
        label = datetime.fromisoformat(times[idx]).strftime("%I%p").lstrip("0")
        _, emoji, _ = WEATHER_CODES.get(codes[idx], ("Unknown", "❓", "cloud"))
        rain = probs[idx] if probs[idx] is not None else 0
        strip.append({
            "time": label,
            "temp": round(temps[idx]),
            "rain": rain,
            "icon": emoji,
        })
    return strip


def c_to_f(temp_c):
    """Convert Celsius temperature to Fahrenheit (1 decimal)."""
    return round((temp_c * 9 / 5) + 32, 1)


def build_daily_forecast(data):
    """Extract 5-day daily forecast cards from Open-Meteo daily payload."""
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    maxs = daily.get("temperature_2m_max", [])
    mins = daily.get("temperature_2m_min", [])
    probs = daily.get("precipitation_probability_max", [])

    cards = []
    for idx in range(min(5, len(dates))):
        dt = datetime.fromisoformat(dates[idx])
        day_label = "Today" if idx == 0 else dt.strftime("%a")
        code = codes[idx] if idx < len(codes) else 0
        cond, icon, _ = WEATHER_CODES.get(code, ("Unknown", "❓", "cloud"))
        rain = probs[idx] if idx < len(probs) and probs[idx] is not None else 0
        cards.append({
            "date": dt.strftime("%d %b"),
            "day": day_label,
            "condition": cond,
            "icon": icon,
            "temp_max": round(maxs[idx], 1) if idx < len(maxs) else 0,
            "temp_min": round(mins[idx], 1) if idx < len(mins) else 0,
            "rain_prob": rain,
        })
    return cards


def reverse_geocode(lat, lon):
    """Convert GPS coordinates into (city_name, country) using a free keyless endpoint."""
    try:
        url = (
            f"https://api.bigdatacloud.net/data/reverse-geocode-client"
            f"?latitude={lat}&longitude={lon}&localityLanguage=en"
        )
        data = fetch_json(url, retries=1)
        city = data.get("city") or data.get("locality") or data.get("principalSubdivision")
        country = data.get("countryName", "")
        if city:
            return city, country
    except Exception:
        pass
    return f"{lat:.2f}, {lon:.2f}", "GPS"


def fetch_weather_by_coords(name, country, lat, lon):
    """Fetch weather, hourly strip, 5-day forecast, sunrise/sunset, AQI, and UV concurrently."""
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
        f"&hourly=temperature_2m,precipitation_probability,weather_code"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_probability_max,uv_index_max"
        f"&timezone=auto&forecast_days=5"
    )
    aq_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}&current=us_aqi,uv_index"
    )

    def fetch_aq():
        try:
            return fetch_json(aq_url, retries=1)
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_weather = pool.submit(fetch_json, weather_url)
        fut_aq = pool.submit(fetch_aq)
        data = fut_weather.result()
        aq_data = fut_aq.result()

    current = data["current"]
    daily = data["daily"]

    aqi = None
    uv_now = daily.get("uv_index_max", [None])[0]
    if aq_data:
        aqi = aq_data.get("current", {}).get("us_aqi")
        if aq_data.get("current", {}).get("uv_index") is not None:
            uv_now = aq_data["current"]["uv_index"]

    rain_prob = daily["precipitation_probability_max"][0]
    if rain_prob is None:
        rain_prob = 0

    label, icon, art_key = WEATHER_CODES.get(current["weather_code"], ("Unknown", "❓", "cloud"))

    result = {
        "name": name,
        "country": country,
        "temp": current["temperature_2m"],
        "feels_like": current.get("apparent_temperature", current["temperature_2m"]),
        "humidity": current["relative_humidity_2m"],
        "wind": current["wind_speed_10m"],
        "condition": label,
        "icon": icon,
        "art_key": art_key,
        "rain_prob": rain_prob,
        "aqi": aqi,
        "uv": round(uv_now, 1) if uv_now is not None else None,
        "sunrise": format_time(daily["sunrise"][0]),
        "sunset": format_time(daily["sunset"][0]),
        "hourly": build_hourly_strip(data),
        "daily": build_daily_forecast(data),
    }
    save_cache(name, result)
    return result


def fetch_city_weather(city):
    """Geocode city name and fetch weather (falls back to offline cache if no internet)."""
    try:
        encoded_city = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"
        geo_data = fetch_json(geo_url)
        if not geo_data.get("results"):
            return None
        place = geo_data["results"][0]
        return fetch_weather_by_coords(
            place["name"], place.get("country", ""), place["latitude"], place["longitude"]
        )
    except NoInternetError:
        cached = load_cache(city)
        if cached:
            cached["from_cache"] = True
            return cached
        raise


def fetch_multiple_cities(city_names):
    """Fetch weather for multiple cities in parallel, preserving order."""
    results = []
    missing = []

    def safe_fetch(name):
        try:
            return name, fetch_city_weather(name), None
        except NoInternetError as err:
            return name, None, err

    with ThreadPoolExecutor(max_workers=min(5, max(1, len(city_names)))) as pool:
        outcomes = list(pool.map(safe_fetch, city_names))

    for name, info, err in outcomes:
        if err is not None:
            raise err
        if info is None:
            missing.append(name)
        else:
            results.append(info)
    return results, missing


def get_umbrella_and_alerts(w, color=True):
    """Return umbrella suggestion and weather alerts with symbols."""
    cond_lower = w["condition"].lower()
    is_rainy = any(word in cond_lower for word in ("rain", "drizzle", "shower", "thunderstorm"))

    def wrap(ansi, text):
        return f"{ansi}{text}{RESET}" if color else text

    if is_rainy or w["rain_prob"] >= 50:
        umbrella = wrap(BLUE, f"☔ Carry an umbrella! ({w['condition']}, {w['rain_prob']}% rain)")
    elif w["rain_prob"] >= 25:
        umbrella = wrap(CYAN, f"🌂 Keep a small umbrella handy ({w['rain_prob']}% rain)")
    else:
        umbrella = wrap(GREEN, "😎 No umbrella needed today")

    alerts = []
    if "thunderstorm" in cond_lower or "heavy" in cond_lower:
        alerts.append(wrap(RED, f"⛈️  STORM ALERT: {w['condition']} — stay safe indoors"))
    if w["temp"] >= 35:
        alerts.append(wrap(RED, f"🔥 HEAT ALERT: {w['temp']}°C — stay hydrated & avoid direct sun"))
    elif w["temp"] <= 10:
        alerts.append(wrap(CYAN, f"❄️  COLD ALERT: {w['temp']}°C — wear warm layers"))
    if w["wind"] >= 35:
        alerts.append(wrap(YELLOW, f"💨 WIND ALERT: Strong winds ({w['wind']} km/h)"))
    if w["humidity"] >= 85:
        alerts.append(wrap(BLUE, f"💧 HUMIDITY ALERT: High humidity ({w['humidity']}%)"))
    if "fog" in cond_lower:
        alerts.append(wrap(YELLOW, "🌫️  VISIBILITY ALERT: Foggy — drive carefully"))
    if w.get("aqi") is not None and w["aqi"] > 150:
        alerts.append(wrap(RED, f"😷 AQI ALERT: Unhealthy air ({w['aqi']}) — wear a mask outdoors"))
    if w.get("uv") is not None and w["uv"] >= 8:
        alerts.append(wrap(YELLOW, f"🕶️  UV ALERT: High UV ({w['uv']}) — use sunscreen/hat"))

    return umbrella, alerts


def show_single_city(w):
    """Display creative weather card with ASCII art, AQI/UV, hourly strip, and alerts."""
    t_col = temp_color(w["temp"])
    art = WEATHER_ART[w["art_key"]]
    umbrella, alerts = get_umbrella_and_alerts(w)
    aqi_label, aqi_col = aqi_badge(w.get("aqi"))
    aqi_text = f"{aqi_col}{w['aqi']} ({aqi_label}){RESET}" if w.get("aqi") is not None else f"{DIM}N/A{RESET}"
    uv_text = f"{w['uv']}" if w.get("uv") is not None else "N/A"

    title = f"📍 {w['name']}, {w['country']}".strip(", ")
    if w.get("from_cache"):
        title += f"  {YELLOW}[OFFLINE CACHE: {w.get('cached_at', '')}]{RESET}"

    info_lines = [
        f"{BOLD}{WHITE}{title}{RESET}",
        f"{t_col}{BOLD}{w['temp']}°C{RESET} {DIM}(Feels {w['feels_like']}°C){RESET}  •  {w['condition']}",
        f"💧 Humidity: {make_bar(w['humidity'], 8, BLUE)} {w['humidity']}%   💨 Wind: {w['wind']} km/h",
        f"🌧️  Rain:     {make_bar(w['rain_prob'], 8, CYAN)} {w['rain_prob']}%   😷 AQI: {aqi_text}  ☀️ UV: {uv_text}",
        f"🌅 Sunrise:  {YELLOW}{w['sunrise']}{RESET}   🌇 Sunset: {MAGENTA}{w['sunset']}{RESET}",
    ]

    rows = [f" {art_line}  {info_line}" for art_line, info_line in zip(art, info_lines)]
    hourly = w.get("hourly", [])
    hourly_line = None
    if hourly:
        slots = "  ".join(f"{DIM}{h['time']}{RESET} {h['icon']} {h['temp']}°({h['rain']}%)" for h in hourly)
        hourly_line = f" 🕒 Next Hours: {slots}"

    footer_lines = [' 🎒 ' + umbrella]
    if alerts:
        footer_lines.extend(' 🚨 ' + alert for alert in alerts)
    else:
        footer_lines.append(f" {GREEN}✅ All clear — no severe weather alerts{RESET}")

    candidates = rows + footer_lines + ([hourly_line] if hourly_line else [])
    inner_width = max(78, max(visible_len(line) for line in candidates) + 2)

    print(f"\n{CYAN}╭{'─' * inner_width}╮{RESET}")
    for row in rows:
        print(f"{CYAN}│{RESET}{pad_ansi(row, inner_width)}{CYAN}│{RESET}")
    if hourly_line:
        print(f"{CYAN}├{'─' * inner_width}┤{RESET}")
        print(f"{CYAN}│{RESET}{pad_ansi(hourly_line, inner_width)}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * inner_width}┤{RESET}")
    for line in footer_lines:
        print(f"{CYAN}│{RESET}{pad_ansi(line, inner_width)}{CYAN}│{RESET}")
    print(f"{CYAN}╰{'─' * inner_width}╯{RESET}\n")


def compare_cities(city_names):
    """Compare up to 5 cities in a creative boxed dashboard."""
    results, missing = fetch_multiple_cities(city_names)
    for name in missing:
        print(f"{YELLOW}⚠️  City '{name}' not found (skipping).{RESET}")

    if not results:
        return

    w_city, w_temp, w_aqi, w_hum, w_rain, w_sun = 12, 8, 13, 13, 17, 21
    total_w = w_city + w_temp + w_aqi + w_hum + w_rain + w_sun + 17

    print(f"\n{CYAN}╭{'─' * total_w}╮{RESET}")
    header_title = f"{BOLD}{WHITE}🌍 MULTI-CITY WEATHER COMPARISON ({len(results)} CITIES){RESET}"
    print(f"{CYAN}│{RESET} {pad_ansi(header_title, total_w - 1)}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * total_w}┤{RESET}")

    cols = (
        f" {BOLD}{'City':<{w_city}}{RESET} │ "
        f"{BOLD}{'Temp':<{w_temp}}{RESET} │ "
        f"{BOLD}{'AQI':<{w_aqi}}{RESET} │ "
        f"{BOLD}{'Humidity':<{w_hum}}{RESET} │ "
        f"{BOLD}{'Rain & Sky':<{w_rain}}{RESET} │ "
        f"{BOLD}{'Sunrise / Sunset':<{w_sun}}{RESET} "
    )
    print(f"{CYAN}│{RESET}{pad_ansi(cols, total_w)}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * total_w}┤{RESET}")

    for w in results:
        t_col = temp_color(w["temp"])
        aqi_label, aqi_col = aqi_badge(w.get("aqi"))
        aqi_str = pad_ansi(
            f"{aqi_col}{w['aqi']} {aqi_label}{RESET}" if w.get("aqi") is not None else f"{DIM}N/A{RESET}",
            w_aqi,
        )
        c_str = f"{BOLD}{w['name'][:w_city]:<{w_city}}{RESET}"
        t_str = pad_ansi(f"{t_col}{w['temp']}°C{RESET}", w_temp)
        h_str = pad_ansi(f"{make_bar(w['humidity'], 5, BLUE)} {w['humidity']}%", w_hum)
        r_text = f"{w['rain_prob']}% {w['condition']}"[:w_rain]
        r_str = f"{r_text:<{w_rain}}"
        s_str = pad_ansi(f"{YELLOW}{w['sunrise']}{RESET} / {MAGENTA}{w['sunset']}{RESET}", w_sun)

        row = f" {c_str} │ {t_str} │ {aqi_str} │ {h_str} │ {r_str} │ {s_str} "
        print(f"{CYAN}│{RESET}{pad_ansi(row, total_w)}{CYAN}│{RESET}")

    print(f"{CYAN}╰{'─' * total_w}╯{RESET}")

    # Highlights
    warmest = max(results, key=lambda x: x["temp"])
    coolest = min(results, key=lambda x: x["temp"])
    humidest = max(results, key=lambda x: x["humidity"])
    print(
        f"\n✨ {BOLD}Highlights:{RESET} "
        f"{RED}🔥 Warmest: {warmest['name']} ({warmest['temp']}°C){RESET}  •  "
        f"{CYAN}❄️ Coolest: {coolest['name']} ({coolest['temp']}°C){RESET}  •  "
        f"{BLUE}💧 Most Humid: {humidest['name']} ({humidest['humidity']}%){RESET}"
    )

    print(f"\n{BOLD}🎒 Umbrella Suggestions & Weather Alerts:{RESET}")
    for w in results:
        umbrella, alerts = get_umbrella_and_alerts(w)
        print(f"  {w['icon']} {BOLD}{w['name']}:{RESET} {umbrella}")
        for alert in alerts:
            print(f"      🚨 {alert}")
    print()


def print_banner():
    """Print an eye-catching startup header."""
    title = f"  {BOLD}{WHITE}🌤️  SMART WEATHER & TRAVEL ADVISOR{RESET}  {DIM}(Open-Meteo API){RESET}"
    print(f"\n{CYAN}╭───────────────────────────────────────────────────────────╮{RESET}")
    print(f"{CYAN}│{RESET}{pad_ansi(title, 59)}{CYAN}│{RESET}")
    print(f"{CYAN}╰───────────────────────────────────────────────────────────╯{RESET}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.system("")  # Enable ANSI colors on Windows console
    print_banner()
    raw = input(
        f"🔎 Enter 1–5 cities {DIM}(e.g. Pune, Mumbai){RESET} or press {BOLD}Enter{RESET} for 📍 My Location: "
    ).strip()

    try:
        if raw == "" or raw.lower() in ("me", "gps", "location", "auto"):
            print(f"{CYAN}📡 Detecting your location...{RESET}")
            loc = detect_my_location()
            if not loc:
                print(f"{RED}❌ Could not auto-detect location. Please enter a city name manually.{RESET}")
            else:
                weather = fetch_weather_by_coords(loc["name"], loc["country"], loc["lat"], loc["lon"])
                show_single_city(weather)
        else:
            cities = [c.strip() for c in raw.split(",") if c.strip()]
            if len(cities) > 5:
                print(f"{YELLOW}⚠️  You can compare at most 5 cities. Showing the first 5.{RESET}")
                cities = cities[:5]

            if len(cities) == 1:
                weather = fetch_city_weather(cities[0])
                if weather is None:
                    print(f"{RED}❌ City '{cities[0]}' not found. Please check spelling.{RESET}")
                else:
                    show_single_city(weather)
            else:
                compare_cities(cities)
    except NoInternetError as e:
        print(f"{RED}❌ No internet connection and no offline cache found. ({e}){RESET}")
    except Exception as e:
        print(f"{RED}❌ Unexpected error: {e}{RESET}")
