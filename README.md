# Weather Agent with OpenAI

A small, beginner-friendly Python project that shows how to use an OpenAI model as an agent. The complete example lives in one readable Python file.

The user enters a city, the model chooses a weather tool, the app fetches live weather data, and the model turns that data into a natural answer.

## Why this example is useful

- Easy to read
- Cheap to run
- Uses a real tool-calling flow
- Good starting point for bigger agent projects

## What this project does

1. Prompts the user for a city
2. Sends the request to an OpenAI model
3. Lets the model call a custom `get_weather` tool
4. Uses Open-Meteo to fetch live weather data
5. Returns a short weather summary to the user

## Project files

- `main.py` contains the full agent example
- `.env.example` shows the environment variables you need
- `requirements.txt` lists the Python packages

## Default model

This project uses `gpt-5-nano` by default because it is a low-cost choice for a simple tool-calling demo.

If you want a stronger model later, update `OPENAI_MODEL` in `.env`. A good next step is `gpt-5.6-luna`.

## Setup

1. Create a virtual environment if you want one:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Open `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-5-nano
```

## Run the app

```bash
python3 main.py
```

Example:

```text
Enter a city: Toronto

It is currently 24C and partly cloudy in Toronto, Ontario, Canada.
```

## How the agent works

The model does not fetch weather directly. Instead, the app uses one simple tool-calling round trip:

1. Send the city and weather tool to the model
2. Run `get_weather` with the city chosen by the model
3. Send the weather result back to the model
4. Print the model's short answer

## Notes

- Weather data comes from the free Open-Meteo API
- The app uses `.env` for local configuration
- `.env` is ignored by Git so your real API key is not committed

## Ideas for next improvements

- Add a multi-city forecast mode
- Save recent searches
- Add a web interface with Flask or FastAPI
- Show temperatures in both Celsius and Fahrenheit
