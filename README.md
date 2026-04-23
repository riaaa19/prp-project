# College Club & Event Management System

A modular Python desktop application built with Tkinter for managing college club events, student registrations, and admin event control.

## Project Overview

This app provides:
- Admin login and dashboard
- Event creation, editing, and deletion
- Student login and event registration
- Registration tracking and export
- Clean Tkinter user interface
- SQLite database integration with seeded demo data

## Project Structure

```
prp-project/
│── main.py
│── README.md
│── database/
│     └── db.py
│── models/
│     ├── user.py
│     ├── event.py
│     └── registration.py
│── services/
│     ├── auth_service.py
│     ├── event_service.py
│     └── registration_service.py
│── ui/
│     ├── login_page.py
│     ├── admin_dashboard.py
│     ├── student_dashboard.py
│     └── components.py
│── utils/
│     └── validators.py
```

## Features

### Authentication
- Login with email and password
- Email validation using regex
- Role-based navigation: admin or student

### Admin Dashboard
- Add events with name, date, and club
- View, edit, and delete events
- View student registrations
- Export registrations as CSV

### Student Dashboard
- Browse all available events
- Register for events
- View registered events
- Cancel registrations

### Database
- SQLite database stored in `database/college_club.db`
- Tables: `users`, `clubs`, `events`, `registrations`, plus supporting tables
- Automatic table creation and sample data seeding on first run

## Getting Started

### Requirements
- Python 3.8 or higher
- Tkinter (included with standard Python installers on Windows/macOS/Linux)

### Run the App

1. Open a terminal or PowerShell window.
2. Change directory to the project folder:
   ```powershell
   cd "c:\Users\Jiya\Downloads\PRP\prp-project"
   ```
3. Run the main application:
   ```powershell
   python main.py
   ```

### Default Demo Accounts

- Admin: `admin@college.edu` / `admin123`
- Student: `alice@college.edu` / `alice123`
- Student: `bob@college.edu` / `bob123`

## Notes

- The SQLite database file is created automatically in `database/college_club.db`.
- The app uses a modular architecture to separate UI, services, models, and database logic.
- Add more event and user data from the admin dashboard after logging in.

## Contribution

Feel free to extend the project by adding user registration approval, improved event search, or enhanced reporting features.
