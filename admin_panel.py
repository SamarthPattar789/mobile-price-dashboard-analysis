from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
import io
import pandas as pd

from models import Brand, PhoneModel, Sale

admin_bp = Blueprint("admin", __name__, url_prefix="/admin", template_folder="templates")


def require_admin() -> bool:
    return bool(current_user.is_authenticated and getattr(current_user, "role", "user") == "admin")


@admin_bp.before_request
def guard_admin():
    # Allow non-admins to hit nothing under /admin
    if request.endpoint and request.endpoint.startswith("admin."):
        if not require_admin():
            return redirect(url_for("dashboard.index"))


@admin_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("Please choose a CSV file", "warning")
            return redirect(request.url)

        df = pd.read_csv(file)
        required_cols = {
            "Brand",
            "Model",
            "RAM",
            "Storage",
            "Camera",
            "Battery",
            "Processor",
            "Price",
            "Units Sold",
            "Region",
            "Channel",
            "Year",
        }
        if not required_cols.issubset(set(df.columns)):
            flash("CSV missing required columns", "danger")
            return redirect(request.url)

        SessionLocal = current_app.session_factory
        with SessionLocal() as db:
            brand_cache = {b.name: b for b in db.query(Brand).all()}
            for _, row in df.iterrows():
                brand = brand_cache.get(row["Brand"]) or Brand(name=row["Brand"])
                if brand.id is None:
                    db.add(brand)
                    db.flush()
                    brand_cache[brand.name] = brand

                model = (
                    db.query(PhoneModel)
                    .filter(PhoneModel.brand_id == brand.id, PhoneModel.model_name == row["Model"]).first()
                )
                if not model:
                    model = PhoneModel(
                        brand_id=brand.id,
                        model_name=row["Model"],
                        ram=row.get("RAM", ""),
                        storage=row.get("Storage", ""),
                        camera=row.get("Camera", ""),
                        battery=row.get("Battery", ""),
                        processor=row.get("Processor", ""),
                        os=str(row.get("OS", "")),
                        display_size=str(row.get("Display Size", "")),
                        launch_year=int(row.get("Year", 0) or 0),
                    )
                    db.add(model)
                    db.flush()

                sale = Sale(
                    model_id=model.id,
                    units_sold=int(row.get("Units Sold", 0) or 0),
                    total_revenue=float(row.get("Price", 0) or 0) * int(row.get("Units Sold", 0) or 0),
                    average_price=float(str(row.get("Price", 0)).replace(",", "").replace("₹", "") or 0),
                    region=row.get("Region", ""),
                    channel=row.get("Channel", ""),
                    year=int(row.get("Year", 0) or 0),
                )
                db.add(sale)

            db.commit()
        flash("Data uploaded successfully", "success")
        return redirect(url_for("dashboard.index"))
    return render_template("admin_upload.html")


@admin_bp.route("/export/<string:format>", methods=["GET"])
@login_required
def export(format: str):
    if not require_admin():
        return redirect(url_for("dashboard.index"))
    SessionLocal = current_app.session_factory
    with SessionLocal() as db:
        query = (
            db.query(
                Brand.name.label("Brand"),
                PhoneModel.model_name.label("Model"),
                PhoneModel.ram.label("RAM"),
                PhoneModel.storage.label("Storage"),
                PhoneModel.camera.label("Camera"),
                PhoneModel.battery.label("Battery"),
                PhoneModel.processor.label("Processor"),
                Sale.average_price.label("Price"),
                Sale.units_sold.label("Units Sold"),
                Sale.region.label("Region"),
                Sale.channel.label("Channel"),
                Sale.year.label("Year"),
            )
            .join(PhoneModel, PhoneModel.id == Sale.model_id)
            .join(Brand, Brand.id == PhoneModel.brand_id)
        )
        df = pd.read_sql(query.statement, db.bind)

    if format == "csv":
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode()), as_attachment=True, download_name="sales_export.csv")
    if format == "xlsx":
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        buf.seek(0)
        return send_file(buf, as_attachment=True, download_name="sales_export.xlsx")
    if format == "pdf":
        # Simple tabular PDF via pandas -> string; for production, create a rich PDF report
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        pdf_buf = io.BytesIO()
        c = canvas.Canvas(pdf_buf, pagesize=A4)
        textobject = c.beginText(40, 800)
        textobject.textLine("Mobile Sales Export")
        textobject.textLine("")
        for line in df.head(100).to_string(index=False).splitlines():
            textobject.textLine(line[:95])
        c.drawText(textobject)
        c.showPage()
        c.save()
        pdf_buf.seek(0)
        return send_file(pdf_buf, as_attachment=True, download_name="sales_export.pdf")
    return redirect(url_for("dashboard.index"))


