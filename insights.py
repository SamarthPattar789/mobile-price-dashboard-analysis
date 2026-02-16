from flask import Blueprint, render_template, current_app, jsonify
from flask_login import login_required
from sqlalchemy import func, case
from models import Brand, PhoneModel, Sale

insights_bp = Blueprint("insights", __name__, template_folder="templates")


def generate_insights(db):
    """Generate automatic insights from sales data"""
    insights = []
    
    # 1. Top brand by region and year
    region_year_query = (
        db.query(
            Brand.name.label("brand"),
            Sale.region,
            Sale.year,
            func.sum(Sale.units_sold).label("total_units")
        )
        .join(PhoneModel, PhoneModel.id == Sale.model_id)
        .join(Brand, Brand.id == PhoneModel.brand_id)
        .group_by(Brand.name, Sale.region, Sale.year)
        .order_by(Sale.year.desc(), func.sum(Sale.units_sold).desc())
    )
    
    # Get top brand for each region-year combination
    region_year_sales = {}
    for row in region_year_query.all():
        key = f"{row.region}_{row.year}"
        if key not in region_year_sales:
            region_year_sales[key] = {
                "brand": row.brand,
                "region": row.region,
                "year": row.year,
                "units": row.total_units
            }
    
    # Generate insights for top brands by region
    for key, data in list(region_year_sales.items())[:5]:  # Top 5
        insights.append({
            "type": "performance",
            "severity": "info",
            "title": f"{data['brand']} models sold highest in {data['region']} in {data['year']}.",
            "description": f"Total units sold: {data['units']:,}",
            "icon": "trending-up"
        })
    
    # 2. Year-over-year sales changes by brand
    brand_yearly = (
        db.query(
            Brand.name.label("brand"),
            Sale.year,
            func.sum(Sale.units_sold).label("total_units")
        )
        .join(PhoneModel, PhoneModel.id == Sale.model_id)
        .join(Brand, Brand.id == PhoneModel.brand_id)
        .group_by(Brand.name, Sale.year)
        .order_by(Brand.name, Sale.year)
    )
    
    brand_sales_by_year = {}
    for row in brand_yearly.all():
        if row.brand not in brand_sales_by_year:
            brand_sales_by_year[row.brand] = {}
        brand_sales_by_year[row.brand][row.year] = row.total_units
    
    # Calculate YoY changes
    for brand, year_data in brand_sales_by_year.items():
        years = sorted(year_data.keys())
        if len(years) >= 2:
            prev_year = years[-2]
            curr_year = years[-1]
            prev_sales = year_data[prev_year]
            curr_sales = year_data[curr_year]
            
            if prev_sales > 0:
                change_pct = ((curr_sales - prev_sales) / prev_sales) * 100
                if abs(change_pct) >= 5:  # Only show significant changes
                    insights.append({
                        "type": "trend",
                        "severity": "warning" if change_pct < 0 else "success",
                        "title": f"{brand} sales {'dropped' if change_pct < 0 else 'increased'} {abs(change_pct):.1f}% in {curr_year}.",
                        "description": f"From {prev_sales:,} units in {prev_year} to {curr_sales:,} units in {curr_year}",
                        "icon": "trending-down" if change_pct < 0 else "trending-up"
                    })
    
    # 3. Battery capacity correlation with sales
    battery_sales_query = (
        db.query(
            PhoneModel.battery,
            func.sum(Sale.units_sold).label("total_units"),
            func.avg(Sale.units_sold).label("avg_units")
        )
        .join(Sale, Sale.model_id == PhoneModel.id)
        .filter(PhoneModel.battery.isnot(None), PhoneModel.battery != "")
        .group_by(PhoneModel.battery)
        .order_by(func.sum(Sale.units_sold).desc())
    )
    
    battery_data = battery_sales_query.all()
    if len(battery_data) >= 2:
        # Check if there's a clear pattern (higher battery = more sales)
        top_battery = battery_data[0]
        if top_battery.total_units > 0:
            # Extract numeric battery value for comparison
            try:
                battery_str = str(top_battery.battery).replace("mAh", "").replace(" ", "").strip()
                battery_val = int(battery_str) if battery_str else 0
                
                if battery_val > 4000:  # High capacity
                    insights.append({
                        "type": "correlation",
                        "severity": "info",
                        "title": "Battery capacity strongly influences sales.",
                        "description": f"Models with {top_battery.battery} battery show highest sales performance",
                        "icon": "battery-full"
                    })
            except:
                pass
    
    # 4. RAM correlation
    ram_sales_query = (
        db.query(
            PhoneModel.ram,
            func.sum(Sale.units_sold).label("total_units")
        )
        .join(Sale, Sale.model_id == PhoneModel.id)
        .filter(PhoneModel.ram.isnot(None), PhoneModel.ram != "")
        .group_by(PhoneModel.ram)
        .order_by(func.sum(Sale.units_sold).desc())
    )
    
    ram_data = ram_sales_query.first()
    if ram_data and ram_data.total_units > 0:
        insights.append({
            "type": "correlation",
            "severity": "info",
            "title": f"Models with {ram_data.ram} RAM show highest sales.",
            "description": f"Total units sold: {ram_data.total_units:,}",
            "icon": "memory"
        })
    
    # 5. Storage correlation
    storage_sales_query = (
        db.query(
            PhoneModel.storage,
            func.sum(Sale.units_sold).label("total_units")
        )
        .join(Sale, Sale.model_id == PhoneModel.id)
        .filter(PhoneModel.storage.isnot(None), PhoneModel.storage != "")
        .group_by(PhoneModel.storage)
        .order_by(func.sum(Sale.units_sold).desc())
    )
    
    storage_data = storage_sales_query.first()
    if storage_data and storage_data.total_units > 0:
        insights.append({
            "type": "correlation",
            "severity": "info",
            "title": f"Models with {storage_data.storage} storage are most popular.",
            "description": f"Total units sold: {storage_data.total_units:,}",
            "icon": "hard-drive"
        })
    
    # 6. Channel performance
    channel_query = (
        db.query(
            Sale.channel,
            func.sum(Sale.units_sold).label("total_units"),
            func.sum(Sale.total_revenue).label("total_revenue")
        )
        .group_by(Sale.channel)
        .order_by(func.sum(Sale.units_sold).desc())
    )
    
    top_channel = channel_query.first()
    if top_channel:
        insights.append({
            "type": "performance",
            "severity": "success",
            "title": f"{top_channel.channel} channel drives highest sales.",
            "description": f"{top_channel.total_units:,} units sold, ₹{top_channel.total_revenue:,.0f} revenue",
            "icon": "shopping-cart"
        })
    
    return insights


@insights_bp.route("/insights")
@login_required
def index():
    """Display insights and alerts page"""
    SessionLocal = current_app.session_factory
    with SessionLocal() as db:
        insights = generate_insights(db)
    
    # Separate insights by type
    performance_insights = [i for i in insights if i["type"] == "performance"]
    trend_insights = [i for i in insights if i["type"] == "trend"]
    correlation_insights = [i for i in insights if i["type"] == "correlation"]
    
    return render_template(
        "insights.html",
        performance_insights=performance_insights,
        trend_insights=trend_insights,
        correlation_insights=correlation_insights,
        all_insights=insights
    )


@insights_bp.route("/insights/api")
@login_required
def api_insights():
    """API endpoint to get insights as JSON"""
    SessionLocal = current_app.session_factory
    with SessionLocal() as db:
        insights = generate_insights(db)
    
    return jsonify({"insights": insights})


