"""
=============================================================================
 Project: Weather App with API (Open-Meteo)
 Free, no API key required, zero signup.
 
 Core Flow:
 1. User inputs city name (e.g. Pune, Mumbai, London)
 2. Geocoding API: City Name -> Latitude & Longitude
 3. Weather API: Coordinates -> Real-time Weather & Forecast JSON
 4. Parse & Display: Clean terminal output, packing tips & comparisons
=============================================================================
"""

import sys
import argparse
import requests


# WMO Weather interpretation codes (WW)
# Source: Open-Meteo / World Meteorological Organization
WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog / Haze", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌨️"),
    57: ("Dense freezing drizzle", "🌨️"),
    61: ("Slight rain", "🌧️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌨️"),
    67: ("Heavy freezing rain", "🌨️"),
    71: ("Slight snow fall", "❄️"),
    73: ("Moderate snow fall", "❄️"),
    75: ("Heavy snow fall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


def weather_code_to_text(code: int) -> tuple[str, str]:
    """Convert WMO code integer to readable text and emoji icon."""
    return WEATHER_CODES.get(code, ("Unknown", "❓"))


def get_coordinates(city_name: str) -> dict | None:
    """
    Step 1: Geocoding
    Calls Open-Meteo Geocoding API to convert city name into latitude & longitude.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name.strip(),
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results")
        if not results:
            return None
        
        first = results[0]
        return {
            "name": first.get("name"),
            "country": first.get("country", ""),
            "admin1": first.get("admin1", ""), # State/Province
            "lat": first.get("latitude"),
            "lon": first.get("longitude")
        }
    except requests.RequestException as e:
        print(f"❌ Network Error: Could not connect to Geocoding API ({e})")
        return None


def get_weather(lat: float, lon: float) -> dict | None:
    """
    Step 2: Weather Data Fetching
    Calls Open-Meteo Forecast API for current weather & daily forecast.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "timezone": "auto"
    }

    try:
        response = requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Network Error: Could not fetch weather data ({e})")
        return None


def get_packing_advice(temp: float, rain_chance: int, condition: str) -> list[str]:
    """Smart feature: Generates practical travel / day advice."""
    advice = []
    
    # Rain checks
    if rain_chance >= 60 or "rain" in condition.lower() or "drizzle" in condition.lower() or "shower" in condition.lower():
        advice.append("☔ Rain alert! Carry an umbrella or raincoat.")
    elif rain_chance >= 30:
        advice.append("🌂 Slight chance of rain, keeping a small umbrella handy might help.")
        
    # Temperature checks
    if temp >= 35:
        advice.append("☀️ Extreme heat! Stay hydrated, wear light cottons, and use sunscreen.")
    elif temp >= 28:
        advice.append("😎 Warm weather - sunglasses and hydration recommended.")
    elif temp <= 10:
        advice.append("🧥 Cold weather! Wear a warm jacket, sweater, and scarf.")
    elif temp <= 18:
        advice.append("🧣 Chilly breeze - a light jacket or hoodie is ideal.")
        
    if not advice:
        advice.append("✨ Pleasant weather! No special gear needed.")
        
    return advice


def display_current_weather(city_info: dict, weather_data: dict, show_pack: bool = False, show_forecast: bool = False):
    """Formats and prints clean, readable weather info to terminal."""
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    temp = current.get("temperature_2m", "N/A")
    feels_like = current.get("apparent_temperature", "N/A")
    humidity = current.get("relative_humidity_2m", "N/A")
    wind = current.get("wind_speed_10m", "N/A")
    w_code = current.get("weather_code", 0)
    cond_text, cond_emoji = weather_code_to_text(w_code)

    today_rain_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0

    location_str = f"{city_info['name']}"
    if city_info.get("country"):
        location_str += f", {city_info['country']}"

    # Exact target format from your spec:
    # Pune: 29°C, Haze, Humidity 62%, Wind 11 km/h
    print(f"\n👉 {city_info['name']}: {temp}°C, {cond_text}, Humidity {humidity}%, Wind {wind} km/h")
    print("=" * 55)
    print(f"📍 {location_str}  {cond_emoji}")
    print(f"   • Temperature: {temp}°C (Feels like {feels_like}°C)")
    print(f"   • Condition:   {cond_text}")
    print(f"   • Humidity:    {humidity}%")
    print(f"   • Wind Speed:  {wind} km/h")
    print(f"   • Rain Chance: {today_rain_prob}%")
    print("=" * 55)

    # Smart feature: Travel Packing advice
    if show_pack or today_rain_prob >= 50 or (isinstance(temp, (int, float)) and (temp >= 35 or temp <= 12)):
        print("\n🎒 Daily / Travel Advice:")
        advice_list = get_packing_advice(temp if isinstance(temp, (int, float)) else 20, today_rain_prob, cond_text)
        for tip in advice_list:
            print(f"   {tip}")

    # Extension: 5-Day Forecast
    if show_forecast and daily:
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        codes = daily.get("weather_code", [])

        print("\n📅 5-Day Forecast:")
        print(f" {'Date':<12} | {'Condition':<20} | {'High / Low':<12} | {'Rain %':<6}")
        print("-" * 55)
        for i in range(min(5, len(dates))):
            d_date = dates[i]
            d_cond, d_icon = weather_code_to_text(codes[i])
            d_cond_str = f"{d_icon} {d_cond}"[:18]
            d_range = f"{max_temps[i]}° / {min_temps[i]}°"
            d_rain = f"{rain_probs[i]}%"
            print(f" {d_date:<12} | {d_cond_str:<20} | {d_range:<12} | {d_rain:<6}")
    print()


