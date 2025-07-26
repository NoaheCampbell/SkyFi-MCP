"""Budget alert system for consistent spending warnings."""
import logging
from typing import Tuple, Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class BudgetStatus(Enum):
    """Budget status levels."""
    SAFE = "safe"           # < 50% spent
    WARNING = "warning"     # 50-75% spent  
    CRITICAL = "critical"   # 75-90% spent
    DANGER = "danger"       # > 90% spent
    EXCEEDED = "exceeded"   # > 100% spent


def get_budget_status(spent: float, limit: float) -> Tuple[BudgetStatus, float]:
    """
    Get budget status and percentage.
    
    Returns:
        (status, percentage_spent)
    """
    if limit <= 0:
        return BudgetStatus.SAFE, 0.0
    
    percentage = (spent / limit) * 100
    
    if percentage >= 100:
        return BudgetStatus.EXCEEDED, percentage
    elif percentage >= 90:
        return BudgetStatus.DANGER, percentage
    elif percentage >= 75:
        return BudgetStatus.CRITICAL, percentage
    elif percentage >= 50:
        return BudgetStatus.WARNING, percentage
    else:
        return BudgetStatus.SAFE, percentage


def format_budget_alert(spent: float, limit: float, context: str = "") -> str:
    """
    Format a budget alert message with visual indicators.
    
    Args:
        spent: Amount spent
        limit: Budget limit
        context: Additional context (e.g., "daily", "total")
        
    Returns:
        Formatted alert string
    """
    status, percentage = get_budget_status(spent, limit)
    remaining = max(0, limit - spent)
    
    # Status indicators
    indicators = {
        BudgetStatus.SAFE: "🟢",
        BudgetStatus.WARNING: "🟡", 
        BudgetStatus.CRITICAL: "🟠",
        BudgetStatus.DANGER: "🔴",
        BudgetStatus.EXCEEDED: "💀"
    }
    
    # Progress bar
    filled = int(percentage / 10)  # 10 segments
    filled = min(filled, 10)  # Cap at 10
    empty = 10 - filled
    
    if status == BudgetStatus.EXCEEDED:
        bar = "█" * 10 + "▌" * min(int((percentage - 100) / 10), 5)
    else:
        bar = "█" * filled + "░" * empty
    
    # Build alert
    indicator = indicators[status]
    alert = f"{indicator} Budget {context}: ${spent:.2f} / ${limit:.2f} ({percentage:.1f}%)\n"
    alert += f"   [{bar}] ${remaining:.2f} remaining"
    
    # Add warnings
    if status == BudgetStatus.EXCEEDED:
        alert += f"\n   ⚠️  BUDGET EXCEEDED by ${spent - limit:.2f}!"
    elif status == BudgetStatus.DANGER:
        alert += f"\n   ⚠️  Only ${remaining:.2f} left! (90% spent)"
    elif status == BudgetStatus.CRITICAL:
        alert += f"\n   ⚠️  Budget running low - 75% spent"
    elif status == BudgetStatus.WARNING:
        alert += f"\n   ℹ️  Half of budget used"
    
    return alert


def should_show_alert(spent: float, limit: float, last_alert_percentage: Optional[float] = None) -> bool:
    """
    Determine if we should show a budget alert.
    Shows alerts at: 50%, 75%, 90%, 100% thresholds.
    
    Args:
        spent: Current spending
        limit: Budget limit
        last_alert_percentage: Last percentage when alert was shown
        
    Returns:
        True if alert should be shown
    """
    if limit <= 0:
        return False
        
    current_percentage = (spent / limit) * 100
    
    # Always show if exceeded
    if current_percentage >= 100:
        return True
    
    # Check threshold crossings
    thresholds = [50, 75, 90]
    
    if last_alert_percentage is None:
        # First time - show if above any threshold
        return any(current_percentage >= t for t in thresholds)
    
    # Show if crossed a new threshold
    for threshold in thresholds:
        if last_alert_percentage < threshold <= current_percentage:
            return True
    
    return False


def format_spending_summary(cost_tracker, config) -> str:
    """
    Format a comprehensive spending summary.
    
    Args:
        cost_tracker: Cost tracker instance
        config: Config with limits
        
    Returns:
        Formatted summary with all budget alerts
    """
    total_spent = cost_tracker.get_total_spent()
    daily_spent = cost_tracker.get_daily_spent()
    
    summary = "💰 Spending Summary\n"
    summary += "━" * 40 + "\n\n"
    
    # Total budget
    summary += format_budget_alert(total_spent, config.cost_limit, "Total") + "\n\n"
    
    # Daily budget
    summary += format_budget_alert(daily_spent, config.daily_limit, "Daily") + "\n\n"
    
    # Recent orders
    orders = cost_tracker.get_order_history()
    if orders:
        summary += "📋 Recent Orders:\n"
        for order in orders[-3:]:  # Last 3
            summary += f"   • ${order['cost']:.2f} - {order['timestamp']}\n"
    
    return summary


def check_order_feasibility(order_cost: float, cost_tracker, config) -> Tuple[bool, str]:
    """
    Check if an order is feasible given current budgets.
    
    Returns:
        (is_feasible, warning_message)
    """
    total_spent = cost_tracker.get_total_spent()
    daily_spent = cost_tracker.get_daily_spent()
    
    warnings = []
    
    # Check total budget
    if total_spent + order_cost > config.cost_limit:
        warnings.append(f"❌ Would exceed total budget (${total_spent:.2f} + ${order_cost:.2f} > ${config.cost_limit:.2f})")
    
    # Check daily budget
    if daily_spent + order_cost > config.daily_limit:
        warnings.append(f"❌ Would exceed daily budget (${daily_spent:.2f} + ${order_cost:.2f} > ${config.daily_limit:.2f})")
    
    # Check if we're close to limits
    total_after = total_spent + order_cost
    total_status, total_pct = get_budget_status(total_after, config.cost_limit)
    
    if total_status in [BudgetStatus.CRITICAL, BudgetStatus.DANGER]:
        warnings.append(f"⚠️  Would use {total_pct:.1f}% of total budget")
    
    is_feasible = len([w for w in warnings if w.startswith("❌")]) == 0
    
    return is_feasible, "\n".join(warnings)