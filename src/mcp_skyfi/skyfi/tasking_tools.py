"""SkyFi satellite tasking tools."""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json

from mcp.types import Tool

logger = logging.getLogger(__name__)


async def register_tasking_tools() -> List[Tool]:
    """Register satellite tasking tools."""
    return [
        Tool(
            name="skyfi_get_tasking_quote",
            description=(
                "Get detailed pricing quote and feasibility analysis for satellite tasking request. "
                "REQUIRED before ordering. Returns quote ID, pricing tiers, capture windows, and feasibility score."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of interest as WKT polygon"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Earliest acceptable capture date (ISO format or natural language)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Latest acceptable capture date (ISO format or natural language)"
                    },
                    "resolution": {
                        "type": "string",
                        "description": "Required resolution: 'high' (0.3-0.5m), 'medium' (0.5-1m), 'low' (1-3m)",
                        "enum": ["high", "medium", "low"],
                        "default": "medium"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Tasking priority: 'standard', 'priority', 'urgent'",
                        "enum": ["standard", "priority", "urgent"],
                        "default": "standard"
                    },
                    "cloud_coverage": {
                        "type": "number",
                        "description": "Maximum acceptable cloud coverage (0-100%)",
                        "default": 20
                    },
                    "off_nadir": {
                        "type": "number",
                        "description": "Maximum off-nadir angle in degrees (0-45)",
                        "default": 30
                    }
                },
                "required": ["aoi", "start_date", "end_date"]
            }
        ),
        Tool(
            name="skyfi_create_tasking_order",
            description=(
                "Confirm and create a tasking order using a previously generated quote. "
                "Requires quote_id from skyfi_get_tasking_quote and user confirmation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "quote_id": {
                        "type": "string",
                        "description": "Quote ID from skyfi_get_tasking_quote"
                    },
                    "selected_tier": {
                        "type": "string",
                        "description": "Selected pricing tier from the quote",
                        "enum": ["economy", "standard", "premium"]
                    },
                    "delivery_email": {
                        "type": "string",
                        "description": "Email address for delivery notification"
                    },
                    "special_instructions": {
                        "type": "string",
                        "description": "Any special capture instructions or requirements"
                    },
                    "confirm_price": {
                        "type": "number",
                        "description": "Confirm the expected price to prevent accidental orders"
                    }
                },
                "required": ["quote_id", "selected_tier", "confirm_price"]
            }
        ),
        Tool(
            name="skyfi_get_order_status",
            description=(
                "Get current status and progress information for an existing order. "
                "Returns status, progress percentage, estimated completion, and any issues."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to check status for"
                    },
                    "include_timeline": {
                        "type": "boolean",
                        "description": "Include detailed timeline of order events",
                        "default": False
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="skyfi_analyze_capture_feasibility",
            description=(
                "Analyze the feasibility of satellite imagery capture for a specific area and time period. "
                "Returns feasibility score, weather predictions, and satellite availability."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of interest as WKT polygon"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start of capture window"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End of capture window"
                    },
                    "required_conditions": {
                        "type": "object",
                        "properties": {
                            "max_cloud_cover": {"type": "number", "default": 20},
                            "min_sun_elevation": {"type": "number", "default": 30},
                            "avoid_snow": {"type": "boolean", "default": False}
                        }
                    }
                },
                "required": ["aoi", "start_date", "end_date"]
            }
        ),
        Tool(
            name="skyfi_predict_satellite_passes",
            description=(
                "Predict satellite passes and optimal capture windows for a specific area. "
                "Returns pass times, elevation angles, and quality scores."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of interest as WKT polygon"
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days to predict ahead (1-30)",
                        "default": 7
                    },
                    "satellites": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific satellites to check (optional)"
                    },
                    "min_elevation": {
                        "type": "number",
                        "description": "Minimum elevation angle in degrees",
                        "default": 60
                    }
                },
                "required": ["aoi"]
            }
        )
    ]


async def register_monitoring_tools() -> List[Tool]:
    """Register monitoring and notification tools."""
    return [
        Tool(
            name="skyfi_create_webhook_subscription",
            description=(
                "Create a webhook subscription for SkyFi notifications and alerts. "
                "Receive real-time updates for orders, new imagery, and monitoring alerts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "webhook_url": {
                        "type": "string",
                        "description": "HTTPS endpoint to receive notifications"
                    },
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["order.completed", "order.failed", "imagery.new", "monitoring.alert"]
                        },
                        "description": "Event types to subscribe to"
                    },
                    "secret": {
                        "type": "string",
                        "description": "Shared secret for webhook signature validation"
                    },
                    "active": {
                        "type": "boolean",
                        "description": "Whether webhook is active immediately",
                        "default": True
                    }
                },
                "required": ["webhook_url", "events"]
            }
        ),
        Tool(
            name="skyfi_setup_area_monitoring",
            description=(
                "Set up automated monitoring for new imagery in a specific area. "
                "Get alerts when new satellite images become available."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of interest as WKT polygon"
                    },
                    "monitoring_name": {
                        "type": "string",
                        "description": "Name for this monitoring setup"
                    },
                    "criteria": {
                        "type": "object",
                        "properties": {
                            "min_resolution": {"type": "number", "description": "Minimum resolution in meters"},
                            "max_cloud_cover": {"type": "number", "description": "Maximum cloud coverage %"},
                            "providers": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific providers to monitor"
                            }
                        }
                    },
                    "notification_email": {
                        "type": "string",
                        "description": "Email for notifications"
                    },
                    "webhook_url": {
                        "type": "string",
                        "description": "Optional webhook for real-time alerts"
                    },
                    "check_frequency": {
                        "type": "string",
                        "description": "How often to check: 'hourly', 'daily', 'weekly'",
                        "default": "daily"
                    }
                },
                "required": ["aoi", "monitoring_name"]
            }
        ),
        Tool(
            name="skyfi_get_notification_status",
            description=(
                "Check the status and delivery history of webhook notifications. "
                "Debug webhook issues and verify delivery."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "webhook_id": {
                        "type": "string",
                        "description": "Webhook subscription ID"
                    },
                    "hours": {
                        "type": "integer",
                        "description": "Number of hours of history to retrieve",
                        "default": 24
                    },
                    "include_payloads": {
                        "type": "boolean",
                        "description": "Include full notification payloads",
                        "default": False
                    }
                },
                "required": ["webhook_id"]
            }
        )
    ]