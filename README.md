# Django Project

A new Django project setup with best practices.

## Setup Instructions

### 1. Activate Virtual Environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Apply Migrations

```powershell
python manage.py migrate
```

### 4. Create Superuser

```powershell
python manage.py createsuperuser
```

### 5. Run Development Server

```powershell
python manage.py runserver
```

Visit `http://127.0.0.1:8000` in your browser.

## Project Structure

- `config/` - Project configuration
- `main/` - Main app
- `manage.py` - Django management script
- `requirements.txt` - Python dependencies
- `.env` - Environment variables

## Admin Panel

Access the admin panel at `http://127.0.0.1:8000/admin/`
