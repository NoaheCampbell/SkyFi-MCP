"""SkyFi tool definitions for MCP."""
from typing import List

from mcp.types import Tool


async def register_skyfi_tools() -> List[Tool]:
    """Register SkyFi tools with the MCP server."""
    tools = [
        Tool(
            name="skyfi_search_archives",
            description="Search for satellite imagery. Supports natural language dates like 'last week', 'past month', 'yesterday'. Automatically uses LOW resolution to minimize costs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "aoi": {
                        "type": "string",
                        "description": "Area of Interest as WKT polygon (e.g., POLYGON((lon1 lat1, lon2 lat2, ...)))"
                    },
                    "fromDate": {
                        "type": "string",
                        "description": "Start date (supports natural language: 'yesterday', 'last week', '2 weeks ago', 'January 15', or ISO format)"
                    },
                    "toDate": {
                        "type": "string",
                        "description": "End date (supports natural language: 'today', 'now', or ISO format)"
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
        Tool(
            name="skyfi_list_orders",
            description="Get list of all satellite image orders with their current status (processing, complete, failed). Shows order IDs, status, and download instructions for completed orders. Use this to check order status or get download links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_type": {
                        "type": "string",
                        "enum": ["ARCHIVE", "TASKING"],
                        "description": "Filter by order type (optional)"
                    },
                    "page_size": {
                        "type": "integer",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                        "description": "Number of orders per page"
                    },
                    "page_number": {
                        "type": "integer",
                        "default": 0,
                        "minimum": 0,
                        "description": "Page number (0-indexed)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="skyfi_get_download_url",
            description="Download a completed order file. Automatically downloads to temp directory and returns the file path.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID from the confirmed order or order list"
                    },
                    "deliverable_type": {
                        "type": "string",
                        "enum": ["image", "payload", "tiles"],
                        "default": "image",
                        "description": "Type of deliverable to download (image=visual imagery, payload=full package, tiles=tile service)"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="skyfi_download_order",
            description="Download a completed order file to local disk. Automatically handles authentication.",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID from the confirmed order or order list"
                    },
                    "deliverable_type": {
                        "type": "string",
                        "enum": ["image", "payload", "tiles"],
                        "default": "image",
                        "description": "Type of deliverable to download (image=visual imagery, payload=full package, tiles=tile service)"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "Path where to save the file (optional, defaults to order_ID_type.zip)"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="skyfi_save_search",
            description="Save a search configuration for quick re-use later",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Unique name for this saved search"
                    },
                    "aoi": {
                        "type": "string",
                        "description": "Area of Interest as WKT polygon"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date (can be natural language)"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date (can be natural language)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of this search"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags for categorization (e.g., 'project-x', 'monthly')"
                    },
                    "resolution": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                        "description": "Preferred resolution"
                    },
                    "max_cloud_cover": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Maximum acceptable cloud cover percentage"
                    }
                },
                "required": ["name", "aoi", "from_date", "to_date"]
            }
        ),
        Tool(
            name="skyfi_list_saved_searches",
            description="List all saved searches",
            inputSchema={
                "type": "object",
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["created_at", "last_used", "use_count", "name"],
                        "default": "created_at",
                        "description": "Sort order"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="skyfi_run_saved_search",
            description="Run a previously saved search by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_name": {
                        "type": "string",
                        "description": "Name or ID of the saved search"
                    },
                    "override_dates": {
                        "type": "boolean",
                        "default": False,
                        "description": "Use current dates instead of saved dates"
                    }
                },
                "required": ["search_name"]
            }
        ),
        Tool(
            name="skyfi_multi_location_search",
            description="Search multiple locations at once. Provide either a list of WKT polygons or points to search around.",
            inputSchema={
                "type": "object",
                "properties": {
                    "locations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of WKT polygons to search"
                    },
                    "points": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "description": "List of [longitude, latitude] points to search around"
                    },
                    "buffer_km": {
                        "type": "number",
                        "default": 5.0,
                        "description": "Buffer radius in km (only used with points)"
                    },
                    "from_date": {
                        "type": "string",
                        "description": "Start date for all locations"
                    },
                    "to_date": {
                        "type": "string",
                        "description": "End date for all locations"
                    },
                    "resolution": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
                        "description": "Desired resolution"
                    }
                },
                "required": ["from_date", "to_date"]
            }
        ),
        Tool(
            name="skyfi_export_order_history",
            description="Export order history to various formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["csv", "json", "html", "markdown"],
                        "default": "csv",
                        "description": "Export format"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output file path (auto-generated if not provided)"
                    },
                    "include_summary": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include summary statistics"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="skyfi_estimate_cost",
            description="Get accurate cost estimate for an order with detailed breakdown",
            inputSchema={
                "type": "object",
                "properties": {
                    "archive_id": {
                        "type": "string",
                        "description": "Archive ID from search results"
                    },
                    "area_km2": {
                        "type": "number",
                        "description": "Area in square kilometers"
                    },
                    "include_fees": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include processing fees in estimate"
                    }
                },
                "required": ["archive_id", "area_km2"]
            }
        ),
        Tool(
            name="skyfi_compare_costs",
            description="Compare costs across multiple archives for the same area",
            inputSchema={
                "type": "object",
                "properties": {
                    "archive_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of archive IDs to compare"
                    },
                    "area_km2": {
                        "type": "number",
                        "description": "Area in square kilometers"
                    }
                },
                "required": ["archive_ids", "area_km2"]
            }
        ),
        Tool(
            name="skyfi_authenticate",
            description="Generate a secure authentication link for setting up your SkyFi API key. Use this instead of typing your API key in chat.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="skyfi_check_auth",
            description="Check current authentication status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
    ]
    
    # Add budget tools
    from .budget_tools import register_budget_tools
    budget_tools = await register_budget_tools()
    tools.extend(budget_tools)
    
    # Add account tools
    from .account_tools import register_account_tools
    account_tools = await register_account_tools()
    tools.extend(account_tools)
    
    return tools