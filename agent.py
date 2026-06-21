from google.genai import Client
from google.adk.agents.llm_agent import Agent
# from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.tools.example_tool import ExampleTool
from google.genai import types
import os
import json 
from typing import Optional
from datetime import datetime
import httpx

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "http://api.openweathermap.org/data/2.5/forecast"

FLIGHTS_JSON_PATH = "flights_dataset.json"
HOTELS_JSON_PATH = "mock_hotels.json"

with open(FLIGHTS_JSON_PATH, "r") as f:
    flights_data = json.load(f)

with open(HOTELS_JSON_PATH, "r") as f:
    hotels_data = json.load(f)

for hotel in hotels_data:
    hotel["city_normalized"] = hotel.get("city", "").lower()

example_tool = ExampleTool([
{
    "input": {
        "role": "user",
        "parts": [{"text": "I want to plan a trip to Paris."}],
    },
    "output": [
        {
            "role": "flight_agent",
            "parts": [{"text": "I found flights from New York to Paris on June 10th. The return flight is available on June 15th."}],
        },
        {
            "role": "hotel_agent",
            "parts": [{"text": "In Paris, you can stay at Hotel Lumiere for $120 per night or Eiffel Stay for $95 per night."}],
        },
        {
            "role": "attractions_agent",
            "parts": [{"text": "Some must-see attractions include the Eiffel Tower, Louvre Museum, and Seine River cruise."}],
        },
        {
            "role": "root_agent",
            "parts": [{"text": "Here’s a draft plan: Fly from New York to Paris on June 10th, stay at Hotel Lumiere or Eiffel Stay, and explore the Eiffel Tower, Louvre, and Seine cruise. Your return flight is on June 15th. Would you like me to finalize this plan?"}],
        },
    ],
},
{
    "input": {
        "role": "user",
        "parts": [{"text": "Can you suggest a hotel near the Eiffel Tower?"}],
    },
    "output": [
        {
            "role": "hotel_agent",
            "parts": [{"text": "Eiffel Stay is a great choice—it’s close to the Eiffel Tower, rated 4.0, and priced at $95 per night."}],
        },
        {
            "role": "root_agent",
            "parts": [{"text": "I recommend Eiffel Stay since it balances affordability and location. Do you want me to add this to your trip plan?"}],
        },
    ],
},
{
    "input": {
        "role": "user",
        "parts": [{"text": "What can I do on day 2 of my trip?"}],
    },
    "output": [
        {
            "role": "attractions_agent",
            "parts": [{"text": "On day 2, you could visit the Louvre Museum in the morning and enjoy a Seine River cruise in the evening."}],
        },
        {
            "role": "root_agent",
            "parts": [{"text": "That sounds like a great day! I’ll add Louvre in the morning and a Seine cruise in the evening to your itinerary."}],
        },
    ],
},
{
    "input": {
        "role": "user",
        "parts": [{"text": "Book me a return flight to New York."}],
    },
    "output": [
        {
            "role": "flight_agent",
            "parts": [{"text": "Your return flight from Paris to New York is scheduled for June 15th at 3:00 PM."}],
        },
        {
            "role": "root_agent",
            "parts": [{"text": "Your trip is now confirmed with a return flight on June 15th. Do you want me to summarize the full itinerary?"}],
        },
    ],
},
{
    "input": {
        "role": "user",
        "parts": [{"text": "Plan a full trip to Paris from New York, including flights, hotels, weather, and attractions."}],
    },
    "output": [
        {
            "role": "flight_agent",
            "parts": [{"text": "I found flights from New York to Paris on June 10th. Return flights are available on June 15th."}],
        },
        {
            "role": "hotel_agent",
            "parts": [{"text": "For Paris, you can stay at Hotel Lumiere for $120 per night or Eiffel Stay for $95 per night."}],
        },
        {
            "role": "weather_agent",
            "parts": [{"text": "The forecast for Paris from June 10 to June 15 is: June 10: Sunny (High: 25°C, Low: 15°C), June 11: Light Rain (High: 22°C, Low: 14°C), June 12: Cloudy (High: 23°C, Low: 16°C), June 13: Sunny (High: 24°C, Low: 15°C), June 14: Partly Cloudy (High: 23°C, Low: 14°C), June 15: Sunny (High: 25°C, Low: 16°C)."}],
        },
        {
            "role": "attractions_agent",
            "parts": [{"text": "Suggested attractions include the Eiffel Tower, Louvre Museum, Notre Dame, and a Seine River cruise."}],
        },
        {
            "role": "root_agent",
            "parts": [{"text": "Here’s your complete trip plan: Fly from New York to Paris on June 10, stay at Hotel Lumiere or Eiffel Stay, enjoy the attractions and local weather-aware activities, and return to New York on June 15. Do you want me to finalize this itinerary?"}],
        },
    ],
},

])

