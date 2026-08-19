# Professional E-Commerce Login System (Flask + MySQL)

This project implements a responsive OTP-based login flow using:
- HTML, CSS, JavaScript
- Python Flask backend
- MySQL storage

## Features

- Login page opens first (`/`)
- Login using phone number or Gmail/email
- New users can click **Create a New Account**
- Backend-generated 6-digit OTP with expiry + attempt limits
- OTP verification with server-side hash checking
- Success message: **Login Successfully**
- First-time users are redirected to **Create Profile** page
- Profile fields: Name, Address, City, State, Pincode
- Profile data saved to MySQL
- Returning users go directly to Home page after OTP verification
- Session-based authentication and protected routes

## Folder Structure

```
ecommerce/
|-- app.py
|-- requirements.txt
|-- .env.example
|-- init_db.sql
|-- README.md
|-- app/
|   |-- __init__.py
|   |-- config.py
|   |-- db.py
|   |-- otp_delivery.py
|   |-- routes.py
|   |-- security.py
|   `-- validators.py
|-- templates/
|   |-- base.html
|   |-- login.html
|   |-- verify_otp.html
|   |-- create_profile.html
|   `-- home.html
`-- static/
    |-- css/styles.css
    `-- js/main.js
```

## Setup

1. Create a virtual environment and activate it.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill your values.
4. Make sure MySQL server is running.
5. Run the app:

```bash
python app.py
```

App URL: `http://127.0.0.1:5000`

## OTP Delivery Configuration

- Email OTP: configure SMTP values in `.env`
- SMS OTP: configure Twilio values in `.env`
- Development fallback: when `ALLOW_CONSOLE_OTP=true`, OTP is printed in backend logs if provider is not configured.

## Security Notes

- OTP is generated on the backend and stored as salted hash.
- OTP has expiry and max attempt limit.
- Parameterized SQL queries prevent SQL injection.
- Session is required to access profile/home routes.
- Set a strong `SECRET_KEY` in production and use HTTPS.
