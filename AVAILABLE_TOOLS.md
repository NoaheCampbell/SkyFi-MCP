# SkyFi MCP Server - Available Tools

Total Tools: **29**

## SkyFi Core Tools (13)

1. **skyfi_search_archives** - Search for satellite imagery with natural language dates
2. **skyfi_prepare_order** - Prepare a satellite image order (step 1 of ordering)
3. **skyfi_confirm_order** - Confirm and place the order (step 2 of ordering)
4. **skyfi_get_user** - Get current user information and account details
5. **skyfi_spending_report** - Get spending report and budget status
6. **skyfi_list_orders** - List recent satellite image orders
7. **skyfi_download_order** - Download a completed order
8. **skyfi_multi_location_search** - Search multiple areas simultaneously
9. **skyfi_export_order_history** - Export order history to various formats
10. **skyfi_estimate_cost** - Quick cost estimation for an area
11. **skyfi_compare_costs** - Compare costs across different scenarios
12. **skyfi_search_exact** - Search with exact polygon (no auto-simplification)
13. **skyfi_search_bbox** - Search with simple bounding box (most reliable)

## Satellite Tasking Tools (5)

14. **skyfi_get_tasking_quote** - Get a detailed quote for satellite tasking
15. **skyfi_create_tasking_order** - Create a tasking order from a quote
16. **skyfi_get_order_status** - Check the status of a tasking order
17. **skyfi_analyze_capture_feasibility** - Analyze feasibility of capturing imagery
18. **skyfi_predict_satellite_passes** - Predict satellite passes over an area

## Monitoring Tools (3)

19. **skyfi_create_webhook_subscription** - Set up webhooks for new imagery alerts
20. **skyfi_setup_area_monitoring** - Monitor specific areas for new captures
21. **skyfi_get_notification_status** - Check monitoring subscription status

## Weather Tools (2)

22. **weather_current** - Get current weather conditions
23. **weather_forecast** - Get weather forecast for planning

## OpenStreetMap Tools (5)

24. **osm_geocode** - Convert addresses to coordinates
25. **osm_reverse_geocode** - Convert coordinates to addresses
26. **osm_polygon_to_wkt** - Convert place names to WKT polygons
27. **osm_generate_aoi** - Generate area of interest polygons
28. **osm_calculate_distance** - Calculate distances between points

## Removed Tools (23)

The following tools were removed to streamline the interface:

### Authentication & Budget Management
- skyfi_authenticate
- skyfi_check_auth
- update_account_budget
- request_budget_change
- confirm_budget_change
- view_current_budget

### Redundant Tools
- skyfi_get_download_url (functionality in download_order)
- skyfi_get_pricing (replaced by estimate_cost)
- calculate_archive_pricing
- estimate_tasking_pricing

### Saved Searches
- skyfi_save_search
- skyfi_list_saved_searches
- skyfi_run_saved_search

### OSM Advanced Tools
- osm_batch_geocode
- osm_search_nearby_pois
- osm_search_businesses
- osm_create_bounding_box

## Tool Categories by Purpose

### Search & Discovery
- skyfi_search_archives
- skyfi_multi_location_search
- osm_geocode
- osm_polygon_to_wkt

### Ordering & Downloads
- skyfi_prepare_order
- skyfi_confirm_order
- skyfi_list_orders
- skyfi_download_order
- skyfi_export_order_history

### Cost Management
- skyfi_spending_report
- skyfi_estimate_cost
- skyfi_compare_costs

### Satellite Tasking
- skyfi_get_tasking_quote
- skyfi_create_tasking_order
- skyfi_get_order_status
- skyfi_analyze_capture_feasibility
- skyfi_predict_satellite_passes

### Monitoring & Alerts
- skyfi_create_webhook_subscription
- skyfi_setup_area_monitoring
- skyfi_get_notification_status

### Geographic Tools
- osm_geocode
- osm_reverse_geocode
- osm_polygon_to_wkt
- osm_generate_aoi
- osm_calculate_distance

### Weather Planning
- weather_current
- weather_forecast

### Account Management
- skyfi_get_user
- skyfi_spending_report