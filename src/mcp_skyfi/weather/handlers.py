"""Handlers for weather tool calls."""
import logging
from typing import Any, Dict, List

from mcp.types import TextContent
from .client import WeatherClient

logger = logging.getLogger(__name__)


async def handle_weather_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle weather tool calls."""
    client = WeatherClient()
    
    try:
        if name == "weather_current":
            location = arguments.get("location")
            lat = arguments.get("lat")
            lon = arguments.get("lon")
            
            # Try to get real weather data
            if client.has_api_key():
                weather_data = await client.get_current_weather(location=location, lat=lat, lon=lon)
                if weather_data:
                    # Parse real weather data
                    main = weather_data.get('main', {})
                    weather = weather_data.get('weather', [{}])[0]
                    wind = weather_data.get('wind', {})
                    
                    response = f"""Current Weather for {weather_data.get('name', location or f'{lat}, {lon}')}:
Temperature: {main.get('temp', 'N/A')}°F ({round((main.get('temp', 72) - 32) * 5/9, 1)}°C)
Feels Like: {main.get('feels_like', 'N/A')}°F
Conditions: {weather.get('description', 'N/A').title()}
Humidity: {main.get('humidity', 'N/A')}%
Wind: {wind.get('speed', 'N/A')} mph {wind.get('deg', '')}
Pressure: {main.get('pressure', 'N/A')} hPa

🌡️ Min: {main.get('temp_min', 'N/A')}°F | Max: {main.get('temp_max', 'N/A')}°F"""
                    
                    return [TextContent(type="text", text=response)]
            
            # Fall back to mock data if no API key
            if not location:
                location = f"{lat}, {lon}"
            
            mock_response = f"""Current Weather for {location}:
Temperature: 72°F (22°C)
Conditions: Partly Cloudy
Humidity: 65%
Wind: 10 mph NW
Pressure: 30.15 in

Note: This is mock data. Configure WEATHER_API_KEY for real weather data."""
            
            return [TextContent(type="text", text=mock_response)]
        
        elif name == "weather_forecast":
            location = arguments.get("location")
            lat = arguments.get("lat")
            lon = arguments.get("lon")
            days = arguments.get("days", 3)
            
            # Try to get real forecast data
            if client.has_api_key():
                forecast_data = await client.get_forecast(location=location, lat=lat, lon=lon, days=days)
                if forecast_data and 'list' in forecast_data:
                    # Parse forecast data
                    city_name = forecast_data.get('city', {}).get('name', location or f'{lat}, {lon}')
                    forecasts = forecast_data['list']
                    
                    response = f"""Weather Forecast for {city_name} ({days} days):

"""
                    # Group forecasts by day
                    from datetime import datetime
                    daily_data = {}
                    
                    for forecast in forecasts:
                        date = datetime.fromtimestamp(forecast['dt']).strftime('%Y-%m-%d')
                        if date not in daily_data:
                            daily_data[date] = {
                                'temps': [],
                                'conditions': [],
                                'rain': False,
                                'snow': False
                            }
                        
                        daily_data[date]['temps'].append(forecast['main']['temp'])
                        daily_data[date]['conditions'].append(forecast['weather'][0]['description'])
                        
                        if 'rain' in forecast:
                            daily_data[date]['rain'] = True
                        if 'snow' in forecast:
                            daily_data[date]['snow'] = True
                    
                    # Display daily summaries
                    day_count = 0
                    for date, data in sorted(daily_data.items()):
                        if day_count >= days:
                            break
                        
                        day_count += 1
                        date_obj = datetime.strptime(date, '%Y-%m-%d')
                        day_name = date_obj.strftime('%A, %B %d')
                        
                        high_temp = max(data['temps'])
                        low_temp = min(data['temps'])
                        
                        # Get most common condition
                        condition_counts = {}
                        for cond in data['conditions']:
                            condition_counts[cond] = condition_counts.get(cond, 0) + 1
                        main_condition = max(condition_counts.items(), key=lambda x: x[1])[0]
                        
                        # Format precipitation
                        precip = []
                        if data['rain']:
                            precip.append('🌧️ Rain')
                        if data['snow']:
                            precip.append('❄️ Snow')
                        
                        response += f"""Day {day_count} - {day_name}:
  🌡️ High: {high_temp:.0f}°F | Low: {low_temp:.0f}°F
  ☁️ {main_condition.title()}"""
                        
                        if precip:
                            response += f"\n  💧 {', '.join(precip)}"
                        
                        response += "\n\n"
                    
                    return [TextContent(type="text", text=response.strip())]
            
            # Fall back to mock data if no API key
            if not location:
                location = f"{lat}, {lon}"
            
            mock_response = f"""Weather Forecast for {location} ({days} days):

Day 1: High 75°F, Low 60°F - Sunny
Day 2: High 73°F, Low 58°F - Partly Cloudy
Day 3: High 70°F, Low 55°F - Chance of Rain

Note: This is mock data. Configure WEATHER_API_KEY for real weather data."""
            
            return [TextContent(type="text", text=mock_response)]
        
        else:
            raise ValueError(f"Unknown weather tool: {name}")
    
    except Exception as e:
        logger.error(f"Error handling weather tool {name}: {e}")
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]