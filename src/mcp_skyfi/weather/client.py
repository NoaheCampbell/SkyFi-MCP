"""Weather API client using OpenWeatherMap."""
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class WeatherClient:
    """Client for OpenWeatherMap API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize weather client."""
        self.api_key = api_key or os.environ.get('WEATHER_API_KEY')
        self.base_url_25 = "https://api.openweathermap.org/data/2.5"
        self.base_url_30 = "https://api.openweathermap.org/data/3.0"
        
    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    async def get_current_weather(self, location: str = None, lat: float = None, lon: float = None) -> Dict[str, Any]:
        """Get current weather for a location."""
        if not self.has_api_key():
            return None
            
        async with httpx.AsyncClient() as client:
            params = {
                'appid': self.api_key,
                'units': 'imperial'  # Use Fahrenheit
            }
            
            if location:
                params['q'] = location
            elif lat is not None and lon is not None:
                params['lat'] = lat
                params['lon'] = lon
            else:
                raise ValueError("Either location or lat/lon required")
            
            try:
                response = await client.get(f"{self.base_url_25}/weather", params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Weather API error: {e}")
                return None
    
    async def get_forecast(self, location: str = None, lat: float = None, lon: float = None, days: int = 3) -> Dict[str, Any]:
        """Get weather forecast using 2.5 API."""
        if not self.has_api_key():
            return None
            
        async with httpx.AsyncClient() as client:
            params = {
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': min(days * 8, 40)  # API returns 3-hour intervals, max 40
            }
            
            if location:
                params['q'] = location
            elif lat is not None and lon is not None:
                params['lat'] = lat
                params['lon'] = lon
            else:
                raise ValueError("Either location or lat/lon required")
            
            try:
                response = await client.get(f"{self.base_url_25}/forecast", params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Weather API error: {e}")
                return None
    
    async def get_onecall(self, lat: float, lon: float, exclude: List[str] = None) -> Dict[str, Any]:
        """Get One Call API 3.0 data (current, minutely, hourly, daily, alerts)."""
        if not self.has_api_key():
            return None
            
        async with httpx.AsyncClient() as client:
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            if exclude:
                params['exclude'] = ','.join(exclude)
            
            try:
                response = await client.get(f"{self.base_url_30}/onecall", params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"One Call API error: {e}")
                return None