# SkyFi MCP Integration Guide

This guide shows how to integrate the SkyFi MCP server with various AI frameworks and providers.

## Table of Contents
- [Claude Desktop](#claude-desktop)
- [Cursor](#cursor)
- [Claude Web](#claude-web)
- [Langchain](#langchain)
- [Vercel AI SDK](#vercel-ai-sdk)
- [OpenAI](#openai)
- [Anthropic SDK](#anthropic-sdk)
- [Google Gemini](#google-gemini)
- [ADK (Anthropic Development Kit)](#adk)

## Claude Desktop

### Local Installation
```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["-m", "pip", "install", "-q", "git+https://github.com/NoaheCampbell/SkyFi-MCP.git", "&&", "python3", "-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Remote Server
```json
{
  "mcpServers": {
    "skyfi": {
      "command": "npx",
      "args": ["@noahecampbell/skyfi-mcp-client"],
      "env": {
        "SKYFI_WS_URL": "wss://skyfi-mcp.fly.dev"
      }
    }
  }
}
```

## Cursor

Add to `.cursor/mcp_settings.json`:
```json
{
  "mcpServers": {
    "skyfi": {
      "command": "python3",
      "args": ["-m", "mcp_skyfi"],
      "env": {
        "SKYFI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Claude Web

Currently, Claude Web doesn't support direct MCP connections. Use the API integration instead:

```python
import anthropic

client = anthropic.Anthropic()

# Use the MCP tools via function calling
response = client.messages.create(
    model="claude-3-opus-20240229",
    messages=[{
        "role": "user",
        "content": "Search for satellite images of Central Park from last week"
    }],
    tools=[{
        "name": "skyfi_search_archives",
        "description": "Search for satellite imagery",
        "input_schema": {
            "type": "object",
            "properties": {
                "aoi": {"type": "string"},
                "fromDate": {"type": "string"},
                "toDate": {"type": "string"}
            }
        }
    }]
)
```

## Langchain

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
import httpx
import asyncio

class SkyFiMCPTool:
    def __init__(self, ws_url="wss://skyfi-mcp.fly.dev", api_key=None):
        self.ws_url = ws_url
        self.api_key = api_key
        
    async def call_tool(self, tool_name: str, arguments: dict):
        """Call MCP tool via WebSocket."""
        import websockets
        import json
        
        async with websockets.connect(
            self.ws_url,
            extra_headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        ) as websocket:
            # Send MCP request
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                },
                "id": 1
            }
            await websocket.send(json.dumps(request))
            
            # Get response
            response = await websocket.recv()
            return json.loads(response)

# Create Langchain tools
skyfi_tool = SkyFiMCPTool(api_key="your-api-key")

search_tool = Tool(
    name="search_satellite_images",
    func=lambda q: asyncio.run(skyfi_tool.call_tool("skyfi_search_archives", {
        "aoi": q["aoi"],
        "fromDate": q["from_date"],
        "toDate": q["to_date"]
    })),
    description="Search for satellite imagery"
)

# Use with agent
llm = OpenAI(temperature=0)
agent = initialize_agent([search_tool], llm, agent="zero-shot-react-description")
```

## Vercel AI SDK

```typescript
import { createAssistant } from '@vercel/ai-sdk';
import WebSocket from 'ws';

// MCP WebSocket client
class MCPClient {
  private ws: WebSocket;
  
  constructor(private wsUrl: string, private apiKey?: string) {}
  
  async connect() {
    this.ws = new WebSocket(this.wsUrl, {
      headers: this.apiKey ? {
        'Authorization': `Bearer ${this.apiKey}`
      } : undefined
    });
    
    return new Promise((resolve, reject) => {
      this.ws.on('open', resolve);
      this.ws.on('error', reject);
    });
  }
  
  async callTool(name: string, args: any) {
    const request = {
      jsonrpc: '2.0',
      method: 'tools/call',
      params: { name, arguments: args },
      id: Date.now()
    };
    
    this.ws.send(JSON.stringify(request));
    
    return new Promise((resolve) => {
      this.ws.once('message', (data) => {
        resolve(JSON.parse(data.toString()));
      });
    });
  }
}

// Create AI assistant with MCP tools
const mcp = new MCPClient('wss://skyfi-mcp.fly.dev', 'your-api-key');
await mcp.connect();

const assistant = createAssistant({
  tools: {
    searchSatelliteImages: {
      description: 'Search for satellite imagery',
      parameters: z.object({
        aoi: z.string(),
        fromDate: z.string(),
        toDate: z.string()
      }),
      execute: async (args) => {
        return mcp.callTool('skyfi_search_archives', args);
      }
    }
  }
});
```

## OpenAI

```python
from openai import OpenAI
import json
import asyncio
import websockets

class MCPToolWrapper:
    def __init__(self, ws_url="wss://skyfi-mcp.fly.dev", api_key=None):
        self.ws_url = ws_url
        self.api_key = api_key
    
    async def call(self, tool_name, **kwargs):
        async with websockets.connect(
            self.ws_url,
            extra_headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else None
        ) as websocket:
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": kwargs},
                "id": 1
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            return json.loads(response)

# Setup OpenAI with function calling
client = OpenAI()
mcp = MCPToolWrapper(api_key="your-skyfi-api-key")

# Define tools for OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_satellite_images",
            "description": "Search for satellite imagery in a specific area and time range",
            "parameters": {
                "type": "object",
                "properties": {
                    "aoi": {"type": "string", "description": "Area of interest as WKT polygon"},
                    "fromDate": {"type": "string", "description": "Start date (ISO format or natural language)"},
                    "toDate": {"type": "string", "description": "End date (ISO format or natural language)"}
                },
                "required": ["aoi", "fromDate", "toDate"]
            }
        }
    }
]

# Use in conversation
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Find satellite images of Manhattan from last week"}],
    tools=tools,
    tool_choice="auto"
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        if tool_call.function.name == "search_satellite_images":
            args = json.loads(tool_call.function.arguments)
            result = asyncio.run(mcp.call("skyfi_search_archives", **args))
            # Process result...
```

## Anthropic SDK

```python
from anthropic import Anthropic
import asyncio
from mcp_client import MCPToolWrapper  # Reuse from OpenAI example

client = Anthropic()
mcp = MCPToolWrapper(api_key="your-skyfi-api-key")

# Define MCP tools for Claude
tools = [
    {
        "name": "skyfi_search",
        "description": "Search for satellite imagery",
        "input_schema": {
            "type": "object",
            "properties": {
                "aoi": {"type": "string"},
                "fromDate": {"type": "string"},
                "toDate": {"type": "string"}
            },
            "required": ["aoi", "fromDate", "toDate"]
        }
    }
]

# Use with Claude API
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "Search for recent satellite images of Tokyo"
    }]
)

# Handle tool use
if message.stop_reason == "tool_use":
    tool_use = message.content[0]
    result = asyncio.run(mcp.call("skyfi_search_archives", **tool_use.input))
    
    # Continue conversation with result
    followup = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        messages=[
            {"role": "user", "content": "Search for recent satellite images of Tokyo"},
            {"role": "assistant", "content": message.content},
            {"role": "user", "content": f"Tool result: {result}"}
        ]
    )
```

## Google Gemini

```python
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
import asyncio
from mcp_client import MCPToolWrapper

# Configure Gemini
genai.configure(api_key="your-gemini-api-key")
mcp = MCPToolWrapper(api_key="your-skyfi-api-key")

# Define function declarations
search_images = FunctionDeclaration(
    name="search_satellite_images",
    description="Search for satellite imagery",
    parameters={
        "type": "object",
        "properties": {
            "aoi": {"type": "string"},
            "fromDate": {"type": "string"},
            "toDate": {"type": "string"}
        },
        "required": ["aoi", "fromDate", "toDate"]
    }
)

# Create tool
skyfi_tool = Tool(function_declarations=[search_images])

# Create model with tools
model = genai.GenerativeModel('gemini-pro', tools=[skyfi_tool])

# Start conversation
chat = model.start_chat()
response = chat.send_message("Find satellite images of Paris from January 2024")

# Handle function calls
for part in response.parts:
    if part.function_call:
        if part.function_call.name == "search_satellite_images":
            args = dict(part.function_call.args)
            result = asyncio.run(mcp.call("skyfi_search_archives", **args))
            
            # Send result back
            response = chat.send_message(f"Function result: {result}")
```

## ADK (Anthropic Development Kit)

```python
from adk import ADK
from adk.tools import Tool, ToolResult
import asyncio
from mcp_client import MCPToolWrapper

# Initialize ADK with MCP
adk = ADK(api_key="your-anthropic-key")
mcp = MCPToolWrapper(api_key="your-skyfi-api-key")

# Create MCP tool adapter
class SkyFiSearchTool(Tool):
    name = "search_satellite_images"
    description = "Search for satellite imagery"
    
    async def run(self, aoi: str, from_date: str, to_date: str) -> ToolResult:
        result = await mcp.call("skyfi_search_archives",
                               aoi=aoi,
                               fromDate=from_date,
                               toDate=to_date)
        return ToolResult(success=True, data=result)

# Register tool
adk.register_tool(SkyFiSearchTool())

# Use in ADK workflow
async def satellite_research_workflow(location: str):
    # Get location boundary
    boundary_tool = await adk.call_tool("osm_polygon_to_wkt", place_name=location)
    wkt = boundary_tool.data["wkt"]
    
    # Search for images
    images = await adk.call_tool("search_satellite_images",
                                aoi=wkt,
                                from_date="2024-01-01",
                                to_date="2024-12-31")
    
    # Analyze results
    analysis = await adk.generate(
        f"Analyze these satellite image results for {location}: {images.data}",
        system="You are a geospatial analyst"
    )
    
    return analysis

# Run workflow
result = asyncio.run(satellite_research_workflow("Manhattan"))
```

## Multi-User Cloud Deployment

For production multi-user access:

```python
# Server setup with auth headers
import os
os.environ['SKYFI_MULTI_USER'] = 'true'

# Client connection with auth
const client = new MCPClient('wss://skyfi-mcp.fly.dev', {
  headers: {
    'Authorization': 'Bearer user-specific-api-key'
  }
});
```

## Best Practices

1. **API Key Management**
   - Local: Store in environment variables
   - Cloud: Pass via Authorization headers
   - Never commit keys to version control

2. **Error Handling**
   - Always wrap MCP calls in try/catch
   - Handle WebSocket disconnections
   - Implement exponential backoff for retries

3. **Performance**
   - Cache frequently used results
   - Batch requests when possible
   - Use connection pooling for WebSockets

4. **Security**
   - Validate all inputs before sending to MCP
   - Use HTTPS/WSS in production
   - Implement rate limiting

## Troubleshooting

### Connection Issues
```bash
# Test WebSocket connection
wscat -c wss://skyfi-mcp.fly.dev -H "Authorization: Bearer your-api-key"

# Test local MCP
python -m mcp_skyfi --help
```

### Authentication Errors
- Verify API key is valid at app.skyfi.com
- Check Authorization header format: `Bearer <key>`
- Ensure SKYFI_API_KEY environment variable is set

### Tool Errors
- Verify tool name matches exactly (e.g., `skyfi_search_archives`)
- Check required parameters are provided
- Validate WKT polygon format for AOI

## Support

- GitHub Issues: https://github.com/NoaheCampbell/SkyFi-MCP/issues
- API Docs: https://docs.skyfi.com
- Discord: https://discord.gg/skyfi