def query_flights(dep_city=None, arr_city=None, date=None, start_date=None, end_date=None, month=None):
  results = []
  for flight in flights_data:
    dep_time_str=flight["departure_time"]
    try:
        dep_time = datetime.strptime(dep_time_str + "2025", "%m-%d %H:%M-%Y")
    except ValueError:
        continue

    # filter by city names (case-insensitive)    
    if dep_city and flight.get("departure_city", "").lower() != dep_city.lower():
        continue
    if arr_city and flight.get("arrival_city", "").lower() != arr_city.lower():
        continue
    
    # Filter by date

    if start_date and end_date:
        try: 
            start = datetime.strptime(start_date + "-2025", "%m-%d-%Y")
            end = datetime.strptime(end_date +"-2025", "%m-%d-%Y")
        except ValueError:
            continue
        if not (start <= dep_time <= end):
            continue
        
    if month:
        if dep_time.month !=month:
            continue
        
    results.append(flight)
  return results

def query_flights_simple(dep_city: str="", arr_city: str="", date: str="") -> list:
    dep_city = dep_city or None
    arr_city = arr_city or None
    date = date or None
    return query_flights(dep_city=dep_city, arr_city=arr_city, date=date)
    
def query_hotels(
        city: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
):
    results = []
    for hotel in hotels_data:
        if city and city.lower() not in hotel.get("city_normalized", ""):
            continue
        if min_rating and hotel.get("rating", 0) < min_rating:
            continue
        if max_price and hotel.get("price_per_night", float('inf')) > max_price:
            continue
        results.append(hotel)
    return results

async def get_weather(location: str) -> str:
  if not OPENWEATHER_API_KEY:
      return "OpenWeather API key not configured."
  
  async with httpx.AsyncClient() as client:
      params = { 
          "q": location,
          "appid": OPENWEATHER_API_KEY,
          "units": "metric"
      }

      try: 
          response = await client.get(BASE_URL, params=params)
          response.raise_for_status()
          data = response.json()
      except httpx.HTTPStatusError as e:
          return f"Error fetching weather data: {str(e)}"
      except httpx.RequestError as e:
          return f"Network error while fetching weather data: {str(e)}"
      except json.JSONDecodeError:
          return "Error decoding weather data response."
      
  daily_forecasts = {}

  for item in data.get("list",[]):
      date_str = item["dx_txt"].split(' ')[0]
      temp = item["main"]["temp"]
      weather_description = item["weather"][0]["description"]

      if date_str not in daily_forecasts:
        # Initialize with first temperature as min/max
        daily_forecasts[date_str] = {
            "min_temp": temp,
            "max_temp": temp,
            "weather": weather_description,
            "count": 1
        }
      else:
        # Update min/max temperatures
        daily_forecasts[date_str]["min_temp"] = min(daily_forecasts[date_str]["min_temp"], temp)
        daily_forecasts[date_str]["max_temp"] = max(daily_forecasts[date_str]["max_temp"], temp)
        # Simplistic way to get the "main" weather for the day (last update wins)
        daily_forecasts[date_str]["weather"] = weather_description
        daily_forecasts[date_str]["count"] += 1 
        
  summary = []
  for date, daily_data in daily_forecasts.items():
      summary.append(
          f"{date}: {daily_data['weather'].capitalize()} (High: {daily_data['max_temp']:.1f}°C, Low: {daily_data['min_temp']:.1f}°C)"
      )
  
  if not summary:
      return f"Could not find a forecast for {location}. Please check the location spelling."

  return f"Multiday Weather Forecast for {location}:\n- " + "\n- ".join(summary)

