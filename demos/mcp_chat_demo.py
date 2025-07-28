#!/usr/bin/env python3
"""
MCP Chat Demo for SkyFi

Interactive chat interface that showcases the Model Context Protocol.
This demo shows how an AI assistant can use MCP tools to answer questions.
"""

import asyncio
import json
import os
import sys
import uuid
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import our handlers directly
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

app = FastAPI(title="SkyFi MCP Chat Demo")

# HTML template with modern component-based UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SkyFi MCP Chat Demo</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>
    <style>
        .gradient-bg {
            background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%);
        }
        .message-bubble {
            max-width: 80%;
        }
        .tool-call {
            background: linear-gradient(to right, #f3f4f6, #e5e7eb);
            border-left: 3px solid #3b82f6;
            font-family: 'Consolas', 'Monaco', monospace;
        }
        #map { 
            height: 100%;
            width: 100%;
        }
        .typing-indicator {
            display: inline-flex;
            align-items: center;
        }
        .typing-indicator span {
            height: 8px;
            width: 8px;
            background-color: #6b7280;
            border-radius: 50%;
            display: inline-block;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        .thumbnail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        .thumbnail-item {
            position: relative;
            overflow: hidden;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .thumbnail-item:hover {
            transform: scale(1.05);
        }
        .thumbnail-item img {
            width: 100%;
            height: 120px;
            object-fit: cover;
        }
        .thumbnail-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
            color: white;
            padding: 5px;
            font-size: 10px;
        }
        .tool-icon {
            display: inline-block;
            width: 20px;
            text-align: center;
            margin-right: 5px;
        }
        .quick-action {
            cursor: pointer;
            transition: all 0.2s;
        }
        .quick-action:hover {
            background-color: #e5e7eb;
            transform: translateX(5px);
        }
        pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 10px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 12px;
        }
        .markdown-content h3 {
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
        }
        .markdown-content ul {
            list-style-type: disc;
            margin-left: 20px;
        }
        .markdown-content code {
            background: #e5e7eb;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
        }
        .markdown-content pre {
            background-color: #1e293b;
            color: #e2e8f0;
            padding: 1rem;
            border-radius: 0.375rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        .markdown-content pre code {
            background-color: transparent;
            color: #e2e8f0;
            padding: 0;
        }
    </style>
</head>
<body class="bg-gray-50">
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect, useRef, useCallback } = React;
        
        // Message Component
        const Message = ({ message }) => {
            const isUser = message.role === 'user';
            const isToolCall = message.type === 'tool_call';
            const isToolResult = message.type === 'tool_result';
            
            if (isToolCall) {
                return (
                    <div className="mb-4 tool-call p-3 rounded-lg mx-4">
                        <div className="flex items-center text-xs text-gray-700 mb-2">
                            <span className="tool-icon">🔧</span>
                            <span className="font-semibold">Tool Call: {message.tool}</span>
                        </div>
                        <pre className="text-xs">{JSON.stringify(message.args, null, 2)}</pre>
                    </div>
                );
            }
            
            if (isToolResult) {
                // Check if result contains thumbnails
                if (message.thumbnails && message.thumbnails.length > 0) {
                    return (
                        <div className="mb-4 mx-4">
                            <div className="text-xs text-gray-600 mb-2">
                                <span className="tool-icon">📸</span>
                                Satellite Imagery Results
                            </div>
                            <div className="thumbnail-grid">
                                {message.thumbnails.map((thumb, idx) => (
                                    <div key={idx} className="thumbnail-item">
                                        <img src={thumb.url} alt={`Satellite image ${idx + 1}`} />
                                        <div className="thumbnail-info">
                                            <div>{new Date(thumb.date).toLocaleDateString()}</div>
                                            <div>Clouds: {thumb.clouds.toFixed(0)}%</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                }
                
                return (
                    <div className="mb-4 bg-gray-50 p-3 rounded-lg mx-4">
                        <div className="text-xs text-gray-600 mb-1">
                            <span className="tool-icon">✅</span>
                            Tool Result
                        </div>
                        <div 
                            className="text-sm markdown-content" 
                            dangerouslySetInnerHTML={{ 
                                __html: marked.parse(message.result || '') 
                            }}
                        />
                    </div>
                );
            }
            
            return (
                <div className={`flex mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
                    <div className={`message-bubble p-4 rounded-lg ${
                        isUser ? 'bg-blue-600 text-white' : 'bg-white shadow-md'
                    }`}>
                        <div 
                            className={`text-sm ${isUser ? '' : 'markdown-content'}`}
                            dangerouslySetInnerHTML={{ 
                                __html: isUser ? message.content : marked.parse(message.content || '') 
                            }}
                        />
                        <div className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>
                            {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                    </div>
                </div>
            );
        };
        
        // Tool Panel Component
        const ToolPanel = ({ tools, onToolClick }) => {
            const categories = {
                '🗺️ Location': [
                    { name: 'osm_geocode', display: 'Find Location', example: 'Find the coordinates of Central Park' },
                    { name: 'osm_reverse_geocode', display: 'Get Address', example: 'What address is at 40.7580, -73.9855?' },
                    { name: 'osm_generate_aoi', display: 'Create Area', example: 'Create a 5km area around Times Square' }
                ],
                '🌤️ Weather': [
                    { name: 'weather_current', display: 'Current Weather', example: 'What\\'s the weather in Tokyo?' },
                    { name: 'weather_forecast', display: 'Forecast', example: 'Show me the 5-day forecast for London' }
                ],
                '🛰️ Satellite': [
                    { name: 'skyfi_search_archives', display: 'Search Images', example: 'Find satellite images of Manhattan from last week' },
                    { name: 'skyfi_estimate_cost', display: 'Cost Estimate', example: 'How much would satellite imagery of Central Park cost?' },
                    { name: 'skyfi_get_user', display: 'Account Info', example: 'Show my SkyFi account details' }
                ]
            };
            
            return (
                <div className="bg-white rounded-lg shadow-md p-3">
                    <h3 className="font-semibold text-sm mb-2">Quick Actions</h3>
                    {Object.entries(categories).map(([category, categoryTools]) => (
                        <div key={category} className="mb-2">
                            <h4 className="text-xs font-medium text-gray-600 mb-1">{category}</h4>
                            <div className="space-y-0.5">
                                {categoryTools.map(tool => (
                                    <div
                                        key={tool.name}
                                        onClick={() => onToolClick(tool.example)}
                                        className="quick-action text-xs p-1 rounded hover:bg-gray-100 cursor-pointer"
                                        title={`Click to ask: ${tool.example}`}
                                    >
                                        <span className="font-medium">{tool.display}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            );
        };
        
        // Map Component
        const MapView = ({ markers }) => {
            const mapRef = useRef(null);
            const mapInstanceRef = useRef(null);
            const markersRef = useRef([]);
            const polygonRef = useRef(null);
            
            useEffect(() => {
                if (!mapInstanceRef.current && mapRef.current) {
                    mapInstanceRef.current = L.map(mapRef.current).setView([40.7128, -74.0060], 11);
                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap contributors'
                    }).addTo(mapInstanceRef.current);
                }
                
                // Clear existing markers
                markersRef.current.forEach(marker => mapInstanceRef.current.removeLayer(marker));
                markersRef.current = [];
                
                // Clear existing polygon
                if (polygonRef.current) {
                    mapInstanceRef.current.removeLayer(polygonRef.current);
                    polygonRef.current = null;
                }
                
                // Add polygon if available
                if (window.currentPolygon) {
                    polygonRef.current = L.rectangle(window.currentPolygon, {
                        color: '#3b82f6',
                        weight: 2,
                        fillOpacity: 0.1
                    }).addTo(mapInstanceRef.current);
                    
                    // Fit map to polygon bounds
                    mapInstanceRef.current.fitBounds(window.currentPolygon);
                    
                    // Clear after use
                    window.currentPolygon = null;
                }
                
                // Add new markers
                markers.forEach(markerData => {
                    const marker = L.marker(markerData.position)
                        .addTo(mapInstanceRef.current)
                        .bindPopup(markerData.label);
                    markersRef.current.push(marker);
                    
                    // Pan to first marker
                    if (markers.length === 1 && !polygonRef.current) {
                        mapInstanceRef.current.setView(markerData.position, 13);
                    }
                });
                
                // Fit bounds if multiple markers
                if (markers.length > 1 && !polygonRef.current) {
                    const group = L.featureGroup(markersRef.current);
                    mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
                }
            }, [markers]);
            
            return (
                <div className="bg-white rounded-lg shadow-lg p-3 h-full flex flex-col">
                    <h3 className="text-sm font-semibold mb-2 flex items-center">
                        <span className="mr-1">🗺️</span>
                        Interactive Map
                        {markers.length > 0 && (
                            <span className="ml-auto text-xs text-gray-500">
                                {markers.length} location{markers.length > 1 ? 's' : ''}
                            </span>
                        )}
                    </h3>
                    <div ref={mapRef} id="map" className="rounded-lg flex-1"></div>
                </div>
            );
        };
        
        // Stats Component removed for cleaner UI
        
        // Main Chat Application
        const ChatApp = () => {
            const [messages, setMessages] = useState([]);
            const [input, setInput] = useState('');
            const [isTyping, setIsTyping] = useState(false);
            const [markers, setMarkers] = useState([]);
            // Stats removed for cleaner UI
            const ws = useRef(null);
            const messagesEndRef = useRef(null);
            
            // Auto-scrolling removed for better UX
            // Users can manually scroll as needed
            
            // Initialize WebSocket connection
            useEffect(() => {
                const connectWS = async () => {
                    ws.current = new WebSocket(`ws://${window.location.host}/ws/chat`);
                    
                    ws.current.onopen = () => {
                        console.log('Connected to MCP chat server');
                        // Send initial status check
                        ws.current.send(JSON.stringify({
                            type: 'status'
                        }));
                    };
                    
                    ws.current.onmessage = (event) => {
                        const data = JSON.parse(event.data);
                        
                        switch (data.type) {
                            case 'status':
                                // Status updates handled silently
                                break;
                                
                            case 'message':
                                setMessages(prev => [...prev, data.message]);
                                setIsTyping(false);
                                break;
                                
                            case 'tool_call':
                                setMessages(prev => [...prev, {
                                    type: 'tool_call',
                                    tool: data.tool,
                                    args: data.args,
                                    timestamp: new Date().toISOString()
                                }]);
                                // Tool calls tracked silently
                                break;
                                
                            case 'tool_result':
                                setMessages(prev => [...prev, {
                                    type: 'tool_result',
                                    result: data.result,
                                    thumbnails: data.thumbnails,
                                    timestamp: new Date().toISOString()
                                }]);
                                break;
                                
                            case 'map_update':
                                setMarkers(data.markers || []);
                                if (data.polygon) {
                                    // Store polygon data for map display
                                    window.currentPolygon = data.polygon;
                                }
                                break;
                                
                            case 'typing':
                                setIsTyping(true);
                                break;
                                
                            case 'error':
                                setMessages(prev => [...prev, {
                                    role: 'assistant',
                                    content: `Error: ${data.message}`,
                                    timestamp: new Date().toISOString()
                                }]);
                                setIsTyping(false);
                                break;
                        }
                    };
                    
                    ws.current.onerror = (error) => {
                        console.error('WebSocket error:', error);
                    };
                    
                    ws.current.onclose = () => {
                        console.log('WebSocket closed, reconnecting...');
                        setTimeout(connectWS, 3000);
                    };
                };
                
                connectWS();
                
                return () => {
                    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
                        ws.current.close();
                    }
                };
            }, []);
            
            const sendMessage = (content) => {
                if (!content.trim() || !ws.current || ws.current.readyState !== WebSocket.OPEN) return;
                
                const message = {
                    role: 'user',
                    content: content,
                    timestamp: new Date().toISOString()
                };
                
                setMessages(prev => [...prev, message]);
                setInput('');
                
                ws.current.send(JSON.stringify({
                    type: 'message',
                    content: content
                }));
            };
            
            const handleQuickAction = (example) => {
                sendMessage(example);
            };
            
            return (
                <div className="h-screen bg-gray-50 overflow-hidden flex flex-col">
                    {/* Header */}
                    <header className="gradient-bg text-white shadow-lg">
                        <div className="container mx-auto px-6 py-2">
                            <h1 className="text-xl font-bold">🛰️ SkyFi MCP Chat Demo</h1>
                            <p className="text-blue-200 text-xs">Interactive Model Context Protocol Demonstration</p>
                        </div>
                    </header>
                    
                    <div className="container mx-auto px-4 py-2 flex-1 overflow-hidden">
                        <div className="grid grid-cols-1 lg:grid-cols-12 gap-2 h-full">
                            {/* Left Panel - Tools (2 columns) */}
                            <div className="lg:col-span-2 h-full">
                                <ToolPanel onToolClick={handleQuickAction} />
                            </div>
                            
                            {/* Center - Map (5 columns) */}
                            <div className="lg:col-span-5 h-full">
                                <MapView markers={markers} />
                            </div>
                            
                            {/* Right Panel - Chat (5 columns) */}
                            <div className="lg:col-span-5 h-full min-h-0">
                                <div className="bg-white rounded-lg shadow-lg flex flex-col h-full overflow-hidden">
                                    {/* Chat Header */}
                                    <div className="p-3 border-b bg-gray-50">
                                        <h3 className="text-sm font-semibold flex items-center">
                                            <span className="mr-1">💬</span>
                                            Chat Assistant
                                        </h3>
                                    </div>
                                    {/* Messages */}
                                    <div className="flex-1 overflow-y-auto p-4 min-h-0">
                                        {messages.length === 0 && (
                                            <div className="text-center text-gray-500 mt-10">
                                                <p className="text-base mb-2">👋 Hi! I'm your SkyFi assistant.</p>
                                                <p className="text-sm">
                                                    Ask me about satellite imagery, weather, or locations.
                                                </p>
                                                <p className="text-xs text-gray-400 mt-4">
                                                    Try clicking a quick action or type below
                                                </p>
                                            </div>
                                        )}
                                        
                                        {messages.map((msg, idx) => (
                                            <Message key={idx} message={msg} />
                                        ))}
                                        
                                        {isTyping && (
                                            <div className="flex justify-start mb-4">
                                                <div className="bg-white shadow-md p-4 rounded-lg">
                                                    <div className="typing-indicator">
                                                        <span></span>
                                                        <span></span>
                                                        <span></span>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                        
                                        <div ref={messagesEndRef} />
                                    </div>
                                    
                                    {/* Input */}
                                    <div className="border-t p-4">
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={input}
                                                onChange={(e) => setInput(e.target.value)}
                                                onKeyPress={(e) => e.key === 'Enter' && sendMessage(input)}
                                                placeholder="Ask about satellite imagery, weather, or locations..."
                                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                                disabled={!ws.current || ws.current.readyState !== WebSocket.OPEN}
                                            />
                                            <button
                                                onClick={() => sendMessage(input)}
                                                disabled={!ws.current || ws.current.readyState !== WebSocket.OPEN}
                                                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:bg-gray-400"
                                            >
                                                Send
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            );
        };
        
        // Pass API key status to React app
        window.SKYFI_API_KEY = """ + str(bool(os.getenv("SKYFI_API_KEY"))).lower() + """;
        
        // Render the app
        ReactDOM.render(<ChatApp />, document.getElementById('root'));
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Handle WebSocket chat connections with MCP."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data["type"] == "status":
                await websocket.send_json({
                    "type": "status",
                    "skyfi_active": bool(os.getenv("SKYFI_API_KEY"))
                })
            
            elif data["type"] == "message":
                await websocket.send_json({"type": "typing"})
                
                # Process the message and generate response
                try:
                    response = await process_message(
                        data["content"],
                        websocket
                    )
                    
                    await websocket.send_json({
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": response,
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                except Exception as e:
                    error_message = str(e)
                    if "422" in error_message:
                        friendly_error = "The search area might be too complex. Try searching for a smaller or simpler area."
                    elif "521" in error_message:
                        friendly_error = "The satellite imagery service is temporarily unavailable. Please try again later."
                    elif "404" in error_message:
                        friendly_error = "The requested resource was not found. Please check your query."
                    else:
                        friendly_error = f"An error occurred: {error_message}"
                    
                    await websocket.send_json({
                        "type": "message",
                        "message": {
                            "role": "assistant",
                            "content": f"❌ {friendly_error}",
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

async def process_message(content: str, websocket: WebSocket) -> str:
    """Process user message and handle tool calls."""
    content_lower = content.lower()
    
    # Check for cost/pricing requests FIRST (before satellite imagery)
    if any(word in content_lower for word in ['cost', 'price', 'expensive', 'cheap', 'budget', 'estimate', 'how much']):
        if not os.getenv("SKYFI_API_KEY"):
            return ("To get real pricing information, you'll need to configure your SKYFI_API_KEY. "
                   "Typical satellite imagery costs range from $0-50 per km² depending on resolution and recency.")
        
        location = extract_location(content)
        if location:
            # Get coordinates and create AOI
            geocode_result = await handle_osm_tool("osm_geocode", {
                "query": location,
                "limit": 1
            })
            
            if geocode_result:
                coords = parse_coordinates(geocode_result[0].text)
                if coords:
                    wkt = create_simple_polygon(coords['lat'], coords['lon'], 0.05)  # ~10km area
                    
                    # Since skyfi_estimate_cost is not implemented, use search to get price info
                    await websocket.send_json({
                        "type": "tool_call",
                        "tool": "skyfi_search_archives",
                        "args": {
                            "aoi": wkt,
                            "fromDate": "7 days ago",
                            "toDate": "today",
                            "maxCloudCoverage": 100  # Accept any cloud coverage for cost estimate
                        }
                    })
                    
                    search_result = await handle_skyfi_tool("skyfi_search_archives", {
                        "aoi": wkt,
                        "fromDate": "7 days ago",
                        "toDate": "today",
                        "maxCloudCoverage": 100
                    })
                    
                    if search_result and search_result[0].text:
                        # Extract price information from search results
                        text = search_result[0].text
                        
                        # Calculate approximate area (roughly)
                        # For a 0.05 degree square at ~40°N latitude
                        # 1 degree latitude ≈ 111 km, 1 degree longitude ≈ 85 km at this latitude
                        area_km2 = (0.1 * 111) * (0.1 * 85)  # ~94 km²
                        
                        response = f"**Cost estimate for satellite imagery of {location}:**\n\n"
                        response += f"📐 Area: ~{area_km2:.2f} km²\n\n"
                        
                        # Extract pricing from results
                        if "Found" in text:
                            lines = text.split('\n')
                            prices = []
                            for line in lines:
                                if "💵" in line:
                                    # Extract price
                                    price_match = re.search(r'\$([0-9,]+(?:\.[0-9]+)?)', line)
                                    if price_match:
                                        price = float(price_match.group(1).replace(',', ''))
                                        prices.append(price)
                            
                            if prices:
                                min_price = min(prices)
                                max_price = max(prices)
                                avg_price = sum(prices) / len(prices)
                                
                                response += f"💰 **Price Range**: ${min_price:.2f} - ${max_price:.2f}\n"
                                response += f"📊 **Average Price**: ${avg_price:.2f}\n\n"
                                response += f"Based on {len(prices)} recent satellite images available.\n\n"
                                response += "**Note**: Actual costs depend on:\n"
                                response += "• Image resolution (30cm to 5m)\n"
                                response += "• Processing level\n"
                                response += "• Delivery options\n"
                                response += "• Minimum order size (25 km²)"
                            else:
                                response += "💰 Typical costs range from **$0-50 per km²** depending on:\n"
                                response += "• Resolution (30cm high-res to 5m low-res)\n"
                                response += "• Recency of capture\n"
                                response += "• Cloud coverage\n"
                                response += "• Processing requirements"
                        else:
                            response += "💰 Typical satellite imagery costs:\n"
                            response += f"• **Low resolution (3-5m)**: $0-5/km²\n"
                            response += f"• **Medium resolution (1-2m)**: $10-20/km²\n"
                            response += f"• **High resolution (30-50cm)**: $25-50/km²\n\n"
                            response += f"For your {area_km2:.2f} km² area:\n"
                            response += f"• **Estimated range**: ${area_km2*0:.0f} - ${area_km2*50:.0f}"
                        
                        return response
            
            return f"I couldn't estimate costs for **{location}**. Please try a different location."
        else:
            return "Which area would you like a cost estimate for? Please specify a location."
    
    
    # Check for weather requests
    elif any(word in content_lower for word in ['weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny']):
        location = extract_location(content)
        is_forecast = 'forecast' in content_lower or 'next' in content_lower or 'week' in content_lower
        
        if location:
            tool_name = "weather_forecast" if is_forecast else "weather_current"
            
            await websocket.send_json({
                "type": "tool_call",
                "tool": tool_name,
                "args": {"location": location} if not is_forecast else {"location": location, "days": 5}
            })
            
            weather_result = await handle_weather_tool(tool_name, {
                "location": location,
                "days": 5
            } if is_forecast else {"location": location})
            
            if weather_result and weather_result[0].text:
                await websocket.send_json({
                    "type": "tool_result",
                    "result": weather_result[0].text
                })
                
                # Also update map with location
                geocode_result = await handle_osm_tool("osm_geocode", {
                    "query": location,
                    "limit": 1
                })
                
                if geocode_result:
                    coords = parse_coordinates(geocode_result[0].text)
                    if coords:
                        await websocket.send_json({
                            "type": "map_update",
                            "markers": [{
                                "position": [coords['lat'], coords['lon']],
                                "label": f"Weather: {location}"
                            }]
                        })
                
                # Format a nice response
                if is_forecast:
                    return f"Here's the weather forecast for **{location}**:\n\n{weather_result[0].text}"
                else:
                    # Extract key weather info
                    lines = weather_result[0].text.split('\n')
                    temp_line = next((l for l in lines if 'Temperature:' in l), None)
                    cond_line = next((l for l in lines if 'Conditions:' in l), None)
                    
                    if temp_line and cond_line:
                        temp = temp_line.split(':')[1].strip()
                        cond = cond_line.split(':')[1].strip()
                        return f"The current weather in **{location}** is **{temp}** and **{cond}**."
                    else:
                        return weather_result[0].text
            
            return f"I couldn't get weather data for **{location}**. Please try another location."
        else:
            return "Which location would you like weather information for?"
    
    # Check for satellite imagery requests EARLY (before generic "find" catches it)
    elif any(word in content_lower for word in ['satellite', 'imagery', 'images', 'archive', 'photos']):
        location = extract_location(content)
        time_range = extract_time_range(content)
        
        if location:
            # First geocode the location
            await websocket.send_json({
                "type": "tool_call",
                "tool": "osm_geocode",
                "args": {"query": location, "limit": 1}
            })
            
            geocode_result = await handle_osm_tool("osm_geocode", {
                "query": location,
                "limit": 1
            })
            
            if geocode_result and geocode_result[0].text:
                coords = parse_coordinates(geocode_result[0].text)
                location_info = parse_location_info(geocode_result[0].text)
                
                if coords:
                    # Update map
                    await websocket.send_json({
                        "type": "map_update",
                        "markers": [{
                            "position": [coords['lat'], coords['lon']],
                            "label": location
                        }]
                    })
                    
                    # Search for satellite imagery
                    wkt = create_simple_polygon(coords['lat'], coords['lon'])
                    
                    await websocket.send_json({
                        "type": "tool_call",
                        "tool": "skyfi_search_archives",
                        "args": {
                            "aoi": wkt,
                            "fromDate": time_range["from"],
                            "toDate": time_range["to"],
                            "maxCloudCoverage": 20
                        }
                    })
                    
                    # Check if we have API key
                    if not os.getenv("SKYFI_API_KEY"):
                        await websocket.send_json({
                            "type": "tool_result",
                            "result": "⚠️ SkyFi API key not configured. Using mock data for demonstration."
                        })
                        
                        # Return mock response
                        return (f"I found the location **{location}** at coordinates "
                                f"({coords['lat']:.4f}, {coords['lon']:.4f}).\n\n"
                                f"To search for real satellite imagery, you'll need to configure "
                                f"your SKYFI_API_KEY in the .env file.")
                    
                    # Get real imagery
                    imagery_result = await handle_skyfi_tool("skyfi_search_archives", {
                        "aoi": wkt,
                        "fromDate": time_range["from"],
                        "toDate": time_range["to"],
                        "maxCloudCoverage": 20
                    })
                    
                    if imagery_result and imagery_result[0].text:
                        # Parse thumbnails if available
                        from src.mcp_skyfi.skyfi.client import SkyFiClient
                        client = SkyFiClient()
                        
                        # Get raw result for thumbnails
                        try:
                            # Parse relative dates properly
                            from datetime import timedelta
                            if "days ago" in time_range["from"]:
                                days = int(time_range["from"].split()[0])
                                from_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                            elif time_range["from"] == "today":
                                from_date = datetime.now().strftime('%Y-%m-%d')
                            else:
                                from_date = datetime.now().strftime('%Y-%m-%d')
                                
                            if time_range["to"] == "today":
                                to_date = datetime.now().strftime('%Y-%m-%d')
                            else:
                                to_date = datetime.now().strftime('%Y-%m-%d')
                            
                            raw_result = await client.search_archives(
                                aoi=wkt,
                                from_date=from_date + 'T00:00:00Z',
                                to_date=to_date + 'T23:59:59Z'
                            )
                        except Exception as e:
                            print(f"Error getting raw results: {e}")
                            raw_result = {}
                        
                        thumbnails = []
                        if "archives" in raw_result:
                            for archive in raw_result["archives"][:5]:
                                if "thumbnailUrls" in archive and "300x300" in archive["thumbnailUrls"]:
                                    thumbnails.append({
                                        "url": archive["thumbnailUrls"]["300x300"],
                                        "date": archive.get("captureTimestamp", "N/A"),
                                        "clouds": archive.get("cloudCoveragePercent", 0)
                                    })
                        
                        await websocket.send_json({
                            "type": "tool_result",
                            "result": imagery_result[0].text.split('\n\n')[0],  # Just the summary
                            "thumbnails": thumbnails
                        })
                        
                        # Parse the imagery result
                        if "Found" in imagery_result[0].text:
                            count = re.search(r'Found (\d+)', imagery_result[0].text)
                            count_str = count.group(1) if count else "several"
                            
                            response = (f"I found **{count_str} satellite images** of **{location}** "
                                       f"{time_range['description']}!\n\n")
                            
                            # Add details about first few results
                            lines = imagery_result[0].text.split('\n')
                            image_details = []
                            for line in lines:
                                if line.strip().startswith(('1.', '2.', '3.')):
                                    # Extract key info
                                    if 'Date:' in line:
                                        date_match = re.search(r'Date: ([^|]+)', line)
                                        if date_match:
                                            image_details.append(f"• {date_match.group(1).strip()}")
                            
                            if image_details:
                                response += "Recent captures include:\n" + '\n'.join(image_details[:3])
                            
                            return response
                        else:
                            return (f"I couldn't find any satellite imagery of **{location}** "
                                   f"{time_range['description']}. This could be due to cloud cover "
                                   f"or no satellites passing over during that time. Try a different "
                                   f"time period or location.")
                    
            return f"I couldn't locate **{location}**. Could you be more specific or try a different location name?"
        else:
            return "I need a location to search for satellite imagery. Could you specify where you'd like to look?"
    
    # Check for reverse geocoding (coordinates to address)
    elif "what address is at" in content_lower and re.search(r'-?\d+\.?\d*,\s*-?\d+\.?\d*', content):
        # Extract coordinates from the question
        coord_match = re.search(r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)', content)
        if coord_match:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            
            await websocket.send_json({
                "type": "tool_call",
                "tool": "osm_reverse_geocode",
                "args": {"lat": lat, "lon": lon}
            })
            
            result = await handle_osm_tool("osm_reverse_geocode", {
                "lat": lat,
                "lon": lon
            })
            
            if result and result[0].text:
                await websocket.send_json({
                    "type": "tool_result",
                    "result": result[0].text
                })
                
                # Update map
                await websocket.send_json({
                    "type": "map_update",
                    "markers": [{
                        "position": [lat, lon],
                        "label": "Address lookup"
                    }]
                })
                
                # Extract the address from the result
                lines = result[0].text.split('\n')
                address = None
                for line in lines:
                    if line.strip() and not line.startswith('Found'):
                        address = line.strip()
                        break
                
                if address:
                    return (f"The address at coordinates **({lat}, {lon})** is:\n\n"
                           f"📍 **{address}**\n\n"
                           f"I've marked this location on the map.")
                else:
                    return result[0].text
            
            return f"I couldn't find an address at coordinates ({lat}, {lon})."
        else:
            return "Please provide coordinates in the format: lat, lon (e.g., 40.7580, -73.9855)"
    
    # Check for geocoding/location requests (now comes AFTER satellite check)
    elif any(word in content_lower for word in ['where', 'location', 'address', 'coordinates', 'find', 'locate']):
        location = extract_location(content)
        
        if location:
            await websocket.send_json({
                "type": "tool_call",
                "tool": "osm_geocode",
                "args": {"query": location, "limit": 1}
            })
            
            result = await handle_osm_tool("osm_geocode", {
                "query": location,
                "limit": 1
            })
            
            if result and result[0].text:
                await websocket.send_json({
                    "type": "tool_result",
                    "result": result[0].text
                })
                
                coords = parse_coordinates(result[0].text)
                if coords:
                    await websocket.send_json({
                        "type": "map_update",
                        "markers": [{
                            "position": [coords['lat'], coords['lon']],
                            "label": location
                        }]
                    })
                    
                    return (f"I found **{location}**! It's located at coordinates "
                           f"**({coords['lat']:.6f}, {coords['lon']:.6f})**.\n\n"
                           f"I've marked it on the map for you.")
                
                return result[0].text
            
            return f"I couldn't find **{location}**. Could you provide more details?"
        else:
            return "What location would you like me to find?"
    
    # Check for area/AOI creation requests
    elif any(word in content_lower for word in ['area', 'aoi', 'region', 'zone', 'perimeter']):
        location = extract_location(content)
        size = extract_size(content)
        
        if location:
            # First geocode
            geocode_result = await handle_osm_tool("osm_geocode", {
                "query": location,
                "limit": 1
            })
            
            if geocode_result and geocode_result[0].text:
                coords = parse_coordinates(geocode_result[0].text)
                
                if coords:
                    await websocket.send_json({
                        "type": "tool_call",
                        "tool": "osm_generate_aoi",
                        "args": {
                            "center": {"lat": coords['lat'], "lon": coords['lon']},
                            "size_km": size,
                            "shape": "square"
                        }
                    })
                    
                    aoi_result = await handle_osm_tool("osm_generate_aoi", {
                        "center": {"lat": coords['lat'], "lon": coords['lon']},
                        "size_km": size,
                        "shape": "square"
                    })
                    
                    if aoi_result:
                        await websocket.send_json({
                            "type": "tool_result",
                            "result": aoi_result[0].text
                        })
                        
                        # Extract WKT from result and send polygon to map
                        result_text = aoi_result[0].text
                        wkt_match = re.search(r'POLYGON\(\(([^)]+)\)\)', result_text)
                        if wkt_match:
                            # Convert WKT to bounds for map display
                            coords_str = wkt_match.group(1)
                            points = []
                            for coord_pair in coords_str.split(', '):
                                lon, lat = coord_pair.split()
                                points.append([float(lat), float(lon)])
                            
                            # Get bounds
                            if points:
                                lats = [p[0] for p in points]
                                lons = [p[1] for p in points]
                                bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
                                
                                await websocket.send_json({
                                    "type": "map_update",
                                    "markers": [{
                                        "position": [coords['lat'], coords['lon']],
                                        "label": f"{location} center"
                                    }],
                                    "polygon": bounds
                                })
                        
                        return (f"I've created a **{size}km × {size}km area** centered on **{location}**. "
                               f"This area can be used for satellite imagery searches or other geospatial analysis.")
                    
            return f"I couldn't create an area around **{location}**. Please try a different location."
        else:
            return "Where would you like me to create an area of interest?"
    
    # Check for account/user info requests
    elif any(word in content_lower for word in ['account', 'balance', 'credits', 'subscription', 'my skyfi']):
        if not os.getenv("SKYFI_API_KEY"):
            return "You need to configure your SKYFI_API_KEY to view account information."
        
        await websocket.send_json({
            "type": "tool_call",
            "tool": "skyfi_get_user",
            "args": {}
        })
        
        user_result = await handle_skyfi_tool("skyfi_get_user", {})
        
        if user_result:
            await websocket.send_json({
                "type": "tool_result",
                "result": user_result[0].text
            })
            
            return "Here's your SkyFi account information:\n\n" + user_result[0].text
        
        return "I couldn't retrieve your account information. Please check your API key."
    
    # Default response with suggestions
    return ("I can help you with:\n\n"
            "• **Satellite imagery** - \"Find satellite images of Paris from last month\"\n"
            "• **Weather data** - \"What's the weather in Tokyo?\"\n"
            "• **Location search** - \"Where is the Eiffel Tower?\"\n"
            "• **Cost estimates** - \"How much would imagery of Manhattan cost?\"\n"
            "• **Area creation** - \"Create a 10km area around Central Park\"\n\n"
            "What would you like to know?")

def extract_location(text: str) -> Optional[str]:
    """Extract location from user message."""
    # Check for quoted location first
    quoted = re.findall(r'"([^"]*)"', text)
    if quoted:
        return quoted[0]
    
    # Common known locations - check these before removing words
    known_locations = [
        'manhattan', 'central park', 'times square', 'brooklyn', 'tokyo', 'paris', 
        'london', 'new york', 'los angeles', 'chicago', 'san francisco', 'eiffel tower',
        'statue of liberty', 'golden gate bridge', 'empire state building', 'brooklyn bridge',
        'washington dc', 'seattle', 'boston', 'miami', 'atlanta', 'denver', 'phoenix'
    ]
    
    text_lower = text.lower()
    for location in known_locations:
        if location in text_lower:
            # Extract with proper capitalization
            start = text_lower.find(location)
            return text[start:start + len(location)].title()
    
    # Remove common phrases that aren't locations (after checking known locations)
    cleaned_text = re.sub(r'\b(the|in|at|near|around|from|for|find|search|show|get|would)\b', ' ', text, flags=re.IGNORECASE)
    
    # Special handling for "of" - keep it if it's part of a location phrase
    if ' of ' in text:
        # Check if "of" is connecting location words
        parts = text.split(' of ')
        if len(parts) == 2:
            before = parts[0].split()[-1] if parts[0].split() else ""
            after = parts[1].split()[0] if parts[1].split() else ""
            # Keep "of" if both surrounding words are capitalized (e.g., "City of New York")
            if before and after and before[0].isupper() and after[0].isupper():
                cleaned_text = text
    
    # Look for capitalized words (potential place names)
    words = cleaned_text.split()
    location_words = []
    
    for i, word in enumerate(words):
        if word and word[0].isupper() and len(word) > 2:
            # Skip common non-location words
            if word.lower() in ['how', 'what', 'when', 'where', 'why', 'who', 'which', 'much', 'cost', 'price']:
                continue
                
            # Start collecting location words
            location_words = [word]
            
            # Look for following capitalized words or common location suffixes
            j = i + 1
            while j < len(words):
                next_word = words[j]
                if (next_word and (next_word[0].isupper() or 
                    next_word.lower() in ['park', 'square', 'street', 'avenue', 'city', 'tower', 'bridge', 'of'])):
                    location_words.append(next_word)
                    j += 1
                else:
                    break
            
            if location_words and len(' '.join(location_words)) > 3:
                return ' '.join(location_words)
    
    return None

def extract_time_range(text: str) -> Dict[str, str]:
    """Extract time range from user message."""
    text_lower = text.lower()
    
    # Common time patterns
    if 'today' in text_lower:
        return {"from": "today", "to": "today", "description": "from today"}
    elif 'yesterday' in text_lower:
        return {"from": "1 day ago", "to": "1 day ago", "description": "from yesterday"}
    elif 'last week' in text_lower or 'past week' in text_lower:
        return {"from": "7 days ago", "to": "today", "description": "from the last week"}
    elif 'last month' in text_lower or 'past month' in text_lower:
        return {"from": "30 days ago", "to": "today", "description": "from the last month"}
    elif 'last year' in text_lower:
        return {"from": "365 days ago", "to": "today", "description": "from the last year"}
    
    # Look for "X days ago" pattern
    days_match = re.search(r'(\d+)\s*days?\s*ago', text_lower)
    if days_match:
        days = days_match.group(1)
        return {"from": f"{days} days ago", "to": "today", "description": f"from the last {days} days"}
    
    # Default to last 30 days
    return {"from": "30 days ago", "to": "today", "description": "from the last 30 days"}

def extract_size(text: str) -> float:
    """Extract size in km from user message."""
    # Look for number followed by km
    match = re.search(r'(\d+)\s*km', text.lower())
    if match:
        return float(match.group(1))
    
    # Look for written numbers
    size_words = {
        'five': 5, 'ten': 10, 'twenty': 20, 'fifty': 50,
        'small': 5, 'medium': 10, 'large': 20
    }
    
    for word, size in size_words.items():
        if word in text.lower():
            return size
    
    # Default to 10km
    return 10

def parse_coordinates(geocode_text: str) -> Optional[Dict[str, float]]:
    """Parse coordinates from geocode result."""
    # Look for Lat/Lon pattern
    match = re.search(r'Lat:\s*([-\d.]+),\s*Lon:\s*([-\d.]+)', geocode_text)
    if match:
        return {
            'lat': float(match.group(1)),
            'lon': float(match.group(2))
        }
    return None

def parse_location_info(geocode_text: str) -> Optional[str]:
    """Parse location description from geocode result."""
    lines = geocode_text.split('\n')
    for line in lines:
        if line.strip() and not line.startswith('Found') and 'Lat:' not in line:
            return line.strip()
    return None

def create_simple_polygon(lat: float, lon: float, size: float = 0.01) -> str:
    """Create a simple square polygon WKT."""
    return (f"POLYGON(({lon-size} {lat-size}, {lon+size} {lat-size}, "
            f"{lon+size} {lat+size}, {lon-size} {lat+size}, {lon-size} {lat-size}))")

def main():
    """Run the MCP chat demo server."""
    print("\n" + "="*60)
    print("🤖 SkyFi MCP Chat Demo")
    print("="*60)
    print(f"\n✅ Starting chat server...")
    print(f"🔗 Open your browser to: http://localhost:8889")
    print(f"\nThis demo showcases the Model Context Protocol (MCP)")
    print(f"with an interactive chat interface.\n")
    print(f"Features:")
    print(f"  • Natural language understanding")
    print(f"  • Real-time tool execution")
    print(f"  • Interactive map visualization")
    print(f"  • Satellite imagery with thumbnails")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8889, log_level="error")

if __name__ == "__main__":
    main()