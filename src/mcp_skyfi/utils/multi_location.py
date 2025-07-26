"""Multi-location search support for searching multiple areas at once."""
import asyncio
import logging
from typing import List, Dict, Any, Tuple, Optional
from shapely import wkt
from shapely.geometry import Point, Polygon, MultiPolygon

logger = logging.getLogger(__name__)


def create_locations_from_points(
    points: List[Tuple[float, float]],
    buffer_km: float = 5.0
) -> List[str]:
    """Create search areas from a list of points.
    
    Args:
        points: List of (longitude, latitude) tuples
        buffer_km: Buffer radius in kilometers
        
    Returns:
        List of WKT polygons
    """
    locations = []
    
    # Convert km to degrees (approximate)
    buffer_degrees = buffer_km / 111.0  # 1 degree ≈ 111 km
    
    for lon, lat in points:
        # Create a circular buffer around the point
        point = Point(lon, lat)
        circle = point.buffer(buffer_degrees)
        
        # Convert to WKT
        locations.append(circle.wkt)
    
    return locations


def create_grid_search(
    center_lon: float,
    center_lat: float,
    grid_size: int = 3,
    cell_size_km: float = 10.0
) -> List[str]:
    """Create a grid of search areas.
    
    Args:
        center_lon: Center longitude
        center_lat: Center latitude
        grid_size: Grid dimension (e.g., 3 for 3x3)
        cell_size_km: Size of each grid cell in km
        
    Returns:
        List of WKT polygons for grid cells
    """
    locations = []
    
    # Convert km to degrees
    cell_size_deg = cell_size_km / 111.0
    
    # Calculate grid offsets
    half_grid = grid_size // 2
    
    for row in range(-half_grid, half_grid + 1):
        for col in range(-half_grid, half_grid + 1):
            # Calculate cell bounds
            min_lon = center_lon + (col * cell_size_deg) - (cell_size_deg / 2)
            max_lon = center_lon + (col * cell_size_deg) + (cell_size_deg / 2)
            min_lat = center_lat + (row * cell_size_deg) - (cell_size_deg / 2)
            max_lat = center_lat + (row * cell_size_deg) + (cell_size_deg / 2)
            
            # Create polygon
            polygon = Polygon([
                (min_lon, min_lat),
                (max_lon, min_lat),
                (max_lon, max_lat),
                (min_lon, max_lat),
                (min_lon, min_lat)
            ])
            
            locations.append(polygon.wkt)
    
    return locations


def split_large_area(
    wkt_polygon: str,
    max_area_km2: float = 100.0
) -> List[str]:
    """Split a large area into smaller chunks.
    
    Args:
        wkt_polygon: Large area as WKT
        max_area_km2: Maximum area per chunk
        
    Returns:
        List of smaller WKT polygons
    """
    try:
        from ..utils.area_calculator import calculate_wkt_area_km2
        
        # Parse the polygon
        poly = wkt.loads(wkt_polygon)
        
        # Calculate current area
        current_area = calculate_wkt_area_km2(wkt_polygon)
        
        if current_area <= max_area_km2:
            return [wkt_polygon]
        
        # Calculate how many splits needed
        num_splits = int(current_area / max_area_km2) + 1
        grid_size = int(num_splits ** 0.5) + 1
        
        # Get bounds
        bounds = poly.bounds  # (minx, miny, maxx, maxy)
        
        # Create grid
        locations = []
        x_step = (bounds[2] - bounds[0]) / grid_size
        y_step = (bounds[3] - bounds[1]) / grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                # Create cell
                min_x = bounds[0] + (i * x_step)
                max_x = bounds[0] + ((i + 1) * x_step)
                min_y = bounds[1] + (j * y_step)
                max_y = bounds[1] + ((j + 1) * y_step)
                
                cell = Polygon([
                    (min_x, min_y),
                    (max_x, min_y),
                    (max_x, max_y),
                    (min_x, max_y),
                    (min_x, min_y)
                ])
                
                # Only include if it intersects with original
                if cell.intersects(poly):
                    intersection = cell.intersection(poly)
                    if not intersection.is_empty:
                        locations.append(intersection.wkt)
        
        return locations
        
    except Exception as e:
        logger.error(f"Failed to split area: {e}")
        return [wkt_polygon]


