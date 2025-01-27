from tools import register_tool
import requests
from config import OPENWEATHERMAP_API_KEY, OPENWEATHERMAP_DEFAULT_CITY


@register_tool
def get_weather(city: str = None) -> str:
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
    if not OPENWEATHERMAP_API_KEY:
        return "Weather API is not configured. Please set OPENWEATHERMAP_API_KEY in .env file."

    # Handle "current city" requests
    if city is None or city.lower() in ["current", "current city", "my city"]:
        target_city = OPENWEATHERMAP_DEFAULT_CITY
        default_city_note = f" (using default city {OPENWEATHERMAP_DEFAULT_CITY})"
    else:
        target_city = city
        default_city_note = ""

    try:
        # Make API request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={target_city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        # Handle API errors
        if response.status_code != 200:
            error_msg = data.get('message', 'Unknown error')
            return f"Could not get weather for {target_city}: {error_msg}"

        # Extract weather data
        weather = data['weather'][0]['description']
        temp = data['main']['temp']
        humidity = data['main']['humidity']

        return (f"The weather in {target_city}{default_city_note} is {temp}°C with {weather}. "
                f"Humidity is {humidity}%.")

    except Exception as e:
        return f"Error getting weather: {str(e)}"
