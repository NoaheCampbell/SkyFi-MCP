"""HTTP+SSE server implementation for MCP SkyFi."""
import json
import logging
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..skyfi.tools import register_skyfi_tools
from ..weather.tools import register_weather_tools
from ..osm.tools import register_osm_tools
from ..utils.http_auth import verify_api_key
from ..utils.http_spending import HTTPSpendingTracker
from ..utils.http_orders import HTTPOrderManager

logger = logging.getLogger(__name__)


class ToolRequest(BaseModel):
    """Request model for tool execution."""
    tool: str
    arguments: Dict[str, Any]


class MCPManifest(BaseModel):
    """MCP manifest response."""
    name: str
    version: str
    tools: list


# Global connections
redis_client: Optional[redis.Redis] = None
db_session_maker: Optional[sessionmaker] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global redis_client, db_session_maker
    
    # Initialize Redis
    redis_client = await redis.from_url(
        "redis://localhost:6379",
        encoding="utf-8",
        decode_responses=True
    )
    
    # Initialize database
    engine = create_async_engine(
        "sqlite+aiosqlite:///mcp_skyfi.db",
        echo=False
    )
    db_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    yield
    
    # Cleanup
    await redis_client.close()


# Create FastAPI app
app = FastAPI(
    title="MCP SkyFi Server",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-skyfi"}


@app.get("/mcp/manifest")
async def get_manifest() -> MCPManifest:
    """Get MCP manifest with available tools."""
    tools = []
    tools.extend(await register_skyfi_tools())
    tools.extend(await register_weather_tools())
    tools.extend(await register_osm_tools())
    
    return MCPManifest(
        name="mcp-skyfi",
        version="0.1.0",
        tools=[{
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema
        } for tool in tools]
    )


async def get_current_user(
    api_key: str = Header(alias="X-Skyfi-Api-Key")
) -> Dict[str, Any]:
    """Dependency to get current user from API key."""
    user = await verify_api_key(api_key, redis_client)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user


@app.post("/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Execute a tool with the given arguments."""
    try:
        # Create spending tracker for this user
        spending_tracker = HTTPSpendingTracker(
            redis_client=redis_client,
            user_id=user["id"]
        )
        
        # Import appropriate handler based on tool name
        if tool_name.startswith("skyfi_"):
            from ..skyfi.http_handlers import handle_skyfi_tool
            result = await handle_skyfi_tool(
                name=tool_name,
                arguments=request.arguments,
                user=user,
                spending_tracker=spending_tracker
            )
        elif tool_name.startswith("weather_"):
            from ..weather.handlers import handle_weather_tool
            result = await handle_weather_tool(tool_name, request.arguments)
        elif tool_name.startswith("osm_"):
            from ..osm.handlers import handle_osm_tool
            result = await handle_osm_tool(tool_name, request.arguments)
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
        
        # Convert TextContent to dict
        return {
            "success": True,
            "result": result[0].text if result else ""
        }
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sse/search/{search_id}")
async def search_progress(
    search_id: str,
    user: Dict = Depends(get_current_user)
):
    """Stream search progress via SSE."""
    async def generate():
        try:
            # Simulate progress updates
            for progress in range(0, 101, 10):
                data = {
                    "event": "progress",
                    "searchId": search_id,
                    "progress": progress,
                    "message": f"Searching archives... {progress}%"
                }
                yield json.dumps(data)
                
                # Check Redis for actual results
                result_key = f"search:{user['id']}:{search_id}"
                results = await redis_client.get(result_key)
                if results:
                    yield json.dumps({
                        "event": "complete",
                        "searchId": search_id,
                        "results": json.loads(results)
                    })
                    break
                    
                await asyncio.sleep(1)
                
        except Exception as e:
            yield json.dumps({
                "event": "error",
                "message": str(e)
            })
    
    return EventSourceResponse(generate())


@app.get("/spending/report")
async def spending_report(user: Dict = Depends(get_current_user)):
    """Get spending report for authenticated user."""
    tracker = HTTPSpendingTracker(redis_client, user["id"])
    
    total_spent = await tracker.get_total_spent()
    daily_spent = await tracker.get_daily_spent()
    remaining = 40.0 - total_spent  # Using config limit
    
    return {
        "userId": user["id"],
        "totalSpent": total_spent,
        "dailySpent": daily_spent,
        "remainingBudget": remaining,
        "limits": {
            "total": 40.0,
            "daily": 40.0,
            "perOrder": 20.0
        }
    }


@app.post("/orders/prepare")
async def prepare_order(
    request: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """Prepare an order (HTTP version of prepare_order tool)."""
    order_manager = HTTPOrderManager(redis_client)
    spending_tracker = HTTPSpendingTracker(redis_client, user["id"])
    
    # Check spending limits
    estimated_cost = request["estimated_cost"]
    total_spent = await spending_tracker.get_total_spent()
    
    if estimated_cost > 20.0:  # Max order cost
        raise HTTPException(
            status_code=400,
            detail=f"Order exceeds maximum single order limit (${estimated_cost} > $20)"
        )
    
    if total_spent + estimated_cost > 40.0:  # Total limit
        raise HTTPException(
            status_code=400,
            detail=f"Order would exceed budget (${total_spent} + ${estimated_cost} > $40)"
        )
    
    # Create pending order
    token = await order_manager.create_pending_order(
        user_id=user["id"],
        order_details=request,
        estimated_cost=estimated_cost
    )
    
    return {
        "token": token,
        "confirmationCode": f"CONFIRM-{token[:6]}",
        "expiresIn": 300,
        "estimatedCost": estimated_cost,
        "currentSpending": total_spent,
        "remainingBudget": 40.0 - total_spent
    }


@app.post("/orders/confirm")
async def confirm_order(
    request: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """Confirm a pending order."""
    order_manager = HTTPOrderManager(redis_client)
    spending_tracker = HTTPSpendingTracker(redis_client, user["id"])
    
    token = request["token"]
    confirmation_code = request["confirmationCode"]
    
    # Validate order
    order = await order_manager.get_pending_order(token, user["id"])
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found or expired"
        )
    
    # Verify confirmation code
    if confirmation_code != f"CONFIRM-{token[:6]}":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation code"
        )
    
    # Process order (would call SkyFi API here)
    # ... actual order processing ...
    
    # Record spending
    await spending_tracker.add_spending(order["estimated_cost"])
    
    return {
        "success": True,
        "orderId": "12345",  # From SkyFi API
        "cost": order["estimated_cost"],
        "message": "Order placed successfully"
    }


def create_http_server():
    """Create and configure the HTTP server."""
    return app