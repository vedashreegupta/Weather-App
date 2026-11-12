"""Unit tests for SkyPulse Weather core logic and PWA helpers."""

import os
import tempfile
import unittest
from unittest.mock import patch

import pwa_app
import weather


class TestWeatherCore(unittest.TestCase):
    def test_c_to_f(self):
        self.assertEqual(weather.c_to_f(0), 32.0)
        self.assertEqual(weather.c_to_f(25), 77.0)
        self.assertEqual(weather.c_to_f(-10), 14.0)

    def test_aqi_badge_ranges(self):
        self.assertEqual(weather.aqi_badge(None)[0], "N/A")
        self.assertEqual(weather.aqi_badge(42)[0], "Good")
        self.assertEqual(weather.aqi_badge(85)[0], "Moderate")
        self.assertEqual(weather.aqi_badge(130)[0], "Sensitive")
        self.assertEqual(weather.aqi_badge(180)[0], "Unhealthy")
        self.assertEqual(weather.aqi_badge(250)[0], "Hazardous")

    def test_umbrella_and_alerts_plain_and_triggers(self):
        extreme = {
            "condition": "Thunderstorm",
            "rain_prob": 80,
            "temp": 37.5,
            "wind": 40.0,
            "humidity": 90,
            "aqi": 175,
            "uv": 9.2,
        }
        umbrella, alerts = weather.get_umbrella_and_alerts(extreme, color=False)
        self.assertIn("Carry an umbrella", umbrella)
        self.assertNotIn("\033", umbrella)
        self.assertEqual(len(alerts), 6)  # storm, heat, wind, humidity, aqi, uv
        self.assertTrue(all("\033" not in a for a in alerts))

    def test_umbrella_mild_and_clear(self):
        mild_rain = {
            "condition": "Overcast",
            "rain_prob": 30,
            "temp": 22.0,
            "wind": 8.0,
            "humidity": 55,
            "aqi": 40,
            "uv": 3.0,
        }
        umbrella, alerts = weather.get_umbrella_and_alerts(mild_rain, color=False)
        self.assertIn("small umbrella", umbrella)
        self.assertEqual(alerts, [])

        foggy_cold = {
            "condition": "Fog",
            "rain_prob": 0,
            "temp": 8.0,
            "wind": 5.0,
            "humidity": 70,
        }
        umb2, alerts2 = weather.get_umbrella_and_alerts(foggy_cold, color=False)
        self.assertIn("No umbrella needed", umb2)
        self.assertEqual(len(alerts2), 2)  # cold + fog

    def test_build_hourly_strip(self):
        payload = {
            "current": {"time": "2026-11-12T14:15"},
            "hourly": {
                "time": [f"2026-11-12T{h:02d}:00" for h in range(12, 24)]
                + [f"2026-11-13T{h:02d}:00" for h in range(0, 4)],
                "temperature_2m": [28 + (i % 5) for i in range(16)],
                "precipitation_probability": [None if i == 2 else i * 5 for i in range(16)],
                "weather_code": [0] * 16,
            },
        }
        strip = weather.build_hourly_strip(payload)
        self.assertEqual(len(strip), 6)
        self.assertEqual(strip[0]["time"], "2PM")
        self.assertEqual(strip[0]["rain"], 0)  # None coerced safely to 0

    def test_build_daily_forecast(self):
        payload = {
            "daily": {
                "time": ["2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15", "2026-11-16", "2026-11-17"],
                "weather_code": [0, 2, 61, 3, 95, 0],
                "temperature_2m_max": [30.1, 29.5, 26.0, 28.0, 27.4, 31.0],
                "temperature_2m_min": [18.2, 17.9, 16.5, 17.0, 18.0, 19.0],
                "precipitation_probability_max": [0, None, 75, 20, 85, 5],
            }
        }
        cards = weather.build_daily_forecast(payload)
        self.assertEqual(len(cards), 5)
        self.assertEqual(cards[0]["day"], "Today")
        self.assertEqual(cards[1]["rain_prob"], 0)
        self.assertEqual(cards[2]["condition"], "Light rain")

    def test_fetch_multiple_cities_parallel_order(self):
        def fake_fetch(city):
            if city == "Atlantis":
                return None
            return {"name": city, "temp": 25.0}

        with patch.object(weather, "fetch_city_weather", side_effect=fake_fetch):
            results, missing = weather.fetch_multiple_cities(["Pune", "Atlantis", "Tokyo", "Delhi"])
        self.assertEqual([r["name"] for r in results], ["Pune", "Tokyo", "Delhi"])
        self.assertEqual(missing, ["Atlantis"])

    def test_offline_cache_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_cache = os.path.join(tmpdir, "cache.json")
            with patch.object(weather, "CACHE_FILE", tmp_cache):
                weather.save_cache("Pune", {"name": "Pune", "temp": 26.5})
                loaded = weather.load_cache("pune")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["temp"], 26.5)
                self.assertIn("cached_at", loaded)


class TestPWAApp(unittest.TestCase):
    def test_static_assets_exist(self):
        for fname in ("index.html", "manifest.json", "sw.js", "icon.svg"):
            self.assertTrue(os.path.exists(os.path.join(pwa_app.STATIC_DIR, fname)), fname)

    def test_enrich_weather_and_mem_cache(self):
        sample = {
            "name": "Pune",
            "condition": "Clear sky",
            "rain_prob": 0,
            "temp": 26.0,
            "wind": 6.0,
            "humidity": 40,
        }
        enriched = pwa_app._enrich_weather(sample)
        self.assertIn("No umbrella needed", enriched["umbrella"])
        self.assertEqual(enriched["alerts"], [])

        pwa_app._cache_set("test:pune", enriched)
        self.assertEqual(pwa_app._cache_get("test:pune")["name"], "Pune")

    def test_pwa_asgi_static_routes(self):
        import anyio

        async def check_routes():
            for path in ("/", "/manifest.json", "/sw.js", "/icon.svg"):
                messages = []

                async def receive():
                    return {"type": "http.request", "body": b"", "more_body": False}

                async def send(msg):
                    messages.append(msg)

                scope = {
                    "type": "http",
                    "method": "GET",
                    "path": path,
                    "raw_path": path.encode(),
                    "query_string": b"",
                    "headers": [],
                }
                await pwa_app.app(scope, receive, send)
                self.assertEqual(messages[0]["status"], 200, path)

        anyio.run(check_routes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
