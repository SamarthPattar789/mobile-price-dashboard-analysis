## Mobile Sales Analytics Web Portal

Interactive dashboard with authentication and Power BI embedding.

### Quick Start (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Optional: set env vars
$env:SECRET_KEY = "change-me"
# For SQLite default, skip DATABASE_URI. For Postgres:
# $env:DATABASE_URI = "postgresql+psycopg2://user:pass@localhost:5432/mobiles"
# Power BI report URL (secure embed or publish-to-web for testing):
# $env:PBI_REPORT_URL = "https://app.powerbi.com/view?r=..."

python app.py
```

Visit `http://localhost:5000/login`, sign up an admin, then upload `data/sample_sales.csv` under Admin Upload.

### Power BI Embedding

- For quick demos, use Publish to Web URL (not for sensitive data) and set `PBI_REPORT_URL`.
- For production, use Power BI Embedded with service principal to generate an embed token and supply an app route that injects the token into the iframe or uses the JavaScript SDK. This scaffold expects a ready-to-use iframe URL via `PBI_REPORT_URL`.

### Features

- Login/signup with roles (admin/user)
- Admin CSV upload to populate brands/models/sales
- Export data as CSV/Excel/PDF
- Responsive Bootstrap UI
- Power BI report iframe on the dashboard


