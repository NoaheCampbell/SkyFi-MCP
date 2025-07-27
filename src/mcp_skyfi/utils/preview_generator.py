"""Generate preview information and ASCII art for satellite images."""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_search_preview(archive: Dict[str, Any], area_km2: Optional[float] = None) -> str:
    """
    Generate a text preview for a satellite image from search results.
    
    Args:
        archive: Archive data from search results
        
    Returns:
        Preview text with ASCII representation
    """
    # Extract key information
    archive_id = archive.get('archiveId', 'N/A')
    satellite = archive.get('satellite', 'Unknown')
    resolution = archive.get('resolution', 'N/A')
    cloud_cover = archive.get('cloudCover', 0)
    capture_date = archive.get('captureDate', 'N/A')
    
    # Get proper price formatting
    from ..utils.price_interpreter import format_price_info
    price_info = format_price_info(archive, area_km2)
    
    # Extract preview URLs if available
    preview_url = archive.get('previewUrl') or archive.get('thumbnailUrl')
    quicklook_url = archive.get('quicklookUrl')
    
    # Generate ASCII representation based on cloud cover
    ascii_preview = generate_cloud_cover_ascii(cloud_cover)
    
    # Build preview text
    preview = f"┌─ {satellite} ({resolution}m) ─────────────┐\n"
    preview += f"│ ID: {archive_id[:12]}...         │\n"
    preview += f"│ Date: {capture_date[:10]}              │\n"
    preview += f"│ Clouds: {cloud_cover}%                         │\n"
    preview += f"│ 💵 {price_info:<28} │\n"
    preview += f"│                                    │\n"
    
    # Add ASCII art
    for line in ascii_preview.split('\n'):
        preview += f"│ {line:<34} │\n"
    
    preview += f"│                                    │\n"
    
    # Add preview URL if available
    if preview_url:
        preview += f"│ 🖼️  Preview available              │\n"
    if quicklook_url:
        preview += f"│ 👁️  Quicklook available            │\n"
        
    preview += f"└────────────────────────────────────┘"
    
    return preview


def generate_cloud_cover_ascii(cloud_percent: float) -> str:
    """
    Generate ASCII art representation of cloud coverage.
    
    Args:
        cloud_percent: Cloud coverage percentage (0-100)
        
    Returns:
        ASCII art string
    """
    if cloud_percent < 10:
        # Clear sky
        return (
            "     ☀️              \n"
            "                    \n"
            " ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲  \n"
            " ╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱  "
        )
    elif cloud_percent < 30:
        # Partly cloudy
        return (
            "    ☁️   ☀️         \n"
            "                    \n"
            " ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲  \n"
            " ╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱  "
        )
    elif cloud_percent < 60:
        # Cloudy
        return (
            "   ☁️  ☁️  ☁️       \n"
            "      ☁️            \n"
            " ╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲  \n"
            " ╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱  "
        )
    else:
        # Very cloudy
        return (
            " ☁️☁️☁️☁️☁️☁️☁️    \n"
            " ☁️☁️☁️☁️☁️☁️☁️    \n"
            " ░░░░░░░░░░░░░░░░  \n"
            " ░░░░░░░░░░░░░░░░  "
        )


def format_search_results_with_previews(results: list, max_results: int = 5, area_km2: Optional[float] = None) -> str:
    """
    Format search results with preview boxes.
    
    Args:
        results: List of archive results
        max_results: Maximum number of results to show with previews
        area_km2: Search area in km² (for cost calculation)
        
    Returns:
        Formatted text with previews
    """
    if not results:
        return "No satellite images found."
    
    text = f"🛰️  Found {len(results)} satellite images:\n\n"
    
    # Show detailed previews for first few results
    for idx, archive in enumerate(results[:max_results], 1):
        text += f"{idx}. "
        text += generate_search_preview(archive, area_km2)
        text += "\n\n"
    
    # If there are more results, show summary
    if len(results) > max_results:
        text += f"... and {len(results) - max_results} more results\n\n"
        
        # Show brief summary of remaining results
        text += "Additional results (without preview):\n"
        for idx, archive in enumerate(results[max_results:max_results+10], max_results+1):
            satellite = archive.get('satellite', 'Unknown')
            date = archive.get('captureDate', 'N/A')[:10]
            price = archive.get('price', 0)
            clouds = archive.get('cloudCover', 0)
            
            # Format price properly for summary
            if area_km2:
                from ..utils.price_interpreter import interpret_archive_price
                _, total_price, _ = interpret_archive_price(archive, area_km2)
                text += f"{idx}. {satellite} - {date} - ${total_price:.2f} - {clouds}% clouds\n"
            else:
                text += f"{idx}. {satellite} - {date} - ${price:.2f}/km² - {clouds}% clouds\n"
        
        if len(results) > max_results + 10:
            text += f"\n... and {len(results) - max_results - 10} more\n"
    
    return text


def generate_order_status_preview(order: Dict[str, Any]) -> str:
    """
    Generate a visual representation of order status.
    
    Args:
        order: Order data
        
    Returns:
        Visual status representation
    """
    status = order.get('status', 'UNKNOWN')
    order_type = order.get('orderType', 'ARCHIVE')
    
    # Status visualization
    status_bar = {
        'CREATED': '🆕 [▱▱▱▱▱▱▱▱▱▱] Created',
        'PROVIDER_PENDING': '⏳ [██▱▱▱▱▱▱▱▱] Provider Processing',
        'PROCESSING_PENDING': '🔄 [██████▱▱▱▱] Processing Image',
        'PROCESSING_COMPLETE': '✅ [██████████] Complete!',
        'FAILED': '❌ [××××××××××] Failed'
    }.get(status, '🔵 [▱▱▱▱▱▱▱▱▱▱] Unknown')
    
    return status_bar


def estimate_area_preview(area_km2: float) -> str:
    """
    Generate a visual representation of area size.
    
    Args:
        area_km2: Area in square kilometers
        
    Returns:
        Visual comparison to help users understand the size
    """
    # Compare to known areas
    if area_km2 < 1:
        comparison = "< Central Park"
        visual = "▫️"
    elif area_km2 < 10:
        comparison = "≈ Small town"
        visual = "◽"
    elif area_km2 < 50:
        comparison = "≈ City district"
        visual = "◻️"
    elif area_km2 < 200:
        comparison = "≈ Small city"
        visual = "⬜"
    elif area_km2 < 1000:
        comparison = "≈ Large city"
        visual = "🏙️"
    else:
        comparison = "≈ Metropolitan area"
        visual = "🌆"
    
    return f"{visual} {area_km2:.1f} km² ({comparison})"


def format_cost_breakdown(cost_components: Dict[str, float], total_cost: float) -> str:
    """
    Format a cost breakdown for display.
    
    Args:
        cost_components: Dictionary of cost components
        total_cost: Total cost
        
    Returns:
        Formatted cost breakdown string
    """
    text = "💰 Cost Breakdown:\n"
    text += "─" * 30 + "\n"
    
    # Show each component
    for component, amount in cost_components.items():
        text += f"  {component}: ${amount:.2f}\n"
    
    text += "─" * 30 + "\n"
    text += f"  Total: ${total_cost:.2f}\n"
    
    return text