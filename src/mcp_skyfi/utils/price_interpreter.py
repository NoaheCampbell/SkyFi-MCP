"""Interpret prices from search results - detect if per km² or total."""
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger(__name__)


def interpret_archive_price(
    archive: Dict[str, Any], 
    area_km2: Optional[float] = None
) -> Tuple[float, float, str]:
    """
    Interpret price from archive data.
    
    SkyFi API returns price per km² in search results.
    We need to calculate total price based on area.
    
    Args:
        archive: Archive data from search
        area_km2: Area in square kilometers (if known)
        
    Returns:
        (price_per_km2, total_price, explanation)
    """
    # Get the price from archive
    listed_price = archive.get('price', 0)
    
    # Check if there's explicit price type info
    price_type = archive.get('priceType', 'PER_KM2')  # Default assumption
    
    # SkyFi typically shows price per km²
    if price_type == 'TOTAL' or archive.get('totalPrice'):
        # Rare case - total price given
        total_price = archive.get('totalPrice', listed_price)
        if area_km2 and area_km2 > 0:
            price_per_km2 = total_price / area_km2
        else:
            price_per_km2 = listed_price
        explanation = "Price shown is total cost"
    else:
        # Normal case - price per km²
        price_per_km2 = listed_price
        
        if area_km2:
            # Calculate total with minimum area
            billable_area = max(area_km2, 25.0)  # 25 km² minimum
            total_price = price_per_km2 * billable_area
            
            if area_km2 < 25.0:
                explanation = f"${price_per_km2:.2f}/km² × 25 km² (minimum billing)"
            else:
                explanation = f"${price_per_km2:.2f}/km² × {area_km2:.1f} km²"
        else:
            # No area provided - can't calculate total
            total_price = price_per_km2  # Best guess
            explanation = f"${price_per_km2:.2f}/km² (area unknown)"
    
    return price_per_km2, total_price, explanation


def estimate_order_cost(
    archive: Dict[str, Any],
    area_km2: float
) -> Dict[str, Any]:
    """
    Estimate the total cost for an order.
    
    Args:
        archive: Archive data from search
        area_km2: Actual area in km²
        
    Returns:
        Dict with cost breakdown
    """
    price_per_km2, total_price, explanation = interpret_archive_price(archive, area_km2)
    
    # Additional fees (if any)
    processing_fee = archive.get('processingFee', 0)
    delivery_fee = archive.get('deliveryFee', 0)
    
    final_total = total_price + processing_fee + delivery_fee
    
    return {
        'price_per_km2': price_per_km2,
        'area_km2': area_km2,
        'billable_area_km2': max(area_km2, 25.0),
        'base_cost': total_price,
        'processing_fee': processing_fee,
        'delivery_fee': delivery_fee,
        'total_cost': final_total,
        'explanation': explanation,
        'breakdown': [
            f"Base: {explanation} = ${total_price:.2f}",
            f"Processing fee: ${processing_fee:.2f}" if processing_fee > 0 else None,
            f"Delivery fee: ${delivery_fee:.2f}" if delivery_fee > 0 else None,
        ]
    }


def format_price_info(archive: Dict[str, Any], area_km2: Optional[float] = None) -> str:
    """
    Format price information clearly for users.
    
    Args:
        archive: Archive data
        area_km2: Known area (optional)
        
    Returns:
        Formatted price string
    """
    price_per_km2, total_price, explanation = interpret_archive_price(archive, area_km2)
    
    if area_km2:
        # Show both per km² and total
        if area_km2 < 25.0:
            return f"${price_per_km2:.2f}/km² (Total: ${total_price:.2f} for 25 km² minimum)"
        else:
            return f"${price_per_km2:.2f}/km² (Total: ${total_price:.2f} for {area_km2:.1f} km²)"
    else:
        # Just show per km² price
        return f"${price_per_km2:.2f}/km²"


def needs_price_clarification(search_results: list) -> bool:
    """
    Check if we need to clarify pricing with the user.
    
    Args:
        search_results: List of archives from search
        
    Returns:
        True if prices seem ambiguous
    """
    if not search_results:
        return False
    
    # Check for unusual price patterns that might indicate total pricing
    prices = [r.get('price', 0) for r in search_results]
    
    # If all prices are round numbers (100, 500, 1000), might be totals
    round_prices = [p for p in prices if p > 0 and p % 100 == 0]
    if len(round_prices) == len(prices) and len(prices) > 2:
        return True
    
    # If prices are very high (>$50/km²), double-check
    high_prices = [p for p in prices if p > 50]
    if high_prices:
        return True
    
    return False