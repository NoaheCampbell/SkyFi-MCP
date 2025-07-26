"""Improved cost estimation with exact calculations."""
import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, ROUND_UP

logger = logging.getLogger(__name__)


class CostEstimator:
    """Accurate cost estimation for SkyFi orders."""
    
    # Known fees and rules
    MINIMUM_AREA_KM2 = 25.0
    MINIMUM_ORDER_AREA_KM2 = 5.0
    PROCESSING_FEE_PERCENT = 0.03  # 3% processing fee (example)
    
    # Resolution multipliers (approximate)
    RESOLUTION_MULTIPLIERS = {
        "LOW": 1.0,
        "MEDIUM": 1.5,
        "HIGH": 2.0,
        "VERY_HIGH": 3.0
    }
    
    # Product type adjustments
    PRODUCT_ADJUSTMENTS = {
        "DAY": 1.0,
        "NIGHT": 1.2,
        "MULTISPECTRAL": 1.5,
        "SAR": 2.0
    }
    
    def __init__(self):
        """Initialize the cost estimator."""
        self.price_cache = {}
    
    def estimate_order_cost(
        self,
        archive: Dict[str, Any],
        area_km2: float,
        include_fees: bool = True
    ) -> Dict[str, Any]:
        """Calculate exact order cost with all fees.
        
        Args:
            archive: Archive data from search
            area_km2: Actual area in km²
            include_fees: Include processing fees
            
        Returns:
            Detailed cost breakdown
        """
        # Get base price per km²
        base_price_per_km2 = Decimal(str(archive.get('price', 0)))
        
        # Determine billable area (minimum 25 km²)
        actual_area = Decimal(str(area_km2))
        billable_area = max(actual_area, Decimal(str(self.MINIMUM_AREA_KM2)))
        
        # Calculate base cost
        base_cost = base_price_per_km2 * billable_area
        
        # Apply resolution adjustment if needed
        resolution = archive.get('resolution')
        if resolution and resolution in self.RESOLUTION_MULTIPLIERS:
            resolution_mult = Decimal(str(self.RESOLUTION_MULTIPLIERS[resolution]))
            base_cost *= resolution_mult
        
        # Apply product type adjustment
        product_type = archive.get('productType', 'DAY')
        if product_type in self.PRODUCT_ADJUSTMENTS:
            product_mult = Decimal(str(self.PRODUCT_ADJUSTMENTS[product_type]))
            base_cost *= product_mult
        
        # Calculate fees
        processing_fee = Decimal('0')
        if include_fees:
            processing_fee = base_cost * Decimal(str(self.PROCESSING_FEE_PERCENT))
        
        # Calculate total
        total_cost = base_cost + processing_fee
        
        # Round up to nearest cent
        total_cost = total_cost.quantize(Decimal('0.01'), rounding=ROUND_UP)
        
        # Build detailed breakdown
        breakdown = {
            'base_price_per_km2': float(base_price_per_km2),
            'actual_area_km2': float(actual_area),
            'billable_area_km2': float(billable_area),
            'base_cost': float(base_cost.quantize(Decimal('0.01'))),
            'processing_fee': float(processing_fee.quantize(Decimal('0.01'))),
            'total_cost': float(total_cost),
            'area_adjustment': billable_area > actual_area,
            'breakdown_text': self._format_breakdown(
                base_price_per_km2, actual_area, billable_area,
                base_cost, processing_fee, total_cost
            )
        }
        
        # Add any special notes
        notes = []
        if billable_area > actual_area:
            notes.append(f"Minimum billing area of {self.MINIMUM_AREA_KM2} km² applied")
        if resolution and resolution != "LOW":
            notes.append(f"{resolution} resolution pricing applied")
        if product_type != "DAY":
            notes.append(f"{product_type} product type pricing applied")
        
        breakdown['notes'] = notes
        
        return breakdown
    
    def _format_breakdown(
        self,
        price_per_km2: Decimal,
        actual_area: Decimal,
        billable_area: Decimal,
        base_cost: Decimal,
        processing_fee: Decimal,
        total: Decimal
    ) -> str:
        """Format cost breakdown as text.
        
        Returns:
            Formatted breakdown string
        """
        lines = []
        
        # Base calculation
        if billable_area > actual_area:
            lines.append(f"Base: ${price_per_km2}/km² × {billable_area} km² (min) = ${base_cost:.2f}")
            lines.append(f"      (Your area: {actual_area:.1f} km²)")
        else:
            lines.append(f"Base: ${price_per_km2}/km² × {billable_area:.1f} km² = ${base_cost:.2f}")
        
        # Fees
        if processing_fee > 0:
            lines.append(f"Processing fee (3%): ${processing_fee:.2f}")
        
        # Total
        lines.append(f"Total: ${total:.2f}")
        
        return "\n".join(lines)
    
    def estimate_bulk_cost(
        self,
        archives: List[Dict[str, Any]],
        area_km2: float
    ) -> Dict[str, Any]:
        """Estimate cost for ordering multiple archives.
        
        Args:
            archives: List of archives to order
            area_km2: Area for all orders
            
        Returns:
            Bulk cost estimate
        """
        total_cost = Decimal('0')
        individual_costs = []
        
        for archive in archives:
            cost_info = self.estimate_order_cost(archive, area_km2)
            total_cost += Decimal(str(cost_info['total_cost']))
            individual_costs.append({
                'archive_id': archive.get('archiveId', ''),
                'satellite': archive.get('satellite', ''),
                'cost': cost_info['total_cost'],
                'breakdown': cost_info['breakdown_text']
            })
        
        # Check for bulk discounts (hypothetical)
        discount = Decimal('0')
        if len(archives) >= 5:
            discount = total_cost * Decimal('0.05')  # 5% discount
        elif len(archives) >= 10:
            discount = total_cost * Decimal('0.10')  # 10% discount
        
        final_cost = total_cost - discount
        
        return {
            'order_count': len(archives),
            'subtotal': float(total_cost),
            'discount': float(discount),
            'total_cost': float(final_cost),
            'average_per_order': float(final_cost / len(archives)) if archives else 0,
            'individual_costs': individual_costs
        }
    
    def validate_budget(
        self,
        estimated_cost: float,
        available_budget: float,
        safety_margin: float = 0.05
    ) -> Tuple[bool, str]:
        """Validate if order fits within budget with safety margin.
        
        Args:
            estimated_cost: Estimated order cost
            available_budget: Available budget
            safety_margin: Safety margin (default 5%)
            
        Returns:
            (is_valid, message)
        """
        # Add safety margin to estimate
        safe_estimate = estimated_cost * (1 + safety_margin)
        
        if safe_estimate <= available_budget:
            return True, f"Order fits within budget (${safe_estimate:.2f} with {safety_margin*100:.0f}% margin <= ${available_budget:.2f})"
        else:
            shortfall = safe_estimate - available_budget
            return False, f"Order exceeds budget by ${shortfall:.2f} (including {safety_margin*100:.0f}% safety margin)"
    
    def get_affordable_options(
        self,
        archives: List[Dict[str, Any]],
        area_km2: float,
        budget: float
    ) -> List[Dict[str, Any]]:
        """Filter archives by what's affordable within budget.
        
        Args:
            archives: List of available archives
            area_km2: Area to order
            budget: Available budget
            
        Returns:
            List of affordable options with cost info
        """
        affordable = []
        
        for archive in archives:
            cost_info = self.estimate_order_cost(archive, area_km2)
            total_cost = cost_info['total_cost']
            
            if total_cost <= budget:
                affordable.append({
                    'archive': archive,
                    'cost_info': cost_info,
                    'budget_remaining': budget - total_cost,
                    'budget_usage_percent': (total_cost / budget) * 100
                })
        
        # Sort by best value (cloud cover vs price)
        affordable.sort(key=lambda x: (
            x['archive'].get('cloudCover', 100),  # Lower cloud cover first
            x['cost_info']['total_cost']  # Then by price
        ))
        
        return affordable
    
    def format_cost_comparison(
        self,
        archives: List[Dict[str, Any]],
        area_km2: float
    ) -> str:
        """Format a cost comparison table.
        
        Args:
            archives: Archives to compare
            area_km2: Area for comparison
            
        Returns:
            Formatted comparison text
        """
        text = "💰 Cost Comparison\n"
        text += "━" * 50 + "\n\n"
        text += f"Area: {area_km2:.1f} km² (billing: {max(area_km2, self.MINIMUM_AREA_KM2):.1f} km²)\n\n"
        
        # Headers
        text += "| Satellite | Date | Cloud% | $/km² | Total Cost |\n"
        text += "|-----------|------|--------|-------|------------|\n"
        
        for archive in archives[:10]:  # Limit to 10
            cost_info = self.estimate_order_cost(archive, area_km2)
            
            satellite = archive.get('satellite', 'Unknown')[:10]
            date = archive.get('captureDate', 'N/A')[:10]
            cloud = archive.get('cloudCover', 0)
            price_per_km2 = archive.get('price', 0)
            total = cost_info['total_cost']
            
            text += f"| {satellite:<9} | {date} | {cloud:>5.1f}% | ${price_per_km2:>5.2f} | ${total:>10.2f} |\n"
        
        if len(archives) > 10:
            text += f"\n... and {len(archives) - 10} more options\n"
        
        return text