# Small Business Analysis API - Full Documentation

## 1. Project Summary
This project is a FastAPI backend for ecommerce business analysis.

It:
- accepts Excel uploads,
- processes data through a 3-stage pipeline,
- persists cleaned/merged data in SQLite,
- serves analysis endpoints as JSON,
- generates PDF and Excel BI reports.

Primary domain focus: small business ecommerce metrics (revenue, profitability, inventory, expenses, growth, break-even, cashflow).

## 2. Tech Stack
- Python 3.12 (recommended)
- FastAPI
- Uvicorn
- pandas + numpy
- matplotlib + seaborn (used by notebook visualizations)
- openpyxl (Excel IO)
- fpdf2 (PDF report)
- sqlite3 (built-in) for persistent storage

Dependencies file: `ecommerce_backend/requirements.txt`
Note: `matplotlib` and `seaborn` are currently used in `Nepal_Ecommerce_BI_2025.ipynb`, not in the FastAPI runtime routes.

## 3. Project Structure
Key backend folders/files:
- `ecommerce_backend/main.py`: app entrypoint + startup loading behavior.
- `ecommerce_backend/routes/`: API routes.
- `ecommerce_backend/pipeline/`: ingest/clean/transform stages + runner.
- `ecommerce_backend/analysis/`: section-level analytics functions.
- `ecommerce_backend/reports/report_generator.py`: PDF/Excel output generation.
- `ecommerce_backend/database.py`: SQLite persistence and loading.
- `ecommerce_backend/state.py`: in-memory cache used by routes.
- `ecommerce_backend/logger.py`: centralized logging setup.
- `ecommerce_backend/data/raw/`: uploaded source files.
- `ecommerce_backend/data/app.db`: SQLite database.
- `ecommerce_backend/data/exports/`: generated reports.

## 4. Data Input Contract
Uploaded Excel workbook must contain these sheets:
- `Inventory`
- `Sales`
- `Purchase`
- `Expenses`

Expected columns are inferred from pipeline and analysis logic:

### Inventory
- `ItemID`
- `ItemName`
- `Category`
- `OpeningStock`
- `ReorderLevel`
- `SellingPrice`

### Sales
- `Date`
- `ItemID`
- `QuantitySold`
- `UnitPriceSold`
- `Discount`

### Purchase
- `Date`
- `ItemID` (not strictly required for all calculations but expected in dataset design)
- `QuantityBought`
- `UnitCost`

### Expenses
- `Month` (full month name expected in growth logic: e.g., `January`)
- One or more expense columns from:
  - `Salary`
  - `Rent`
  - `Utilities`
  - `Marketing`
  - `EMI`
  - `Interest`
  - `Other` (or `Others`, which is normalized to `Other`)

## 5. End-to-End Processing Flow
### 5.1 Upload Path (`POST /upload`)
1. File is saved into `data/raw`.
2. Pipeline is run:
   - Stage 1 ingest
   - Stage 2 clean
   - Stage 3 transform (compute derived vars)
3. Cleaned DataFrames are merged into SQLite tables (`inv`, `sales`, `purch`, `exp`).
4. Duplicate rows are removed per table.
5. In-memory `state.store` is refreshed from SQLite.

### 5.2 Startup Path (`main.py`)
On application startup:
1. SQLite is initialized.
2. If SQLite has full data, load it into `state.store`.
3. If SQLite is empty, bootstrap from any existing Excel files in `data/raw`:
   - each file runs through pipeline,
   - data is persisted to SQLite,
   - `state.store` is loaded from SQLite.

This allows analysis without requiring a fresh upload every restart.

## 6. Pipeline Stages
### Stage 1: Ingest (`stage_01_ingest.py`)
- Reads the 4 required sheets via `pd.read_excel`.
- Places raw DataFrames in context keys:
  - `inv`, `sales`, `purch`, `exp`.

### Stage 2: Clean (`stage_02_clean.py`)
- Normalizes column names and trims key text fields.
- Renames expense column `Others` -> `Other` (before numeric conversion).
- Parses sales/purchase `Date` columns to datetime.
- Converts numeric columns with `pd.to_numeric(..., errors="coerce")`.
- Handles missing values dynamically using runtime statistics from each sheet:
  - text columns: fill with column `mode`
  - numeric columns: fill with column `median`