# AGENTS
attractions_agent = Agent(
  model="gemini-2.5-flash",
  name="attractions_agent",
  description="Provides tourist attractions info for a given city.",
  instruction="""
    You are resposible for suggesting popular tourist attractions, stightseeing spots, and local activities for the given city.
    provide concise and relevant recommendations to help the user plan their trip.
  """,
  generate_content_config=types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
          category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
          threshold=types.HarmBlockThreshold.OFF,
        ),
      ]
    ),
)

flight_agent = Agent(
  model="gemini-2.5-flash",
  name="flight_agent",
  description="Provides flight information from the mock flight database using city names.",
  instruction="""
    You are a Flight Information agent. When asked for flights between cities on a certain date, 
    query the mock flight dataset and provide a clear summary of matching flights,
    including airline, flight number, departure/arrival cities and times, and status.
    If no flights match, politely tell the user that no flights were found.
    Assume the user provides city names, not airport codes.
  """,
  tools=[query_flights_simple],
  generate_content_config=types.GenerateContentConfig(
      safety_settings=[
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
              threshold=types.HarmBlockThreshold.OFF,
          ),
      ]
  ),
)

hotel_agent = Agent(
  model="gemini-2.5-flash",
  name="hotel_agent",
  description="Provides hotel information for a city using mock hotel database.",
  instruction="""
    You are a Hotel Information agent. When asked about hotels in a city, 
    use the hotel dataset to provide a clear summary including hotel names, ratings, and prices.
    You can optionally consider user's preferences for minimum rating or maximum price.
    Assume all hotels have room availability.
    If no hotels match, politely inform the user.
  """,
  tools=[query_hotels],
  generate_content_config=types.GenerateContentConfig(
      safety_settings=[
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
              threshold=types.HarmBlockThreshold.OFF
          ),
      ]
  ),
)

weather_agent = Agent(
  model='gemini-2.5-flash',
  name="weather_agent",
  description="Provides weather forecasts for a destination using OpenWeatherMap.",
  instruction="Answer weather-related questions using the get_weather tool. If the learner does not specifies the number of days for forecast, you'll usually respond with the forecast for the next 5 days.",
  tools=[get_weather],
  generate_content_config=types.GenerateContentConfig(
      safety_settings=[
          types.SafetySetting(
              category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
              threshold=types.HarmBlockThreshold.OFF,
          ),
      ]
  ),
)

# weather_agent = RemoteA2aAgent(
#     name="weather_agent",
#     description="Provides weather info for a given city.",
#     agent_card=os.path.join(    
#         os.path.dirname(__file__), "agents", "weather_agent", "agent.json"
#     ),
# )

# --- Root Agent ---
root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    instruction="""
        You are TravelPlannerBot.
        When the user asks to plan a trip, you should:

        1. Determine the trip details: departure city, arrival city, dates.
        2. Call flight_agent to find flights.
        3. Call hotel_agent to find hotels for the destination city and dates.
        4. Call weather_agent to get weather forecasts for the destination during the trip.
        5. Call attractions_agent to suggest attractions based on city and weather.
        
        Always consolidate results and present a single, coherent plan to the user.
        Do not ask the user for airport codes; use city names only.
        Use sub-agent outputs internally; do not require the user to call each agent.
        Only ask the user clarifying questions if essential information is missing.
    """,
    global_instruction="You are TravelPlannerBot, ready to autonomously plan trips using your sub-agents.",
    sub_agents=[flight_agent, hotel_agent, weather_agent, attractions_agent],
    tools=[example_tool],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ]
    ),
)