#!/usr/bin/env python3
"""
Web-based demo for SkyFi MCP Server

Run this to start a local web server with an interactive demo UI.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.mcp_skyfi.osm.handlers import handle_osm_tool
from src.mcp_skyfi.weather.handlers import handle_weather_tool
from src.mcp_skyfi.skyfi.handlers import handle_skyfi_tool

# Load environment variables
def load_env():
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)
    except ImportError:
        pass

load_env()

app = FastAPI(title="SkyFi MCP Demo")

# HTML template for the demo
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyFi MCP Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        }
        .tool-card {
            transition: all 0.3s ease;
        }
        .tool-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        #map { 
            height: 400px; 
            cursor: crosshair;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <header class="gradient-bg text-white shadow-lg">
        <div class="container mx-auto px-6 py-6">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold">🛰️ SkyFi MCP Demo</h1>
                    <p class="text-blue-200 mt-1">Interactive Geospatial Intelligence Platform</p>
                </div>
                <div class="text-right">
                    <div id="api-status" class="text-sm">
                        <span class="inline-block w-3 h-3 bg-green-400 rounded-full mr-2"></span>
                        <span id="skyfi-status">SkyFi API: Connected</span>
                    </div>
                    <div class="text-sm mt-1">
                        <span class="inline-block w-3 h-3 bg-green-400 rounded-full mr-2"></span>
                        <span id="weather-status">Weather API: Connected</span>
                    </div>
                </div>
            </div>
        </div>
    </header>

    <div class="container mx-auto px-6 py-8">
        <!-- Tool Categories -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="tool-card bg-white rounded-lg shadow-md p-6">
                <h3 class="text-xl font-semibold mb-2 text-blue-600">🗺️ OpenStreetMap Tools</h3>
                <p class="text-gray-600 text-sm mb-3">8 tools for geocoding and mapping</p>
                <ul class="text-sm space-y-1">
                    <li>• Geocoding & reverse geocoding</li>
                    <li>• Area of interest generation</li>
                    <li>• Polygon validation</li>
                </ul>
            </div>
            
            <div class="tool-card bg-white rounded-lg shadow-md p-6">
                <h3 class="text-xl font-semibold mb-2 text-green-600">🛰️ SkyFi Satellite Tools</h3>
                <p class="text-gray-600 text-sm mb-3">20+ tools for satellite imagery</p>
                <ul class="text-sm space-y-1">
                    <li>• Archive search & ordering</li>
                    <li>• Cost optimization</li>
                    <li>• Satellite tasking</li>
                </ul>
            </div>
            
            <div class="tool-card bg-white rounded-lg shadow-md p-6">
                <h3 class="text-xl font-semibold mb-2 text-yellow-600">🌤️ Weather & Safety</h3>
                <p class="text-gray-600 text-sm mb-3">5+ tools for conditions & limits</p>
                <ul class="text-sm space-y-1">
                    <li>• Weather forecasting</li>
                    <li>• Capture feasibility</li>
                    <li>• Spending guardrails</li>
                </ul>
            </div>
        </div>

        <!-- Interactive Demo Section -->
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-bold mb-6">🎯 Interactive Demo</h2>
            
            <!-- Location Search -->
            <div class="mb-6">
                <label class="block text-sm font-medium text-gray-700 mb-2">Search Location</label>
                <div class="flex gap-2">
                    <input 
                        type="text" 
                        id="location-input" 
                        class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Enter a location (e.g., Times Square, New York)"
                        value="Central Park, New York"
                    >
                    <button 
                        onclick="analyzeLocation()" 
                        class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                        Analyze
                    </button>
                </div>
                <p class="text-xs text-gray-500 mt-1">💡 Tip: Click anywhere on the map to drop a pin and analyze that location</p>
            </div>

            <!-- Map -->
            <div id="map" class="rounded-lg mb-6"></div>

            <!-- Results Section -->
            <div id="results" class="space-y-6">
                <!-- Results will be inserted here -->
            </div>
        </div>

        <!-- Live Activity Feed -->
        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-2xl font-bold mb-4">📊 Live Activity Feed</h2>
            <div id="activity-feed" class="space-y-2 max-h-64 overflow-y-auto">
                <div class="text-gray-500 text-sm">Waiting for activity...</div>
            </div>
        </div>
    </div>

    <script>
        // Initialize map
        const map = L.map('map').setView([40.7128, -74.0060], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        let currentMarker = null;
        let currentPolygon = null;
        let ws = null;
        
        // Add click handler to map
        map.on('click', function(e) {
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;
            
            // Place marker
            if (currentMarker) map.removeLayer(currentMarker);
            currentMarker = L.marker([lat, lon]).addTo(map);
            
            // Update input field
            document.getElementById('location-input').value = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
            
            // Trigger analysis
            analyzeLocation();
        });

        // Connect WebSocket
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleResponse(data);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }

        // Add activity to feed
        function addActivity(message, type = 'info') {
            const feed = document.getElementById('activity-feed');
            const timestamp = new Date().toLocaleTimeString();
            const color = type === 'success' ? 'text-green-600' : type === 'error' ? 'text-red-600' : 'text-gray-600';
            
            const entry = document.createElement('div');
            entry.className = `flex items-center gap-2 p-2 rounded ${type === 'success' ? 'bg-green-50' : type === 'error' ? 'bg-red-50' : 'bg-gray-50'}`;
            entry.innerHTML = `
                <span class="text-xs text-gray-500">${timestamp}</span>
                <span class="${color} text-sm flex-1">${message}</span>
            `;
            
            feed.insertBefore(entry, feed.firstChild);
            
            // Keep only last 20 entries
            while (feed.children.length > 20) {
                feed.removeChild(feed.lastChild);
            }
        }

        // Analyze location
        async function analyzeLocation() {
            const location = document.getElementById('location-input').value;
            if (!location) return;
            
            document.getElementById('results').innerHTML = '<div class="text-center"><div class="loader"></div><p class="mt-2 text-gray-600">Analyzing location...</p></div>';
            
            addActivity(`🔍 Starting analysis for: ${location}`, 'info');
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({location})
                });
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                console.error('Error:', error);
                addActivity('❌ Analysis failed', 'error');
            }
        }

        // Display results
        function displayResults(data) {
            const resultsDiv = document.getElementById('results');
            
            if (data.error) {
                resultsDiv.innerHTML = `<div class="bg-red-50 p-4 rounded-lg text-red-700">${data.error}</div>`;
                return;
            }
            
            // Update map
            if (data.coordinates) {
                const {lat, lon} = data.coordinates;
                map.setView([lat, lon], 13);
                
                if (currentMarker) map.removeLayer(currentMarker);
                currentMarker = L.marker([lat, lon]).addTo(map)
                    .bindPopup(data.location_name || 'Selected Location')
                    .openPopup();
                
                // Add AOI polygon if available
                if (data.aoi_bounds) {
                    if (currentPolygon) map.removeLayer(currentPolygon);
                    currentPolygon = L.rectangle(data.aoi_bounds, {
                        color: '#3b82f6',
                        weight: 2,
                        fillOpacity: 0.1
                    }).addTo(map);
                }
            }
            
            // Build results HTML
            let html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-6">';
            
            // Location info
            if (data.location_info) {
                html += `
                    <div class="bg-blue-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-blue-800 mb-2">📍 Location Details</h3>
                        <p class="text-sm">${data.location_info}</p>
                        ${data.coordinates ? `<p class="text-xs text-gray-600 mt-1">Coordinates: ${data.coordinates.lat.toFixed(4)}, ${data.coordinates.lon.toFixed(4)}</p>` : ''}
                    </div>
                `;
            }
            
            // Weather info
            if (data.weather) {
                html += `
                    <div class="bg-green-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-green-800 mb-2">🌤️ Weather Conditions</h3>
                        <p class="text-sm">${data.weather}</p>
                    </div>
                `;
            }
            
            // Satellite imagery
            if (data.imagery) {
                // Escape any backticks and dollar signs in the imagery data
                const escapedImagery = data.imagery.replace(/[`$]/g, '\\$&');
                // Convert newlines to <br> for proper display
                const imageryHtml = escapedImagery.replace(/\\n/g, '<br>');
                html += `
                    <div class="bg-purple-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-purple-800 mb-2">🛰️ Satellite Imagery</h3>
                        <div class="text-sm space-y-1 mb-4">${imageryHtml}</div>
                `;
                
                // Add thumbnails if available
                if (data.thumbnails && data.thumbnails.length > 0) {
                    html += `<div class="grid grid-cols-2 md:grid-cols-3 gap-2 mt-4">`;
                    data.thumbnails.forEach(thumb => {
                        const date = new Date(thumb.date).toLocaleDateString() || 'N/A';
                        html += `
                            <div class="relative group cursor-pointer">
                                <img src="${thumb.url}" alt="Satellite image ${thumb.id}" 
                                     class="w-full h-32 object-cover rounded-lg shadow-md hover:shadow-lg transition-shadow">
                                <div class="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-1 rounded-b-lg opacity-0 group-hover:opacity-100 transition-opacity">
                                    <div>ID: ${thumb.id.substring(0, 8)}...</div>
                                    <div>Date: ${date}</div>
                                    <div>Clouds: ${thumb.clouds.toFixed(0)}%</div>
                                </div>
                            </div>
                        `;
                    });
                    html += `</div>`;
                }
                
                html += `</div>`;
            }
            
            // Cost info
            if (data.cost_info) {
                html += `
                    <div class="bg-yellow-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-yellow-800 mb-2">💰 Cost Analysis</h3>
                        <p class="text-sm">${data.cost_info}</p>
                    </div>
                `;
            }
            
            html += '</div>';
            
            // Recommendations
            if (data.recommendations && data.recommendations.length > 0) {
                html += `
                    <div class="mt-6 bg-gray-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-gray-800 mb-2">💡 Recommendations</h3>
                        <ul class="space-y-1">
                            ${data.recommendations.map(rec => `<li class="text-sm">• ${rec}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            resultsDiv.innerHTML = html;
            addActivity('✅ Analysis complete!', 'success');
        }

        // Handle WebSocket responses
        function handleResponse(data) {
            if (data.type === 'activity') {
                addActivity(data.message, data.level || 'info');
            }
        }

        // Initialize
        connectWebSocket();
        
        // Check API status
        fetch('/status').then(r => r.json()).then(data => {
            document.getElementById('skyfi-status').textContent = `SkyFi API: ${data.skyfi ? 'Connected' : 'No API Key'}`;
            document.getElementById('weather-status').textContent = `Weather API: ${data.weather ? 'Connected' : 'Using Mock Data'}`;
            
            if (!data.skyfi) {
                document.querySelector('#skyfi-status').previousElementSibling.className = 'inline-block w-3 h-3 bg-yellow-400 rounded-full mr-2';
            }
        });
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE

@app.get("/status")
async def status():
    return {
        "skyfi": bool(os.getenv("SKYFI_API_KEY")),
        "weather": bool(os.getenv("WEATHER_API_KEY"))
    }

@app.post("/analyze")
async def analyze_location(request: Request):
    """Analyze a location using MCP tools."""
    data = await request.json()
    location = data.get("location", "")
    
    if not location:
        return {"error": "No location provided"}
    
    results = {}
    
    # Import the client directly for raw API access
    from src.mcp_skyfi.skyfi.client import SkyFiClient
    
    try:
        # Step 1: Geocode or parse coordinates
        # Check if location is coordinates (lat, lon format)
        if ',' in location and all(part.replace('.', '').replace('-', '').strip().isdigit() for part in location.split(',')):
            try:
                lat_str, lon_str = location.split(',')
                lat = float(lat_str.strip())
                lon = float(lon_str.strip())
                results["coordinates"] = {"lat": lat, "lon": lon}
                results["location_info"] = f"Coordinates: {lat:.6f}, {lon:.6f}"
                
                # Reverse geocode to get location name
                reverse_result = await handle_osm_tool("osm_reverse_geocode", {
                    "lat": lat,
                    "lon": lon
                })
                
                if reverse_result and len(reverse_result) > 0:
                    text = reverse_result[0].text
                    lines = text.split('\n')
                    if len(lines) > 0:
                        results["location_info"] = lines[0].strip()
            except:
                pass
        else:
            # Regular geocoding for text locations
            geocode_result = await handle_osm_tool("osm_geocode", {
                "query": location,
                "limit": 1
            })
            
            if geocode_result and len(geocode_result) > 0:
                text = geocode_result[0].text
                # Parse the text response (simplified parsing)
                lines = text.split('\n')
                if len(lines) > 2:
                    results["location_info"] = lines[2].strip()
                    # Extract coordinates from the text
                    for line in lines:
                        if "Lat:" in line and "Lon:" in line:
                            parts = line.split(',')
                            lat_part = parts[0].split(':')[-1].strip()
                            lon_part = parts[1].split(':')[-1].strip()
                            try:
                                lat = float(lat_part)
                                lon = float(lon_part)
                                results["coordinates"] = {"lat": lat, "lon": lon}
                                
                                # Generate simple AOI bounds
                                offset = 0.02  # ~2km
                                results["aoi_bounds"] = [
                                    [lat - offset, lon - offset],
                                    [lat + offset, lon + offset]
                                ]
                            except:
                                pass
        
        # Step 2: Weather (if we have coordinates)
        if "coordinates" in results:
            weather_result = await handle_weather_tool("weather_current", {
                "lat": results["coordinates"]["lat"],
                "lon": results["coordinates"]["lon"]
            })
            
            if weather_result and len(weather_result) > 0:
                weather_text = weather_result[0].text
                # Extract key weather info
                lines = weather_text.split('\n')
                weather_info = []
                for line in lines[1:6]:  # Get first few lines
                    if line.strip() and ':' in line:
                        weather_info.append(line.strip())
                results["weather"] = " | ".join(weather_info[:3])
        
        # Step 3: Satellite imagery (if API key exists)
        if os.getenv("SKYFI_API_KEY") and "coordinates" in results:
            # Create simple polygon
            lat, lon = results["coordinates"]["lat"], results["coordinates"]["lon"]
            offset = 0.01
            wkt = f"POLYGON(({lon-offset} {lat-offset}, {lon+offset} {lat-offset}, {lon+offset} {lat+offset}, {lon-offset} {lat+offset}, {lon-offset} {lat-offset}))"
            
            # Use raw client to get thumbnail URLs
            skyfi_client = SkyFiClient()
            from_date = (datetime.now() - timedelta(days=30)).isoformat() + 'Z'
            to_date = datetime.now().isoformat() + 'Z'
            
            raw_result = await skyfi_client.search_archives(
                aoi=wkt,
                from_date=from_date,
                to_date=to_date,
                open_data=True,
                resolution="LOW"
            )
            
            # Also get formatted result for display text
            search_result = await handle_skyfi_tool("skyfi_search_archives", {
                "aoi": wkt,
                "fromDate": "30 days ago",
                "toDate": "today",
                "maxCloudCoverage": 20
            })
            
            if search_result and len(search_result) > 0:
                search_text = search_result[0].text
                if "Found" in search_text:
                    # Extract the relevant imagery information
                    lines = search_text.split('\n')
                    imagery_items = []
                    current_item = []
                    
                    for line in lines:
                        if "Found" in line and "satellite" in line:
                            imagery_items.append(line.strip())
                        elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
                            # Start of a new item
                            if current_item:
                                imagery_items.append(' '.join(current_item))
                            current_item = []
                        elif line.strip().startswith('│') and any(keyword in line for keyword in ['ID:', 'Date:', 'Clouds:', '💵']):
                            # Extract key info from the box
                            info = line.strip('│ ').strip()
                            if 'ID:' in info:
                                current_item.append(f"ID: {info.split('ID:')[1].strip()[:12]}...")
                            elif 'Date:' in info:
                                current_item.append(info)
                            elif 'Clouds:' in info:
                                current_item.append(info)
                            elif '💵' in info:
                                current_item.append(info)
                    
                    # Add the last item
                    if current_item:
                        imagery_items.append(' '.join(current_item))
                    
                    # Format the results nicely
                    if len(imagery_items) > 1:
                        formatted_items = [imagery_items[0]]  # "Found X images"
                        for i, item in enumerate(imagery_items[1:6], 1):  # Next 5 items
                            formatted_items.append(f"{i}. {item}")
                        results["imagery"] = '\n'.join(formatted_items)
                    else:
                        results["imagery"] = imagery_items[0] if imagery_items else "No recent imagery available"
                    
                    # Add thumbnail URLs from raw result
                    if "archives" in raw_result and raw_result["archives"]:
                        thumbnails = []
                        for i, archive in enumerate(raw_result["archives"][:5]):
                            if "thumbnailUrls" in archive and "300x300" in archive["thumbnailUrls"]:
                                thumbnails.append({
                                    "url": archive["thumbnailUrls"]["300x300"],
                                    "id": archive.get("archiveId", "unknown"),
                                    "date": archive.get("captureTimestamp", "N/A"),
                                    "clouds": archive.get("cloudCoveragePercent", 0)
                                })
                        results["thumbnails"] = thumbnails
                elif "No images found" in search_text:
                    results["imagery"] = "No imagery in selected area/timeframe"
                else:
                    results["imagery"] = search_text.split('\n')[0] if search_text else "No recent imagery available"
        
        # Add recommendations
        results["recommendations"] = []
        if results.get("weather") and "Clear" in results.get("weather", ""):
            results["recommendations"].append("Good conditions for satellite capture")
        if results.get("imagery") and "Found" in results.get("imagery", ""):
            results["recommendations"].append("Recent imagery available for analysis")
        if os.getenv("SKYFI_API_KEY"):
            results["recommendations"].append("Cost optimization available for orders")
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}
    
    return results

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(5)
            await websocket.send_json({
                "type": "activity",
                "message": "System running smoothly",
                "level": "info"
            })
    except:
        pass

def main():
    """Run the web demo server."""
    print("\n" + "="*60)
    print("🌐 SkyFi MCP Web Demo")
    print("="*60)
    print(f"\n✅ Starting web server...")
    print(f"🔗 Open your browser to: http://localhost:8888")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8888, log_level="error")

if __name__ == "__main__":
    main()