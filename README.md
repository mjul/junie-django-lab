# Junie Django Lab

A Django project template with modern Python tooling. This project includes a basic Django setup with Django Admin enabled and SQLite as the database.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for Python package management.

### Prerequisites

- Python 3.10 or higher
- uv package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd junie-django-lab
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install uv (if not already installed):
   ```bash
   pip install uv
   ```

4. Install dependencies using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

## Using uv

uv is a fast Python package installer and resolver. Here are some common commands:

- Install a package:
  ```bash
  uv pip install <package-name>
  ```

- Install all packages from requirements.txt:
  ```bash
  uv pip install -r requirements.txt
  ```

- Add a package to requirements.txt:
  ```bash
  uv pip install <package-name> --update-requirements requirements.txt
  ```

- Create a virtual environment:
  ```bash
  uv venv
  ```

For more information, visit the [uv documentation](https://github.com/astral-sh/uv).

## Django Project

This is a basic Django project with the following features:
- Django Admin interface enabled
- SQLite database
- Default Django authentication system

### Running the Project

After installing the dependencies, follow these steps to run the project:

1. Apply migrations to set up the database:
   ```bash
   python manage.py migrate
   ```

2. Create a superuser for the admin interface:
   ```bash
   python manage.py createsuperuser
   ```

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Access the admin interface at http://localhost:8000/admin/

### Project Structure

- `config/`: Main project configuration
  - `settings.py`: Project settings including database configuration
  - `urls.py`: URL routing configuration
  - `wsgi.py` and `asgi.py`: Web server configuration
- `manage.py`: Django command-line utility
- `db.sqlite3`: SQLite database file (created after running migrations)
