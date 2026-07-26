import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "gpt-5-nano")
INSTRUCTIONS = (
    "You are a friendly weather assistant. Always use the weather tool. "
    "Give a short answer with the city, temperature in Celsius, and condition."
)

WEATHER_TOOL = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "A city name, such as Toronto or Cairo.",
            }
        },
        "required": ["city"],
        "additionalProperties": False,
    },
}


def get_json(url, params):
    """Fetch JSON from a public API."""
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "weather-agent-example/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def describe_weather(code):
    """Turn an Open-Meteo weather code into plain English."""
    if code == 0:
        return "clear sky"
    if code in (1, 2):
        return "partly cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57):
        return "drizzle"
    if code in (61, 63, 65, 66, 67):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (80, 81, 82):
        return "rain showers"
    if code in (95, 96, 99):
        return "thunderstorm"
    return "unknown conditions"


def get_weather(city):
    """Look up a city and return its current weather."""
    try:
        places = get_json(
            "https://geocoding-api.open-meteo.com/v1/search",
            {"name": city, "count": 1, "language": "en", "format": "json"},
        ).get("results", [])

        if not places:
            return {"error": f"Could not find a city named '{city}'."}

        place = places[0]
        current = get_json(
            "https://api.open-meteo.com/v1/forecast",
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code",
                "timezone": "auto",
            },
        ).get("current", {})

        if not current:
            return {"error": "Current weather is not available for that city."}

        city_name = ", ".join(
            value
            for value in (place.get("name"), place.get("admin1"), place.get("country"))
            if value
        )
        return {
            "city": city_name,
            "temperature_c": current.get("temperature_2m"),
            "condition": describe_weather(current.get("weather_code")),
        }
    except Exception as error:
        return {"error": f"Unable to fetch weather right now: {error}"}


def ask_weather_agent(city):
    """Let the model call the weather tool, then write the final answer."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise RuntimeError("Add your OpenAI API key to the .env file first.")

    client = OpenAI()
    response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        input=f"What is the weather in {city}?",
        tools=[WEATHER_TOOL],
        max_output_tokens=160,
    )

    tool_call = next(
        (item for item in response.output if item.type == "function_call"),
        None,
    )
    if tool_call is None:
        return response.output_text.strip()

    arguments = json.loads(tool_call.arguments)
    weather = get_weather(arguments["city"])

    final_response = client.responses.create(
        model=MODEL,
        instructions=INSTRUCTIONS,
        previous_response_id=response.id,
        input=[
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": json.dumps(weather),
            }
        ],
        tools=[WEATHER_TOOL],
        max_output_tokens=160,
    )
    return final_response.output_text.strip()


def main():
    try:
        city = input("Enter a city: ").strip()
        if not city:
            print("Please enter a city name.")
            return

        print(f"\n{ask_weather_agent(city)}")
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as error:
        print(f"Error: {error}")


if __name__ == "__main__":
    main()
