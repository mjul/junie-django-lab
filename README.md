# Django Project with UV Package Manager

This repository contains a Django project that uses UV for package management with the Django admin UI enabled.

## Project Overview

This is a Django web application that leverages the UV package manager for dependency management. The project is set up with Django's admin interface enabled for easy content management.

## Prerequisites

- Python 3.8 or higher
- [UV](https://github.com/astral-sh/uv) package manager

## Setting Up the Project

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Set Up a Virtual Environment with UV

UV is a fast Python package installer and resolver, written in Rust. It's designed to be a drop-in replacement for pip and pip-tools.

```bash
# Install UV if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Windows:
# .venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate
```

### 3. Install Django and Dependencies

```bash
# Install Django and other dependencies
uv pip install django

# Optional: Create a requirements.txt file for your project
echo "django>=4.2.0" > requirements.txt

# Install from requirements.txt
uv pip install -r requirements.txt
```

### 4. Create a New Django Project

```bash
django-admin startproject config .
```

### 5. Create a Django App

```bash
python manage.py startapp core
```

### 6. Enable the Django Admin UI

The Django admin interface is enabled by default in new Django projects. To use it:

1. Create a superuser to access the admin interface:

```bash
python manage.py createsuperuser
```

2. Make sure the admin app is included in your INSTALLED_APPS in settings.py:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Your apps here
    'core',
]
```

3. Ensure the admin URL pattern is included in your project's urls.py:

```python
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Your URL patterns here
]
```

### 7. Run Migrations

```bash
python manage.py migrate
```

### 8. Run the Development Server

```bash
python manage.py runserver
```

The admin interface will be available at http://127.0.0.1:8000/admin/

## Development Workflow

1. Create models in your app's models.py file
2. Register your models with the admin site in your app's admin.py file
3. Run migrations when you make changes to your models:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Using UV for Package Management

UV provides several advantages over traditional pip:

- Faster installation times
- Improved dependency resolution
- Better caching

Common UV commands:

```bash
# Install a package
uv pip install package-name

# Install a specific version
uv pip install package-name==1.0.0

# Upgrade a package
uv pip install --upgrade package-name

# Uninstall a package
uv pip uninstall package-name

# List installed packages
uv pip list

# Generate a requirements.txt file
uv pip freeze > requirements.txt
```

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [UV Documentation](https://github.com/astral-sh/uv)
- [Django Admin Documentation](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)

## License

[Specify your license here]