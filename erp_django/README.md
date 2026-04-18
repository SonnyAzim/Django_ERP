# ERP Core - Django Inventory Management System

A comprehensive ERP system built with Django, featuring inventory management, bill of materials, forecasting, and stock valuation.

## Features

- **Inventory Management** - Full CRUD for items with stock tracking, categories, and bulk operations
- **Bill of Materials (BoM)** - Multi-level product structure with explosion/implosion analysis
- **Forecasting & MRP** - 12-month rolling forecast with Material Requirements Planning
- **Sales & Delivery** - Order management with stock validation
- **Production** - Manufacturing orders with recursive component deduction
- **Stock Valuation** - Financial analytics with KPI dashboard
- **Duty Calculator** - HS code management with tax calculations
- **Supplier Management** - Multi-vendor tracking with lead times

## Tech Stack

- **Backend**: Django 4.2+ & Django REST Framework
- **Database**: SQLite (default) / PostgreSQL (production)
- **Frontend**: HTML5, Tailwind CSS, Chart.js
- **Authentication**: Django Auth

## Quick Start

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## API Endpoints

### Inventory
- `GET /api/inventory/items/` - List items (paginated)
- `POST /api/inventory/items/` - Create item
- `GET /api/inventory/items/{id}/` - Get item
- `PUT /api/inventory/items/{id}/` - Update item
- `DELETE /api/inventory/items/{id}/` - Delete item
- `POST /api/inventory/items/{id}/adjust_stock/` - Adjust stock
- `POST /api/inventory/items/bulk_upload/` - Bulk upload items
- `POST /api/inventory/items/bulk_update_stock/` - Bulk update stock

### Bill of Materials
- `GET /api/bom/` - List BoM entries
- `POST /api/bom/` - Create BoM entry
- `GET /api/bom/{id}/explosion/` - Explode BoM for item
- `GET /api/bom/where_used/?child_id=X` - Find where component is used

### Forecasting & MRP
- `GET /api/forecasts/forecasts/` - List forecasts
- `POST /api/forecasts/mrp/` - Calculate MRP
- `GET /api/forecasts/mrp/material-requirements/?item_id=X&qty=Y` - Get material requirements
- `GET /api/forecasts/mrp/order-plan/` - Generate order plan

### Sales
- `GET /api/sales/orders/` - List orders
- `POST /api/sales/orders/` - Create order (validates finished goods only)
- `POST /api/sales/orders/{id}/deliver/` - Record delivery
- `POST /api/sales/orders/{id}/confirm/` - Confirm order
- `POST /api/sales/orders/{id}/cancel/` - Cancel order

### Production
- `POST /api/production/` - Create production order
- `POST /api/production/bulk_create/` - Bulk create orders
- `POST /api/production/{id}/cancel/` - Cancel order

### Valuation
- `GET /api/valuation/kpi/` - Get KPI summary
- `GET /api/valuation/by-category/` - Value by category
- `GET /api/valuation/top-assets/` - Top 10 assets
- `GET /api/valuation/exposure-analysis/` - High exposure analysis

### Suppliers
- `GET /api/suppliers/` - List suppliers
- `POST /api/suppliers/link_item/` - Link supplier to item
- `GET /api/suppliers/get_for_item/?item_id=X` - Get suppliers for item

### Duty Calculator
- `GET /api/duty/hs-codes/` - List HS codes
- `POST /api/duty/calculator/calculate/` - Calculate duty

## Data Models

### Item Categories
- RAW MATERIAL (RM)
- PACKAGING MATERIAL (PM)
- SEMI-FINISHED GOODS (SFG)
- FINISHED GOODS (FG)

### Transaction Types
- receive - Stock received
- sale - Item sold
- delivery - Delivery to customer
- adjustment - Manual adjustment
- production - Production output

## Environment Variables

- `DJANGO_SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (default: True)

## Production Deployment

For production, use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'erp_db',
        'USER': 'erp_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## License

MIT
