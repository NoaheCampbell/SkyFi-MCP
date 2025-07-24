"""Handlers for weather tool calls."""
import logging
from typing import Any, Dict, List

from mcp.types import TextContent

logger = logging.getLogger(__name__)


async def handle_weather_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle weather tool calls."""
    # For now, return mock data since weather API requires separate API key
    # In production, this would use a real weather API
    
    try:
        if name == "weather_current":
            location = arguments.get("location")
            if not location:
                lat, lon = arguments.get("lat"), arguments.get("lon")
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
            if not location:
                lat, lon = arguments.get("lat"), arguments.get("lon")
                location = f"{lat}, {lon}"
            
            days = arguments.get("days", 3)
            
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