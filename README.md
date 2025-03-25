# Junie Django Lab

A Django project template with modern Python tooling.

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