class MultiLocationSearcher:
    """Handle searches across multiple locations."""
    
    def __init__(self, client):
        """Initialize with SkyFi client.
        
        Args:
            client: SkyFiClient instance
        """
        self.client = client
    
    async def search_multiple_locations(
        self,
        locations: List[str],
        from_date: str,
        to_date: str,
        **search_params
    ) -> Dict[str, Any]:
        """Search multiple locations concurrently.
        
        Args:
            locations: List of WKT polygons
            from_date: Start date
            to_date: End date
            **search_params: Additional search parameters
            
        Returns:
            Combined results with location info
        """
        # Create search tasks
        tasks = []
        for idx, location in enumerate(locations):
            task = self._search_location(
                location_id=f"loc_{idx+1}",
                aoi=location,
                from_date=from_date,
                to_date=to_date,
                **search_params
            )
            tasks.append(task)
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        combined = {
            "total_results": 0,
            "locations": [],
            "all_results": [],
            "summary": {}
        }
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Location {idx+1} failed: {result}")
                combined["locations"].append({
                    "id": f"loc_{idx+1}",
                    "status": "failed",
                    "error": str(result)
                })
            else:
                combined["locations"].append(result["location_info"])
                combined["all_results"].extend(result["results"])
                combined["total_results"] += result["count"]
        
        # Generate summary
        combined["summary"] = self._generate_summary(combined)
        
        return combined
    
    async def _search_location(
        self,
        location_id: str,
        aoi: str,
        from_date: str,
        to_date: str,
        **search_params
    ) -> Dict[str, Any]:
        """Search a single location.
        
        Args:
            location_id: Identifier for this location
            aoi: WKT polygon
            from_date: Start date
            to_date: End date
            **search_params: Additional parameters
            
        Returns:
            Search results with location metadata
        """
        try:
            # Calculate area
            from ..utils.area_calculator import calculate_wkt_area_km2
            area_km2 = calculate_wkt_area_km2(aoi)
            
            # Perform search
            results = await self.client.search_archives(
                aoi=aoi,
                from_date=from_date,
                to_date=to_date,
                **search_params
            )
            
            # Add location info to each result
            for result in results.get("results", []):
                result["location_id"] = location_id
                result["location_area_km2"] = area_km2
            
            return {
                "location_info": {
                    "id": location_id,
                    "status": "success",
                    "area_km2": area_km2,
                    "result_count": len(results.get("results", []))
                },
                "results": results.get("results", []),
                "count": len(results.get("results", []))
            }
            
        except Exception as e:
            logger.error(f"Search failed for {location_id}: {e}")
            raise
    
    def _generate_summary(self, combined_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics.
        
        Args:
            combined_results: Combined search results
            
        Returns:
            Summary statistics
        """
        all_results = combined_results["all_results"]
        
        if not all_results:
            return {
                "avg_cloud_cover": 0,
                "price_range": {"min": 0, "max": 0},
                "satellites": [],
                "date_range": {"earliest": None, "latest": None}
            }
        
        # Calculate statistics
        cloud_covers = [r.get("cloudCover", 0) for r in all_results]
        prices = [r.get("price", 0) for r in all_results]
        satellites = list(set(r.get("satellite", "") for r in all_results))
        dates = [r.get("captureDate", "") for r in all_results if r.get("captureDate")]
        
        return {
            "avg_cloud_cover": sum(cloud_covers) / len(cloud_covers) if cloud_covers else 0,
            "price_range": {
                "min": min(prices) if prices else 0,
                "max": max(prices) if prices else 0
            },
            "satellites": sorted(satellites),
            "date_range": {
                "earliest": min(dates) if dates else None,
                "latest": max(dates) if dates else None
            },
            "successful_locations": len([l for l in combined_results["locations"] if l["status"] == "success"]),
            "failed_locations": len([l for l in combined_results["locations"] if l["status"] == "failed"])
        }
    
    def format_multi_location_results(
        self,
        results: Dict[str, Any],
        max_per_location: int = 3
    ) -> str:
        """Format multi-location results for display.
        
        Args:
            results: Combined results from search
            max_per_location: Max results to show per location
            
        Returns:
            Formatted text
        """
        text = f"🌍 Multi-Location Search Results\n"
        text += "━" * 50 + "\n\n"
        
        # Summary
        summary = results["summary"]
        text += f"📊 Summary:\n"
        text += f"  • Total Results: {results['total_results']}\n"
        text += f"  • Locations: {summary['successful_locations']} successful"
        if summary['failed_locations'] > 0:
            text += f", {summary['failed_locations']} failed"
        text += "\n"
        text += f"  • Avg Cloud Cover: {summary['avg_cloud_cover']:.1f}%\n"
        text += f"  • Price Range: ${summary['price_range']['min']:.2f} - ${summary['price_range']['max']:.2f}/km²\n"
        text += f"  • Satellites: {', '.join(summary['satellites'])}\n\n"
        
        # Results by location
        for location in results["locations"]:
            if location["status"] == "failed":
                text += f"❌ Location {location['id']}: Failed - {location.get('error', 'Unknown error')}\n\n"
                continue
            
            text += f"📍 Location {location['id']} ({location['area_km2']:.1f} km²):\n"
            text += f"   Found {location['result_count']} images\n"
            
            # Show top results for this location
            location_results = [
                r for r in results["all_results"]
                if r.get("location_id") == location["id"]
            ][:max_per_location]
            
            for r in location_results:
                satellite = r.get("satellite", "Unknown")
                date = r.get("captureDate", "N/A")[:10]
                cloud = r.get("cloudCover", 0)
                price = r.get("price", 0)
                
                text += f"   • {satellite} - {date} - {cloud}% clouds - ${price:.2f}/km²\n"
            
            if location["result_count"] > max_per_location:
                text += f"   ... and {location['result_count'] - max_per_location} more\n"
            
            text += "\n"
        
        return text