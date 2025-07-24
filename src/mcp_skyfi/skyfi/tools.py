"""SkyFi tool definitions for MCP."""
from typing import List

from mcp.types import Tool


async def register_skyfi_tools() -> List[Tool]:
    """Register SkyFi tools with the MCP server."""
    return [
        Tool(
            name="skyfi_search_archives",
            description="Search for available satellite imagery in the SkyFi catalog (automatically uses LOW resolution to minimize costs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of Interest as WKT polygon (e.g., POLYGON((lon1 lat1, lon2 lat2, ...)))"
                    },
                    "fromDate": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Start date for search (ISO 8601 format, e.g., 2024-01-01T00:00:00Z)"
                    },
                    "toDate": {
                        "type": "string",
                        "format": "date-time",
                        "description": "End date for search (ISO 8601 format)"
                    },
                    "openData": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include open data sources"
                    },
                    "productTypes": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["DAY", "NIGHT", "MULTISPECTRAL", "SAR"]
                        },
                        "description": "Types of imagery products to search for"
                    },
                    "resolution": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                        "description": "Desired resolution level"
                    }
                },
                "required": ["aoi", "fromDate", "toDate"]
            }
        ),
        # ORDERING DISABLED FOR SAFETY - Use skyfi_check_price instead
        # Tool(
        #     name="skyfi_order_archive",
        #     description="Order satellite imagery from the catalog with delivery to cloud storage (Cost limit: $40, uses lowest quality by default)",
        #     inputSchema={
        #         "type": "object",
        #         "properties": {
        #             "aoi": {
        #                 "type": "string",
        #                 "description": "Area of Interest as WKT polygon"
        #             },
        #             "archiveId": {
        #                 "type": "string",
        #                 "description": "Archive ID from search results"
        #             },
        #             "deliveryDriver": {
        #                 "type": "string",
        #                 "enum": ["S3", "GS", "AZURE"],
        #                 "description": "Cloud storage provider (S3=AWS, GS=Google Cloud, AZURE=Azure)"
        #             },
        #             "deliveryParams": {
        #                 "type": "object",
        #                 "description": "Provider-specific delivery parameters",
        #                 "additionalProperties": True
        #             },
        #             "estimated_cost": {
        #                 "type": "number",
        #                 "description": "Estimated cost from search results (for validation)"
        #             }
        #         },
        #         "required": ["aoi", "archiveId", "deliveryDriver", "deliveryParams"]
        #     }
        # ),
        Tool(
            name="skyfi_get_user",
            description="Get current authenticated user information and account details",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="skyfi_spending_report",
            description="Get spending report and budget status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="skyfi_get_pricing",
            description="Get ALL pricing options for satellite tasking - shows costs for different providers and resolutions (ignores budget limits)",
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of Interest as WKT polygon (optional - leave blank for general pricing)"
                    },
                    "show_all": {
                        "type": "boolean",
                        "default": True,
                        "description": "Show all prices regardless of budget (default: true)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="skyfi_prepare_order",
            description="Prepare an order for satellite imagery - creates a preview that requires confirmation",
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of Interest as WKT polygon"
                    },
                    "archiveId": {
                        "type": "string",
                        "description": "Archive ID from search results"
                    },
                    "estimated_cost": {
                        "type": "number",
                        "description": "Estimated cost from search/pricing results"
                    }
                },
                "required": ["aoi", "archiveId", "estimated_cost"]
            }
        ),
        Tool(
            name="skyfi_confirm_order",
            description="Confirm a prepared order using the confirmation token and code",
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "Order token from prepare_order"
                    },
                    "confirmation_code": {
                        "type": "string",
                        "description": "Confirmation code (format: CONFIRM-XXXXXX)"
                    }
                },
                "required": ["token", "confirmation_code"]
            }
        ),
    ]