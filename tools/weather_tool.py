import logging
from typing import Optional
import requests
from . import register_tool
from config import Config

logger = logging.getLogger(__name__)

@register_tool
def get_weather(city: Optional[str] = None) -> str:
    """
    Get the current weather for a specific city using OpenWeatherMap API.
    If no city is provided or city is 'current', returns weather for the default city.
    Only accepts real city names as input.
    
    Args:
        city: The city name to get weather for (optional). Can be:
              - A specific city name
              - None (uses default city)
              - 'current' (uses default city)
        
    Returns:
        Weather information or error message
    """
    if not Config.OPENWEATHERMAP_API_KEY:
        return "Weather API is not configured"

    target_city = (city if city and city.lower() not in ["current", "current city", "my city"]
                  else Config.OPENWEATHERMAP_DEFAULT_CITY)
    
    if not target_city:
        return "No city specified and no default city configured"

    try:
        response = requests.get(
            "http://api.openweathermap.org/data/2.5/weather",
            params={
                "q": target_city,
                "appid": Config.OPENWEATHERMAP_API_KEY,
                "units": "metric"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']

        return (f"The weather in {target_city} is {temp}°C with {weather}. "
                f"Humidity is {humidity}%.")

    except requests.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        return f"Error getting weather: {str(e)}"
