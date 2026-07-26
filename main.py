from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


DEFAULT_MODEL = "gpt-5-nano"
MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
AGENT_INSTRUCTIONS = (
    "You are a small weather assistant. "
    "Always use the get_weather tool for weather questions. "
    "Keep the final answer short, clear, and friendly. "
    "Mention the city, current temperature in C, and the weather condition."
)

WEATHER_TOOL = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the current weather for a city entered by the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to look up, for example Toronto or Cairo.",
                }
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    }
]

WEATHER_CODES = {
    0: "clear sky",
    1: "mostly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    56: "light freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "rain showers",
    82: "heavy rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with light hail",
    99: "thunderstorm with heavy hail",
}


def require_api_key() -> None:
    if os.getenv("OPENAI_API_KEY"):
        return

    raise RuntimeError(
        "OPENAI_API_KEY is missing. Add your key to the .env file before running the app."
    )


def read_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "weather-agent-example/1.0"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def find_city(city: str) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
        }
    )
    data = read_json(f"https://geocoding-api.open-meteo.com/v1/search?{query}")
    results = data.get("results") or []

    if not results:
        return None

    best_match = results[0]
    parts = [best_match.get("name"), best_match.get("admin1"), best_match.get("country")]
    label = ", ".join(part for part in parts if part)

    return {
        "label": label,
        "latitude": best_match["latitude"],
        "longitude": best_match["longitude"],
    }


def get_weather(city: str) -> dict[str, Any]:
    try:
        place = find_city(city)
        if place is None:
            return {"error": f"Could not find a city named '{city}'."}

        query = urllib.parse.urlencode(
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,apparent_temperature,wind_speed_10m,weather_code",
                "timezone": "auto",
            }
        )
        data = read_json(f"https://api.open-meteo.com/v1/forecast?{query}")
        current = data.get("current") or {}

        if not current:
            return {"error": "Weather data was not available for that city."}

        return {
            "city": place["label"],
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "wind_kph": current.get("wind_speed_10m"),
            "condition": WEATHER_CODES.get(current.get("weather_code"), "unknown"),
        }
    except Exception as error:
        return {"error": f"Unable to fetch weather right now: {error}"}


def build_tool_outputs(response: Any) -> list[dict[str, str]]:
    tool_outputs: list[dict[str, str]] = []

    for item in response.output:
        if getattr(item, "type", "") != "function_call":
            continue

        arguments = json.loads(item.arguments)
        result = get_weather(arguments["city"])
        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result),
            }
        )

    return tool_outputs


def ask_weather_agent(city: str) -> str:
    require_api_key()
    client = OpenAI()

    response = client.responses.create(
        model=MODEL,
        instructions=AGENT_INSTRUCTIONS,
        input=f"What is the weather in {city}?",
        max_output_tokens=160,
        tools=WEATHER_TOOL,
    )

    while True:
        tool_outputs = build_tool_outputs(response)
        if not tool_outputs:
            return response.output_text.strip()

        response = client.responses.create(
            model=MODEL,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=WEATHER_TOOL,
        )


def main() -> None:
    try:
        city = input("Enter a city: ").strip()
        if not city:
            print("Please enter a city name.")
            return

        print()
        print(ask_weather_agent(city))
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
