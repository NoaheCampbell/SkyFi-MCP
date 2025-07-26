"""Manage saved searches for quick re-use."""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SavedSearchManager:
    """Manage saved searches with persistence."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the saved search manager.
        
        Args:
            storage_path: Path to store saved searches (defaults to ~/.skyfi/saved_searches.json)
        """
        if storage_path is None:
            home_dir = os.path.expanduser("~")
            skyfi_dir = os.path.join(home_dir, ".skyfi")
            os.makedirs(skyfi_dir, exist_ok=True)
            storage_path = os.path.join(skyfi_dir, "saved_searches.json")
        
        self.storage_path = storage_path
        self._load_searches()
    
    def _load_searches(self) -> None:
        """Load saved searches from disk."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    self.searches = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load saved searches: {e}")
                self.searches = {}
        else:
            self.searches = {}
    
    def _save_searches(self) -> None:
        """Save searches to disk."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.searches, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save searches: {e}")
    
    def save_search(
        self,
        name: str,
        aoi: str,
        from_date: str,
        to_date: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        resolution: Optional[str] = None,
        product_types: Optional[List[str]] = None,
        max_cloud_cover: Optional[float] = None
    ) -> str:
        """Save a search configuration.
        
        Args:
            name: Unique name for the search
            aoi: Area of interest (WKT)
            from_date: Start date (can be natural language)
            to_date: End date (can be natural language)
            description: Optional description
            tags: Optional tags for categorization
            resolution: Preferred resolution
            product_types: Preferred product types
            max_cloud_cover: Maximum acceptable cloud cover
            
        Returns:
            Search ID
        """
        search_id = name.lower().replace(" ", "_")
        
        # Calculate area for reference
        try:
            from ..utils.area_calculator import calculate_wkt_area_km2
            area_km2 = calculate_wkt_area_km2(aoi)
        except:
            area_km2 = None
        
        self.searches[search_id] = {
            "id": search_id,
            "name": name,
            "aoi": aoi,
            "area_km2": area_km2,
            "from_date": from_date,
            "to_date": to_date,
            "description": description or "",
            "tags": tags or [],
            "resolution": resolution,
            "product_types": product_types,
            "max_cloud_cover": max_cloud_cover,
            "created_at": datetime.utcnow().isoformat(),
            "last_used": None,
            "use_count": 0
        }
        
        self._save_searches()
        return search_id
    
    def get_search(self, search_id: str) -> Optional[Dict[str, Any]]:
        """Get a saved search by ID.
        
        Args:
            search_id: Search ID or name
            
        Returns:
            Search configuration or None
        """
        # Try exact match first
        if search_id in self.searches:
            search = self.searches[search_id].copy()
            # Update usage stats
            self.searches[search_id]["last_used"] = datetime.utcnow().isoformat()
            self.searches[search_id]["use_count"] += 1
            self._save_searches()
            return search
        
        # Try case-insensitive match
        search_id_lower = search_id.lower().replace(" ", "_")
        if search_id_lower in self.searches:
            search = self.searches[search_id_lower].copy()
            # Update usage stats
            self.searches[search_id_lower]["last_used"] = datetime.utcnow().isoformat()
            self.searches[search_id_lower]["use_count"] += 1
            self._save_searches()
            return search
        
        return None
    
    def list_searches(
        self,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at"
    ) -> List[Dict[str, Any]]:
        """List all saved searches.
        
        Args:
            tags: Filter by tags (if provided)
            sort_by: Sort by field (created_at, last_used, use_count, name)
            
        Returns:
            List of saved searches
        """
        searches = list(self.searches.values())
        
        # Filter by tags if provided
        if tags:
            searches = [
                s for s in searches
                if any(tag in s.get("tags", []) for tag in tags)
            ]
        
        # Sort
        if sort_by == "last_used":
            searches.sort(key=lambda s: s.get("last_used") or "", reverse=True)
        elif sort_by == "use_count":
            searches.sort(key=lambda s: s.get("use_count", 0), reverse=True)
        elif sort_by == "name":
            searches.sort(key=lambda s: s.get("name", ""))
        else:  # created_at
            searches.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        
        return searches
    
    def delete_search(self, search_id: str) -> bool:
        """Delete a saved search.
        
        Args:
            search_id: Search ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if search_id in self.searches:
            del self.searches[search_id]
            self._save_searches()
            return True
        
        # Try case-insensitive
        search_id_lower = search_id.lower().replace(" ", "_")
        if search_id_lower in self.searches:
            del self.searches[search_id_lower]
            self._save_searches()
            return True
        
        return False
    
    def update_search(
        self,
        search_id: str,
        **kwargs
    ) -> bool:
        """Update a saved search.
        
        Args:
            search_id: Search ID to update
            **kwargs: Fields to update
            
        Returns:
            True if updated, False if not found
        """
        if search_id in self.searches:
            for key, value in kwargs.items():
                if key in self.searches[search_id]:
                    self.searches[search_id][key] = value
            self.searches[search_id]["updated_at"] = datetime.utcnow().isoformat()
            self._save_searches()
            return True
        
        return False
    
    def format_search_list(self, searches: List[Dict[str, Any]]) -> str:
        """Format searches for display.
        
        Args:
            searches: List of searches to format
            
        Returns:
            Formatted text
        """
        if not searches:
            return "No saved searches found."
        
        text = "📑 Saved Searches\n"
        text += "━" * 50 + "\n\n"
        
        for idx, search in enumerate(searches, 1):
            name = search.get("name", "Unnamed")
            description = search.get("description", "")
            area = search.get("area_km2")
            tags = search.get("tags", [])
            use_count = search.get("use_count", 0)
            last_used = search.get("last_used")
            
            text += f"{idx}. {name}\n"
            if description:
                text += f"   📝 {description}\n"
            if area:
                text += f"   📏 Area: {area:.1f} km²\n"
            if tags:
                text += f"   🏷️  Tags: {', '.join(tags)}\n"
            text += f"   📊 Used: {use_count} times"
            if last_used:
                text += f" (last: {last_used[:10]})"
            text += "\n\n"
        
        return text