# University Class Timetable

This project is a web-based timetable management system for a university. It allows users to view the class schedule and enables administrators to manage and update the timetable.

## Features

- User registration and login
- Admin registration and login
- JWT-based authentication
- Admin-only protected routes
- Timetable creation, update, and deletion (by admins)
- Timetable filtering (by day or course) for all users
- PDF report generation
- PostgreSQL database
- Flask REST API backend

## Technologies Used

- Python (Flask)
- HTML, CSS, JavaScript (for frontend)
- PostgreSQL
- JWT for authentication
- ReportLab for PDF generation
- DBeaver (for managing the PostgreSQL database)
- dotenv (.env) for secure environment variables

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/university-timetable.git
   cd university-timetable
   ```

2. **Create a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root folder and add:
   ```env
   DB_HOST=localhost
   DB_NAME=your_database_name
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_PORT=5432
   SECRET_KEY=your_secret_key
   ```

5. **Run the App**
   ```bash
   python app.py
   ```

6. **API Testing**

   Use Postman to test API endpoints for:

   - User/Admin registration
   - Login
   - Protected routes
   - Timetable operations

## Project Structure

```
timetable_project/
│
├── app.py               # Main Flask app
├── auth.py              # Authentication and protected route logic
├── db.py                # PostgreSQL database connection
├── .env                 # Environment variables (hidden)
├── templates/           # HTML templates (if any)
├── static/              # Static files: CSS, JS
├── requirements.txt     # Python dependencies
└── README.md
```