- Inventory rules:
  - drop rows where `ItemName` is missing/blank
  - fill `Category` by mode
  - fill `OpeningStock`, `CostPrice`, `SellingPrice`, `ReorderLevel` by median
- Sales rules:
  - fill `QuantitySold`, `UnitPriceSold`, `Discount` by median
  - fill `DeliveryType`, `PaymentMode` by mode
  - `DeliveryCharge` uses conditional median fill:
    - pickup rows: median of pickup `DeliveryCharge`
    - non-pickup rows: median of non-pickup `DeliveryCharge`
    - fallback: overall `DeliveryCharge` median if a segment has no non-null values
- Purchase rules:
  - fill `QuantityBought`, `UnitCost`, `TransportCost` by median
  - fill `PaymentType` by mode
- Expenses rules:
  - fill `Salary`, `Rent`, `Utilities`, `Marketing`, `EMI`, `Interest`, `Other` by median
- Removes duplicate rows in inventory/sales/purchase.
- Removes invalid transactional rows:
  - `QuantitySold` > 0, `QuantityBought` > 0
  - `UnitPriceSold` >= 0, `UnitCost` >= 0
- Drops fully empty rows for sales and purchase.
- Sorts sales/purchase by `Date`.
- Derives time fields:
  - sales: `Month`, `Year`, `MonthName`, `MonthNum`
  - purchase: `Month`, `Year`

### Stage 3: Transform (`stage_03_transform.py`)
Computes aggregate variables in `context["vars"]`:
- `TotalQuantitySold`
- `TotalQuantityBought`
- `GrossRevenue`
- `TotalDiscount`
- `TotalRevenue`
- `TotalPurchaseCost`
- `WeightedAvgCost`
- `COGS`
- `TotalOperatingExpense`

These are reused by all analysis modules.

## 7. SQLite Persistence Model
File: `ecommerce_backend/data/app.db`

Tables:
- `inv`
- `sales`
- `purch`
- `exp`
- `upload_log`:
  - `id` INTEGER PRIMARY KEY
  - `filename` TEXT
  - `uploaded_at` TEXT (default current timestamp)

Merge strategy:
- New rows are appended.
- Deduplication is performed using all columns in each table:
  - for identical rows, only earliest `rowid` is kept.

## 8. Runtime State Model
`state.store` contains:
- `inv`
- `sales`
- `purch`
- `exp`
- `vars`
- `ready`

Important:
- SQLite is the source of truth.
- `state.store` is an in-memory cache refreshed from database.

## 9. API Reference
Base app: FastAPI default docs at:
- `GET /docs`
- `GET /redoc`

### 9.1 Upload
#### `POST /upload`
Uploads one Excel file and merges it into existing dataset.

Request:
- form-data file field: `file`

Success response:
```json
{
  "message": "Upload successful. Data merged into SQLite.",
  "file": "your_file.xlsx"
}
```

Errors:
- `400`: invalid file extension
- `500`: pipeline execution error

### 9.2 Analysis
Prefix: `/analysis`

Endpoints:
- `GET /analysis/profitability`
- `GET /analysis/discounts`
- `GET /analysis/inventory`
- `GET /analysis/products`
- `GET /analysis/expenses`
- `GET /analysis/monthly-growth`
- `GET /analysis/breakeven`
- `GET /analysis/cashflow`
- `GET /analysis/sales-trend`
- `GET /analysis/demand-vs-stock`
- `GET /analysis/cost-efficiency`

If data is unavailable:
- `400` with detail:
  - `No data loaded. Upload a file or place an Excel file in data/raw and restart.`

### 9.3 Report Export
Prefix: `/report`

Endpoints:
- `GET /report/pdf`
  - Returns `BI_Report.pdf`
- `GET /report/excel`
  - Returns `BI_Report.xlsx`

## 10. Analysis Output Definitions
### Profitability
- Revenue, discount, COGS, gross/net profit, margins.
- Includes guard for zero revenue to avoid division errors.

### Discounts
- Discount amount, discount share of revenue, discounted transaction ratio, monthly discount trend.

