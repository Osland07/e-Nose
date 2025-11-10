# E-Nose Project Structure

## Project Overview
This is an electronic nose (e-Nose) application for pork analysis implemented in Python.

## Directory Structure
```
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── assets/                # Static assets directory
├── database/              # Database related modules
│   └── __init__.py       # Database initialization
└── ui/                   # User Interface modules
    ├── __init__.py       # UI package initialization
    ├── history_page.py   # History page implementation
    ├── main_page.py      # Main page implementation
    └── main_window.py    # Main window implementation
```

## Components Description

### Root Directory
- `main.py`: The main entry point of the application
- `requirements.txt`: Lists all Python package dependencies required for the project

### Directories

#### assets/
Contains static assets used in the application such as images, icons, or other resources.

#### database/
Database-related implementation and configuration:
- `__init__.py`: Initializes the database module and sets up necessary configurations

#### ui/
User interface implementation files:
- `__init__.py`: UI package initialization
- `history_page.py`: Implementation of the history viewing page
- `main_page.py`: Implementation of the main application page
- `main_window.py`: Main window implementation and layout management

## Getting Started
To run this project, make sure you have all the required dependencies installed:
```bash
pip install -r requirements.txt
```

Then run the application using:
```bash
python main.py
```