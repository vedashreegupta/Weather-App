"""
SkyPulse Weather - Zero-Flicker Mobile PWA Backend (Starlette + Uvicorn)
Reuses core Open-Meteo logic from weather.py with 10-minute in-memory caching.
"""

import os
import threading
import time
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Route
import uvicorn

from weather import (
    NoInternetError,
    detect_my_location,
    fetch_city_weather,
    fetch_multiple_cities,
    fetch_weather_by_coords,
    get_umbrella_and_alerts,
    reverse_geocode,
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
_MEM_CACHE = {}
_MEM_LOCK = threading.Lock()
CACHE_TTL = 600  # 10 minutes


def _cache_get(key):
    with _MEM_LOCK:
        entry = _MEM_CACHE.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["data"]
    return None


def _cache_set(key, data):
    with _MEM_LOCK:
        _MEM_CACHE[key] = {"ts": time.time(), "data": data}


def _enrich_weather(w):
    """Attach clean umbrella and alert strings for JSON responses."""
    umbrella, alerts = get_umbrella_and_alerts(w, color=False)
    enriched = dict(w)
    enriched["umbrella"] = umbrella
    enriched["alerts"] = alerts
    return enriched


async def serve_index(request):
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


async def serve_manifest(request):
    return FileResponse(os.path.join(STATIC_DIR, "manifest.json"), media_type="application/manifest+json")


async def serve_sw(request):
    return FileResponse(os.path.join(STATIC_DIR, "sw.js"), media_type="application/javascript")


async def serve_icon(request):
    return FileResponse(os.path.join(STATIC_DIR, "icon.svg"), media_type="image/svg+xml")


async def api_weather(request):
    city = request.query_params.get("city", "").strip()
    lat_str = request.query_params.get("lat")
    lon_str = request.query_params.get("lon")

    try:
        if lat_str is not None and lon_str is not None:
            lat = round(float(lat_str), 4)
            lon = round(float(lon_str), 4)
            key = f"coords:{lat},{lon}"
            cached = _cache_get(key)
            if cached:
                return JSONResponse(cached)
            name, country = reverse_geocode(lat, lon)
            w = fetch_weather_by_coords(name, country, lat, lon)
            payload = _enrich_weather(w)
            _cache_set(key, payload)
            return JSONResponse(payload)

        if not city:
            return JSONResponse({"error": "Please provide a city name."}, status_code=400)

        key = f"city:{city.lower()}"
        cached = _cache_get(key)
        if cached:
            return JSONResponse(cached)

        w = fetch_city_weather(city)
        if not w:
            return JSONResponse({"error": f"City '{city}' not found."}, status_code=404)

        payload = _enrich_weather(w)
        _cache_set(key, payload)
        return JSONResponse(payload)

    except ValueError:
        return JSONResponse({"error": "Invalid coordinates."}, status_code=400)
    except NoInternetError:
        return JSONResponse({"error": "No internet connection and no offline cache available."}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def api_auto_location(request):
    try:
        loc = detect_my_location()
        if not loc:
            return JSONResponse({"error": "Could not auto-detect location."}, status_code=404)
        w = fetch_weather_by_coords(loc["name"], loc["country"], loc["lat"], loc["lon"])
        return JSONResponse(_enrich_weather(w))
    except NoInternetError:
        return JSONResponse({"error": "No internet connection."}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def api_compare(request):
    raw = request.query_params.get("cities", "")
    cities = [c.strip() for c in raw.split(",") if c.strip()][:5]
    if not cities:
        return JSONResponse({"error": "Provide 1 to 5 cities separated by commas."}, status_code=400)

    key = "cmp:" + ",".join(c.lower() for c in cities)
    cached = _cache_get(key)
    if cached:
        return JSONResponse(cached)

    try:
        results, missing = fetch_multiple_cities(cities)
        payload = {
            "results": [_enrich_weather(w) for w in results],
            "missing": missing,
        }
        _cache_set(key, payload)
        return JSONResponse(payload)
    except NoInternetError:
        return JSONResponse({"error": "No internet connection."}, status_code=503)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


app = Starlette(
    routes=[
        Route("/", serve_index),
        Route("/manifest.json", serve_manifest),
        Route("/sw.js", serve_sw),
        Route("/icon.svg", serve_icon),
        Route("/api/weather", api_weather),
        Route("/api/auto-location", api_auto_location),
        Route("/api/compare", api_compare),
    ]
)

if __name__ == "__main__":
    print("🚀 Starting SkyPulse Mobile PWA at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
