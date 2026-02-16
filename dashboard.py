from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required
from models import Brand, PhoneModel, Sale

dashboard_bp = Blueprint("dashboard", __name__, template_folder="templates")


@dashboard_bp.route("/")
@login_required
def index():
    # Get Power BI URL from Flask config (loaded from .env or environment)
    # Only use it if it's a valid URL (not placeholder)
    pbi_url = current_app.config.get("PBI_REPORT_URL", "").strip()
    if pbi_url and ("YOUR_REPORT_ID" in pbi_url or len(pbi_url) < 20):
        pbi_url = ""  # Ignore placeholder/invalid URLs
    return render_template("dashboard.html", pbi_url=pbi_url)


@dashboard_bp.route("/api/data")
@login_required
def api_data():
    """API endpoint to get dashboard data"""
    SessionLocal = current_app.session_factory
    with SessionLocal() as db:
        # Get filter parameters
        brand_filter = request.args.get("brand", "")
        model_filter = request.args.get("model", "")
        channel_filter = request.args.get("channel", "")
        region_filter = request.args.get("region", "")
        year_filter = request.args.get("year", "")
        price_filter = request.args.get("price", "")  # Format: "min-max"

        # Base query
        query = (
            db.query(
                Brand.name.label("brand"),
                PhoneModel.model_name.label("model"),
                PhoneModel.ram.label("ram"),
                PhoneModel.storage.label("storage"),
                Sale.units_sold,
                Sale.total_revenue,
                Sale.average_price,
                Sale.region,
                Sale.channel,
                Sale.year,
            )
            .join(PhoneModel, PhoneModel.id == Sale.model_id)
            .join(Brand, Brand.id == PhoneModel.brand_id)
        )

        # Apply filters
        if brand_filter:
            query = query.filter(Brand.name == brand_filter)
        if model_filter:
            query = query.filter(PhoneModel.model_name == model_filter)
        if channel_filter:
            query = query.filter(Sale.channel == channel_filter)
        if region_filter:
            query = query.filter(Sale.region == region_filter)
        if year_filter:
            try:
                query = query.filter(Sale.year == int(year_filter))
            except ValueError:
                pass  # Invalid year filter, ignore it

        # Apply price range filter
        if price_filter:
            try:
                if "-" in price_filter:
                    min_price, max_price = price_filter.split("-")
                    min_price = float(min_price)
                    max_price = float(max_price)
                    query = query.filter(Sale.average_price >= min_price, Sale.average_price <= max_price)
            except (ValueError, AttributeError):
                pass  # Invalid price filter, ignore it

        results = query.all()

        # Calculate KPIs
        total_units = sum(r.units_sold for r in results)
        total_revenue = sum(r.total_revenue for r in results)
        unique_models = len(set((r.brand, r.model) for r in results))
        unique_customers = len(set(r.region for r in results))  # Approximate

        # Brand-wise sales
        brand_sales = {}
        brand_revenue = {}
        for r in results:
            brand_sales[r.brand] = brand_sales.get(r.brand, 0) + r.units_sold
            brand_revenue[r.brand] = brand_revenue.get(r.brand, 0) + r.total_revenue

        # Channel distribution
        channel_sales = {}
        for r in results:
            channel_sales[r.channel] = channel_sales.get(r.channel, 0) + r.units_sold

        # Regional sales
        region_sales = {}
        for r in results:
            region_sales[r.region] = region_sales.get(r.region, 0) + r.units_sold

        # Yearly trends
        yearly_data = {}
        for r in results:
            if r.year not in yearly_data:
                yearly_data[r.year] = {"units": 0, "revenue": 0}
            yearly_data[r.year]["units"] += r.units_sold
            yearly_data[r.year]["revenue"] += r.total_revenue

        # Heatmap data: Sales by region and year
        heatmap_data = {}
        for r in results:
            key = f"{r.region}_{r.year}"
            if key not in heatmap_data:
                heatmap_data[key] = {"region": r.region, "year": r.year, "sales": 0}
            heatmap_data[key]["sales"] += r.units_sold

        # Treemap data: Brand/Model hierarchy
        treemap_data = {}
        for r in results:
            if r.brand not in treemap_data:
                treemap_data[r.brand] = {"name": r.brand, "value": 0, "children": {}}
            if r.model not in treemap_data[r.brand]["children"]:
                treemap_data[r.brand]["children"][r.model] = {"name": r.model, "value": 0}
            treemap_data[r.brand]["value"] += r.units_sold
            treemap_data[r.brand]["children"][r.model]["value"] += r.units_sold

        # Top performing models data
        model_performance = {}
        for r in results:
            key = f"{r.brand} - {r.model}"
            if key not in model_performance:
                model_performance[key] = {
                    "brand": r.brand,
                    "model": r.model,
                    "units_sold": 0,
                    "total_revenue": 0,
                    "avg_price": 0,
                    "regions": set(),
                    "channels": set()
                }
            model_performance[key]["units_sold"] += r.units_sold
            model_performance[key]["total_revenue"] += r.total_revenue
            model_performance[key]["regions"].add(r.region)
            model_performance[key]["channels"].add(r.channel)
        
        # Calculate average price and convert sets to counts
        for key, data in model_performance.items():
            # Calculate weighted average price
            if data["units_sold"] > 0:
                data["avg_price"] = data["total_revenue"] / data["units_sold"]
            data["region_count"] = len(data["regions"])
            data["channel_count"] = len(data["channels"])
            del data["regions"]
            del data["channels"]
        
        top_models_data = list(model_performance.values())

        # Scatter plot data: Price vs Units Sold
        scatter_data = []
        for r in results:
            scatter_data.append({
                "x": r.average_price,
                "y": r.units_sold,
                "brand": r.brand,
                "model": r.model
            })

        # Correlation data: Specs vs Sales
        correlation_data = []
        for r in results:
            ram_val = 0
            storage_val = 0
            if r.ram:
                try:
                    ram_str = str(r.ram).replace("GB", "").replace(" ", "").strip()
                    ram_val = int(ram_str) if ram_str else 0
                except:
                    ram_val = 0
            if r.storage:
                try:
                    storage_str = str(r.storage).replace("GB", "").replace(" ", "").strip()
                    storage_val = int(storage_str) if storage_str else 0
                except:
                    storage_val = 0
            correlation_data.append({
                "ram": ram_val,
                "storage": storage_val,
                "units_sold": r.units_sold,
                "price": r.average_price,
                "revenue": r.total_revenue
            })

        # Get unique filter options
        brands = sorted([b.name for b in db.query(Brand).distinct().all()])
        models = sorted(
            [m.model_name for m in db.query(PhoneModel).distinct().all()]
        )[:100]  # Limit to 100 for dropdown
        channels = sorted(list(set(r.channel for r in results if r.channel)))
        regions = sorted(list(set(r.region for r in results if r.region)))
        years = sorted(list(set(r.year for r in results if r.year)))

        return jsonify(
            {
                "kpis": {
                    "total_units": total_units,
                    "total_revenue": total_revenue,
                    "total_models": unique_models,
                    "total_customers": unique_customers,
                },
                "brand_sales": brand_sales,
                "brand_revenue": brand_revenue,
                "channel_sales": channel_sales,
                "region_sales": region_sales,
                "yearly_trends": yearly_data,
                "heatmap_data": heatmap_data,
                "treemap_data": treemap_data,
                "top_models_data": top_models_data,
                "scatter_data": scatter_data,
                "correlation_data": correlation_data,
                "filters": {
                    "brands": brands,
                    "models": models,
                    "channels": channels,
                    "regions": regions,
                    "years": years,
                },
            }
        )


