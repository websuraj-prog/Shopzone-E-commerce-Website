# 🛒 Shopzone – Full Stack Django E-commerce Website

Shopzone is a **modern full-featured E-commerce web application** built using **Django**.
It includes user authentication, product management, cart system, order functionality, and secure deployment configuration.

This project demonstrates **full-stack development skills**, including backend logic, database integration, authentication, and production deployment.

---

## 📸 Screenshots
<img width="1919" height="1013" alt="Screenshot 2026-03-18 174937" src="https://github.com/user-attachments/assets/516845d9-ec8a-4778-99b0-17edcc0c5833" />
<img width="1919" height="1010" alt="Screenshot 2026-03-18 174907" src="https://github.com/user-attachments/assets/863cacb5-aa59-4805-ba56-4cbcd2ecbe70" />
<img width="1919" height="1012" alt="Screenshot 2026-03-18 174728" src="https://github.com/user-attachments/assets/0567f384-5a08-4309-ba95-dbb99cfe2eea" />
<img width="1919" height="1017" alt="Screenshot 2026-03-18 174840" src="https://github.com/user-attachments/assets/0051cf3e-d35d-4b96-8276-09e9365697ac" />


## 📌 Features

### 👤 User Features

* User Registration & Login system
* Secure Authentication
* Product browsing
* Add to Cart functionality
* Order placement system
* Responsive UI design
* Session-based cart
* Email integration (configurable)

### 🛠 Admin Features

* Django Admin Panel
* Product management (Add, Edit, Delete)
* User management
* Order tracking

### 💻 Technical Features

* Django MVC architecture
* PostgreSQL / SQLite database support
* Static & Media file handling
* Secure production settings
* Environment variable configuration
* WhiteNoise static file deployment
* Crispy Forms for professional UI

---

## 🏗 Tech Stack

### Frontend

* HTML5
* CSS3
* Bootstrap 4
* Django Templates

### Backend

* Python
* Django Framework

### Database

* SQLite (development)
* PostgreSQL (production ready)

---

## 📂 Project Structure

```
Shopzone
│
├── shopzone
│   ├── accounts      # User authentication
│   ├── base          # Base app (shared logic)
│   ├── home          # Homepage
│   ├── products      # Product module
│   ├── templates     # HTML templates
│   ├── static        # CSS, JS files
│   ├── public        # Media files
│   └── ecomm         # Project settings
│       ├── settings.py
│       ├── urls.py
│       ├── wsgi.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## ⚙ Installation Guide

### 1️⃣ Clone repository

```
git clone https://github.com/your-username/shopzone.git
cd shopzone
```

### 2️⃣ Create virtual environment

```
python -m venv venv
```

Activate environment:

Windows

```
venv\Scripts\activate
```

Mac/Linux

```
source venv/bin/activate
```

### 3️⃣ Install dependencies

```
pip install -r requirements.txt
```

### 4️⃣ Apply migrations

```
python manage.py migrate
```

### 5️⃣ Create superuser

```
python manage.py createsuperuser
```

### 6️⃣ Run server

```
python manage.py runserver
```

Open browser:

```
http://127.0.0.1:8000/
```

---

## 🔐 Environment Variables

Create `.env` file:

```
DEBUG=True
SECRET_KEY=your_secret_key
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=sqlite:///db.sqlite3

RAZORPAY_KEY_ID=your_key
RAZORPAY_SECRET_KEY=your_secret
```

---

## 📦 Requirements

```
Django
gunicorn
whitenoise
dj-database-url
python-decouple
crispy-forms
crispy-bootstrap4
psycopg2
```

---

## 👨‍💻 Author

**Suraj Vishwakarma**
Full Stack Web Developer

GitHub: https://github.com/websuraj-prog

---

## ⭐ Support

If you like this project:

Give ⭐ to this repository
Share with others
Contribute improvements

---

## 📜 License

This project is open-source and free to use for learning purposes.
