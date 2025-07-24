#!/usr/bin/env python3
"""Example: Search for satellite imagery of a location."""
import asyncio
from datetime import datetime, timedelta

from mcp_skyfi.skyfi.client import SkyFiClient
from mcp_skyfi.osm.handlers import handle_osm_tool


async def search_satellite_imagery():
    """Example workflow: Search for satellite images of Central Park."""
    
    # Step 1: Get the polygon for Central Park
    print("Step 1: Getting boundary polygon for Central Park...")
    osm_result = await handle_osm_tool(
        "osm_polygon_to_wkt", 
        {"place": "Central Park, Manhattan, New York"}
    )
    
    # Extract WKT from the result (this is simplified - in practice you'd parse properly)
    wkt_text = osm_result[0].text
    wkt_start = wkt_text.find("POLYGON")
    wkt_end = wkt_text.find("\n\n", wkt_start)
    wkt_polygon = wkt_text[wkt_start:wkt_end] if wkt_start != -1 else None
    
    if not wkt_polygon:
        print("Could not extract WKT polygon")
        return
    
    print(f"Found polygon: {wkt_polygon[:100]}...")
    
    # Step 2: Search for satellite imagery
    print("\nStep 2: Searching for satellite imagery...")
    
    async with SkyFiClient() as client:
        results = await client.search_archives(
            aoi=wkt_polygon,
            from_date=(datetime.now() - timedelta(days=90)).isoformat() + "Z",
            to_date=datetime.now().isoformat() + "Z",
            open_data=True,
            product_types=["DAY"],
            resolution="HIGH"
        )
        
        images = results.get("results", [])
        print(f"\nFound {len(images)} satellite images")
        
        # Display top 5 results
        for idx, img in enumerate(images[:5], 1):
            print(f"\n{idx}. Image Details:")
            print(f"   Archive ID: {img.get('archiveId', 'N/A')}")
            print(f"   Date: {img.get('captureDate', 'N/A')}")
            print(f"   Satellite: {img.get('satellite', 'N/A')}")
            print(f"   Resolution: {img.get('resolution', 'N/A')}m")
            print(f"   Cloud Cover: {img.get('cloudCover', 'N/A')}%")
            print(f"   Price: ${img.get('price', 'N/A')}")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the example
    asyncio.run(search_satellite_imagery())