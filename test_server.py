#!/usr/bin/env python3
"""Test script for MCP SkyFi server."""
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta

# Add src to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from mcp_skyfi.skyfi.client import SkyFiClient
from mcp_skyfi.osm.handlers import handle_osm_tool
from mcp_skyfi.weather.handlers import handle_weather_tool


async def test_skyfi_api():
    """Test SkyFi API functionality."""
    print("Testing SkyFi API...")
    
    try:
        async with SkyFiClient() as client:
            # Test user info
            print("\n1. Getting user info...")
            user = await client.get_user()
            print(f"   User: {user.get('email', 'Unknown')}")
            print(f"   Account Type: {user.get('accountType', 'Unknown')}")
            
            # Test search
            print("\n2. Searching for imagery...")
            # Small area in NYC for testing
            test_polygon = "POLYGON((-74.006 40.7128, -74.005 40.7128, -74.005 40.7138, -74.006 40.7138, -74.006 40.7128))"
            
            results = await client.search_archives(
                aoi=test_polygon,
                from_date=(datetime.now() - timedelta(days=30)).isoformat() + "Z",
                to_date=datetime.now().isoformat() + "Z",
                open_data=True
            )
            
            print(f"   Found {len(results.get('results', []))} images")
            if results.get('results'):
                first = results['results'][0]
                print(f"   Latest: {first.get('captureDate', 'N/A')} - {first.get('satellite', 'N/A')}")
    
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure SKYFI_API_KEY is set in your environment or .env file")


async def test_osm_tools():
    """Test OpenStreetMap tools."""
    print("\n\nTesting OpenStreetMap tools...")
    
    # Test geocoding
    print("\n1. Geocoding 'Empire State Building'...")
    result = await handle_osm_tool("osm_geocode", {"query": "Empire State Building, New York"})
    print(f"   {result[0].text[:200]}...")
    
    # Test reverse geocoding
    print("\n2. Reverse geocoding coordinates...")
    result = await handle_osm_tool("osm_reverse_geocode", {"lat": 40.7484, "lon": -73.9857})
    print(f"   {result[0].text[:200]}...")
    
    # Test polygon conversion
    print("\n3. Getting WKT polygon for Manhattan...")
    result = await handle_osm_tool("osm_polygon_to_wkt", {"place": "Manhattan, New York"})
    print(f"   {result[0].text[:200]}...")


async def test_weather_tools():
    """Test weather tools."""
    print("\n\nTesting Weather tools...")
    
    # Test current weather
    print("\n1. Getting current weather...")
    result = await handle_weather_tool("weather_current", {"location": "San Francisco, CA"})
    print(f"   {result[0].text}")
    
    # Test forecast
    print("\n2. Getting weather forecast...")
    result = await handle_weather_tool("weather_forecast", {"location": "New York, NY", "days": 3})
    print(f"   {result[0].text}")


async def main():
    """Run all tests."""
    print("MCP SkyFi Server Test Suite")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run tests
    await test_skyfi_api()
    await test_osm_tools()
    await test_weather_tools()
    
    print("\n" + "=" * 50)
    print("Testing complete!")
    print("\nTo use with Claude Desktop:")
    print("1. Copy the configuration from README.md to your claude_desktop_config.json")
    print("2. Replace 'your-skyfi-api-key-here' with your actual API key")
    print("3. Restart Claude Desktop")


if __name__ == "__main__":
    asyncio.run(main())