def compare_cities(city_list: list[str]):
    """
    Compare Mode: Fetch multiple cities and display in a clean side-by-side table.
    Example: python weather.py Pune Mumbai Delhi
    """
    print(f"\n📊 Comparing weather across {len(city_list)} cities...\n")
    rows = []

    for city in city_list:
        coords = get_coordinates(city)
        if not coords:
            rows.append({
                "city": city,
                "temp": "N/A",
                "condition": "City Not Found",
                "humidity": "N/A",
                "wind": "N/A"
            })
            continue

        w_data = get_weather(coords["lat"], coords["lon"])
        if not w_data or "current" not in w_data:
            rows.append({
                "city": coords["name"],
                "temp": "N/A",
                "condition": "Data Error",
                "humidity": "N/A",
                "wind": "N/A"
            })
            continue

        curr = w_data["current"]
        cond_text, cond_emoji = weather_code_to_text(curr.get("weather_code", 0))
        rows.append({
            "city": f"{coords['name']} ({coords['country']})",
            "temp": f"{curr.get('temperature_2m')}°C",
            "condition": f"{cond_emoji} {cond_text}",
            "humidity": f"{curr.get('relative_humidity_2m')}%",
            "wind": f"{curr.get('wind_speed_10m')} km/h"
        })

    # Render formatted comparison table
    header = f" {'City':<22} | {'Temp':<8} | {'Condition':<20} | {'Humidity':<10} | {'Wind':<10}"
    divider = "-" * len(header)
    print(header)
    print(divider)
    for r in rows:
        print(f" {r['city']:<22} | {r['temp']:<8} | {r['condition']:<20} | {r['humidity']:<10} | {r['wind']:<10}")
    print(divider + "\n")


def run_interactive():
    """Default interactive CLI mode."""
    print("=" * 55)
    print(" 🌤️  Python Weather App (Powered by Open-Meteo)")
    print(" Free, instant live weather. Type 'exit' or 'q' to quit.")
    print("=" * 55)

    while True:
        try:
            city_input = input("\nEnter city: ").strip()
            if not city_input:
                continue
            if city_input.lower() in ("exit", "quit", "q"):
                print("👋 Goodbye!")
                break

            coords = get_coordinates(city_input)
            if not coords:
                print(f"❌ City '{city_input}' not found. Please check spelling!")
                continue

            weather = get_weather(coords["lat"], coords["lon"])
            if not weather:
                print("❌ Could not retrieve weather data. Please try again.")
                continue

            display_current_weather(coords, weather, show_pack=True, show_forecast=True)

        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="🌤️ Fast, free CLI Weather Tool using Open-Meteo API (No API Key Required!)"
    )
    parser.add_argument("cities", nargs="*", help="City name(s) to check (e.g. Pune or Pune Mumbai Delhi)")
    parser.add_argument("--forecast", "-f", action="store_true", help="Show 5-day daily forecast")
    parser.add_argument("--pack", "-p", action="store_true", help="Show travel packing recommendations")

    args = parser.parse_args()

    # 1. No arguments provided -> run interactive prompt
    if not args.cities:
        run_interactive()
        return

    # 2. Multiple cities passed -> run compare mode
    if len(args.cities) > 1:
        compare_cities(args.cities)
        return

    # 3. Single city passed as command-line argument
    city = args.cities[0]
    coords = get_coordinates(city)
    if not coords:
        print(f"❌ City '{city}' not found.")
        sys.exit(1)

    weather = get_weather(coords["lat"], coords["lon"])
    if not weather:
        print("❌ Could not fetch weather.")
        sys.exit(1)

    display_current_weather(coords, weather, show_pack=args.pack, show_forecast=args.forecast)


if __name__ == "__main__":
    main()