### Inventory
- Inventory turnover, days inventory outstanding, below-reorder alerts.

### Products
- Top 10 products by revenue, category revenue contribution.

### Expenses
- Opex share of revenue, expense category breakdown, monthly expenses.

### Monthly Growth
- Month-wise revenue/profit and growth percentages.

### Break-Even
- Product contribution per unit, break-even units, margin of safety.

### Cashflow
- Total inflow/outflow/net movement and monthly cashflow.

### Sales Trend
- Month-wise sales revenue trend (QuantitySold × UnitPriceSold).
- Optional monthly breakdown by PaymentMode and DeliveryType.

### Demand vs Stock
- Item-wise stock and demand comparison.
- Flags potential overstock and stockout-risk items.

### Cost Efficiency
- Month-wise purchase costs vs operating expenses.
- Includes combined cost and expense-to-purchase ratio trend.

## 11. Report Generation
File: `reports/report_generator.py`

### PDF (`BI_Report.pdf`)
Contains executive summaries and dedicated visualization pages for trend-heavy analyses, including:
- Profitability snapshot
- Discounts snapshot
- Inventory + Demand vs Stock summaries
- Expense + Break-even summaries
- Visual charts for monthly growth, sales trend, cashflow, category revenue, and cost efficiency

### Excel (`BI_Report.xlsx`)
Sheets generated for all analyses with both summary/detail tables, plus a `Dashboard Charts` worksheet with embedded visuals.
Key sheets include:
- `Profitability`, `Discounts Summary`, `Discounts Monthly`
- `Inventory Summary`, `Reorder Alerts`
- `Monthly Growth`, `Top Products`, `Category Revenue`
- `Expenses`, `Expenses Summary`, `Monthly Expenses`
- `Cash Flow`, `Cash Flow Summary`
- `Break-Even`, `Break-Even Summary`
- `Sales Trend`, `Sales by Payment`, `Sales by Delivery`
- `Demand vs Stock`, `Overstock Items`, `Stockout Risk`, `Demand Stock Summary`
- `Cost Efficiency`, `Cost Efficiency Summary`
- `Dashboard Charts`

## 12. Setup and Run
From project root:

1. Create/activate virtual environment (if needed).
2. Install requirements:
```bash
pip install -r ecommerce_backend/requirements.txt
```
3. Run backend:
```bash
cd ecommerce_backend
uvicorn main:app --reload
```

Default URL:
- `http://127.0.0.1:8000`

## 13. Logging and Monitoring
Logger:
- Console output + rotating file log.
- Log file: `ecommerce_backend/logs/app.log`
- Rotation: 5 MB x 3 backups.

Useful log events:
- startup source (SQLite load vs raw bootstrap),
- pipeline stage timing,
- upload and persistence events,
- report generation completion.

## 14. Operational Notes
- Uploading same file repeatedly does not explode duplicates for exact identical rows (dedupe applies).
- Schema for `inv/sales/purch/exp` tables is inferred from first inserted DataFrame via pandas `to_sql`.
- If source sheet structure changes significantly, table mismatch can occur on future appends.

## 15. Known Limitations
- No explicit DB migrations/versioning yet.
- Deduplication is full-row based; no business-key upsert logic.
- Single-process in-memory cache is fine for local/small deployment; multi-worker deployments need cache strategy.
- Validation for required columns is implicit; explicit schema validation can be added.

## 16. Suggested Next Improvements
1. Add strict input schema validation per sheet with clear error messages.
2. Add Alembic migrations and explicit SQL schema.
3. Add business-key dedupe/upsert policy (e.g., by transaction ID/date/item).
4. Add unit tests for pipeline and route-level integration tests.
5. Add authentication if exposed beyond local/internal network.

## 17. Quick Troubleshooting
### "No data loaded" on analysis endpoints
- Ensure at least one valid upload succeeded, or place valid Excel in `data/raw` and restart app.

### Report endpoints failing
- Check analysis endpoints first; report generation depends on same store data.

### Pipeline error on upload
- Verify required sheet names and columns.
- Inspect `logs/app.log` for exact traceback.

### Suspected stale data
- Restart app to reload from SQLite.
- Inspect `data/app.db` and `upload_log` table.
