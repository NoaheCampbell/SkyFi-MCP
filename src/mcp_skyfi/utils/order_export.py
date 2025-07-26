"""Export order history in various formats."""
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class OrderExporter:
    """Export order history to various formats."""
    
    def __init__(self):
        """Initialize the exporter."""
        pass
    
    def export_orders(
        self,
        orders: List[Dict[str, Any]],
        format: str = "csv",
        output_path: Optional[str] = None
    ) -> str:
        """Export orders to specified format.
        
        Args:
            orders: List of order data
            format: Export format (csv, json, html, markdown)
            output_path: Output file path (auto-generated if not provided)
            
        Returns:
            Path to exported file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"skyfi_orders_{timestamp}.{format}"
        
        if format == "csv":
            return self._export_csv(orders, output_path)
        elif format == "json":
            return self._export_json(orders, output_path)
        elif format == "html":
            return self._export_html(orders, output_path)
        elif format == "markdown":
            return self._export_markdown(orders, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self, orders: List[Dict[str, Any]], output_path: str) -> str:
        """Export orders as CSV.
        
        Args:
            orders: Order data
            output_path: Output file path
            
        Returns:
            File path
        """
        with open(output_path, 'w', newline='') as csvfile:
            if not orders:
                csvfile.write("No orders found\n")
                return output_path
            
            # Define fields
            fieldnames = [
                'order_id', 'order_code', 'order_type', 'status',
                'cost_usd', 'created_at', 'location', 'satellite',
                'capture_date', 'cloud_cover_percent', 'resolution',
                'area_km2', 'download_available'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for order in orders:
                row = {
                    'order_id': order.get('id', ''),
                    'order_code': order.get('orderCode', ''),
                    'order_type': order.get('orderType', ''),
                    'status': order.get('status', ''),
                    'cost_usd': order.get('orderCost', 0) / 100,  # Convert cents to dollars
                    'created_at': order.get('createdAt', ''),
                    'location': order.get('geocodeLocation', ''),
                    'satellite': '',
                    'capture_date': '',
                    'cloud_cover_percent': '',
                    'resolution': '',
                    'area_km2': '',
                    'download_available': 'Yes' if order.get('status') == 'PROCESSING_COMPLETE' else 'No'
                }
                
                # Extract archive details if available
                if 'archive' in order:
                    archive = order['archive']
                    row['satellite'] = archive.get('constellation', '')
                    row['capture_date'] = archive.get('captureTimestamp', '')
                    row['cloud_cover_percent'] = archive.get('cloudCoveragePercent', '')
                    row['resolution'] = archive.get('resolution', '')
                
                # Extract area if available
                if 'aoi' in order:
                    try:
                        from ..utils.area_calculator import calculate_wkt_area_km2
                        row['area_km2'] = calculate_wkt_area_km2(order['aoi'])
                    except:
                        pass
                
                writer.writerow(row)
        
        logger.info(f"Exported {len(orders)} orders to {output_path}")
        return output_path
    
    def _export_json(self, orders: List[Dict[str, Any]], output_path: str) -> str:
        """Export orders as JSON.
        
        Args:
            orders: Order data
            output_path: Output file path
            
        Returns:
            File path
        """
        # Enhance order data with calculated fields
        enhanced_orders = []
        
        for order in orders:
            enhanced = order.copy()
            
            # Add calculated fields
            enhanced['cost_usd'] = order.get('orderCost', 0) / 100
            enhanced['download_available'] = order.get('status') == 'PROCESSING_COMPLETE'
            
            # Calculate area if possible
            if 'aoi' in order:
                try:
                    from ..utils.area_calculator import calculate_wkt_area_km2
                    enhanced['area_km2'] = calculate_wkt_area_km2(order['aoi'])
                except:
                    enhanced['area_km2'] = None
            
            enhanced_orders.append(enhanced)
        
        # Write JSON
        with open(output_path, 'w') as f:
            json.dump({
                'export_date': datetime.utcnow().isoformat(),
                'total_orders': len(enhanced_orders),
                'total_cost_usd': sum(o['cost_usd'] for o in enhanced_orders),
                'orders': enhanced_orders
            }, f, indent=2)
        
        logger.info(f"Exported {len(orders)} orders to {output_path}")
        return output_path
    
    def _export_html(self, orders: List[Dict[str, Any]], output_path: str) -> str:
        """Export orders as HTML report.
        
        Args:
            orders: Order data
            output_path: Output file path
            
        Returns:
            File path
        """
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>SkyFi Order History</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .summary { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .status-complete { color: green; font-weight: bold; }
        .status-processing { color: orange; }
        .status-failed { color: red; }
    </style>
</head>
<body>
    <h1>SkyFi Order History Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Export Date: {export_date}</p>
        <p>Total Orders: {total_orders}</p>
        <p>Total Cost: ${total_cost:.2f}</p>
        <p>Completed Orders: {completed_orders}</p>
        <p>Processing Orders: {processing_orders}</p>
    </div>
    <h2>Order Details</h2>
    <table>
        <tr>
            <th>Order Code</th>
            <th>Type</th>
            <th>Status</th>
            <th>Cost</th>
            <th>Created</th>
            <th>Location</th>
            <th>Satellite</th>
            <th>Cloud Cover</th>
            <th>Download</th>
        </tr>
        {order_rows}
    </table>
</body>
</html>"""
        
        # Calculate summary stats
        total_cost = sum(order.get('orderCost', 0) / 100 for order in orders)
        completed = len([o for o in orders if o.get('status') == 'PROCESSING_COMPLETE'])
        processing = len([o for o in orders if o.get('status') in ['CREATED', 'PROVIDER_PENDING', 'PROCESSING_PENDING']])
        
        # Generate order rows
        order_rows = []
        for order in orders:
            status = order.get('status', '')
            status_class = ''
            if status == 'PROCESSING_COMPLETE':
                status_class = 'status-complete'
            elif status == 'FAILED':
                status_class = 'status-failed'
            else:
                status_class = 'status-processing'
            
            archive = order.get('archive', {})
            
            row = f"""
        <tr>
            <td>{order.get('orderCode', '')}</td>
            <td>{order.get('orderType', '')}</td>
            <td class="{status_class}">{status}</td>
            <td>${order.get('orderCost', 0) / 100:.2f}</td>
            <td>{order.get('createdAt', '')[:10]}</td>
            <td>{order.get('geocodeLocation', '')}</td>
            <td>{archive.get('constellation', '')}</td>
            <td>{archive.get('cloudCoveragePercent', '')}%</td>
            <td>{'✓' if status == 'PROCESSING_COMPLETE' else '-'}</td>
        </tr>"""
            order_rows.append(row)
        
        # Fill template
        html = html_content.format(
            export_date=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'),
            total_orders=len(orders),
            total_cost=total_cost,
            completed_orders=completed,
            processing_orders=processing,
            order_rows=''.join(order_rows)
        )
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        logger.info(f"Exported {len(orders)} orders to {output_path}")
        return output_path
    
    def _export_markdown(self, orders: List[Dict[str, Any]], output_path: str) -> str:
        """Export orders as Markdown report.
        
        Args:
            orders: Order data
            output_path: Output file path
            
        Returns:
            File path
        """
        with open(output_path, 'w') as f:
            # Header
            f.write("# SkyFi Order History Report\n\n")
            f.write(f"**Export Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")
            
            # Summary
            total_cost = sum(order.get('orderCost', 0) / 100 for order in orders)
            completed = len([o for o in orders if o.get('status') == 'PROCESSING_COMPLETE'])
            
            f.write("## Summary\n\n")
            f.write(f"- **Total Orders:** {len(orders)}\n")
            f.write(f"- **Total Cost:** ${total_cost:.2f}\n")
            f.write(f"- **Completed Orders:** {completed}\n")
            f.write(f"- **Average Cost per Order:** ${total_cost/len(orders):.2f}\n\n")
            
            # Order details
            f.write("## Order Details\n\n")
            f.write("| Order Code | Type | Status | Cost | Created | Location | Satellite | Cloud % |\n")
            f.write("|------------|------|--------|------|---------|----------|-----------|--------|\n")
            
            for order in orders:
                archive = order.get('archive', {})
                f.write(f"| {order.get('orderCode', '')} ")
                f.write(f"| {order.get('orderType', '')} ")
                f.write(f"| {order.get('status', '')} ")
                f.write(f"| ${order.get('orderCost', 0) / 100:.2f} ")
                f.write(f"| {order.get('createdAt', '')[:10]} ")
                f.write(f"| {order.get('geocodeLocation', '')[:20]} ")
                f.write(f"| {archive.get('constellation', '')} ")
                f.write(f"| {archive.get('cloudCoveragePercent', '')} |\n")
            
            # Statistics by satellite
            f.write("\n## Statistics by Satellite\n\n")
            satellite_stats = {}
            for order in orders:
                if 'archive' in order:
                    sat = order['archive'].get('constellation', 'Unknown')
                    if sat not in satellite_stats:
                        satellite_stats[sat] = {'count': 0, 'cost': 0}
                    satellite_stats[sat]['count'] += 1
                    satellite_stats[sat]['cost'] += order.get('orderCost', 0) / 100
            
            for sat, stats in sorted(satellite_stats.items()):
                f.write(f"- **{sat}:** {stats['count']} orders, ${stats['cost']:.2f} total\n")
        
        logger.info(f"Exported {len(orders)} orders to {output_path}")
        return output_path
    
    def generate_summary_report(self, orders: List[Dict[str, Any]]) -> str:
        """Generate a text summary report.
        
        Args:
            orders: Order data
            
        Returns:
            Summary text
        """
        if not orders:
            return "No orders found to summarize."
        
        # Calculate statistics
        total_cost = sum(order.get('orderCost', 0) / 100 for order in orders)
        completed = [o for o in orders if o.get('status') == 'PROCESSING_COMPLETE']
        processing = [o for o in orders if o.get('status') in ['CREATED', 'PROVIDER_PENDING', 'PROCESSING_PENDING']]
        failed = [o for o in orders if o.get('status') == 'FAILED']
        
        # Date range
        dates = [o.get('createdAt', '') for o in orders if o.get('createdAt')]
        if dates:
            earliest = min(dates)[:10]
            latest = max(dates)[:10]
            date_range = f"{earliest} to {latest}"
        else:
            date_range = "N/A"
        
        # Build report
        report = "📊 Order History Summary\n"
        report += "━" * 40 + "\n\n"
        
        report += f"**Date Range:** {date_range}\n"
        report += f"**Total Orders:** {len(orders)}\n"
        report += f"**Total Cost:** ${total_cost:.2f}\n"
        report += f"**Average Cost:** ${total_cost/len(orders):.2f}\n\n"
        
        report += "**Order Status:**\n"
        report += f"  ✅ Completed: {len(completed)}\n"
        report += f"  ⏳ Processing: {len(processing)}\n"
        report += f"  ❌ Failed: {len(failed)}\n\n"
        
        # Cost by status
        if completed:
            completed_cost = sum(o.get('orderCost', 0) / 100 for o in completed)
            report += f"**Completed Orders Cost:** ${completed_cost:.2f}\n"
        
        # Satellite breakdown
        satellite_stats = {}
        for order in orders:
            if 'archive' in order:
                sat = order['archive'].get('constellation', 'Unknown')
                if sat not in satellite_stats:
                    satellite_stats[sat] = 0
                satellite_stats[sat] += 1
        
        if satellite_stats:
            report += "\n**Orders by Satellite:**\n"
            for sat, count in sorted(satellite_stats.items(), key=lambda x: x[1], reverse=True):
                report += f"  • {sat}: {count} orders\n"
        
        return report