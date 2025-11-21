# QR Code Generator - Full Stack Setup Guide

Production-grade QR Code Generator with Django REST API backend and React frontend.

## 🏗️ Project Structure

```
QR/
├── backend/                    # Django REST API
│   ├── qr_project/            # Django project settings
│   ├── qr_generator/          # Main app
│   │   ├── models.py          # Database models
│   │   ├── views.py           # Template views (old)
│   │   ├── api_views.py       # REST API views
│   │   ├── serializers.py     # API serializers
│   │   ├── urls.py            # Template URLs
│   │   └── api_urls.py        # API URLs
│   ├── media/                 # Uploaded files & QR codes
│   ├── manage.py
│   └── requirements.txt
│
└── frontend/                   # React SPA
    ├── public/
    ├── src/
    │   ├── components/        # Reusable components
    │   ├── pages/             # Page components
    │   ├── services/          # API service
    │   └── App.js
    ├── package.json
    └── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL (installed with pgAdmin)

---

## Backend Setup (Django)

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure PostgreSQL
Open pgAdmin and create database:
```sql
CREATE DATABASE qr_database;
```

### 3. Update Database Password
Edit `qr_project/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'qr_database',
        'USER': 'postgres',
        'PASSWORD': 'YOUR_PASSWORD_HERE',  # Change this
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Run Migrations
```bash
python manage.py migrate
```

### 5. Create Admin User (Optional)
```bash
python manage.py createsuperuser
```

### 6. Start Backend Server
```bash
python manage.py runserver
```

Backend runs at: **http://localhost:8000**

---

## Frontend Setup (React)

### 1. Navigate to Frontend
```bash
cd frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Frontend Server
```bash
npm start
```

Frontend runs at: **http://localhost:3000**

---

## 🎯 How to Run Both

### Terminal 1 - Backend
```bash
python manage.py runserver
```

### Terminal 2 - Frontend
```bash
cd frontend
npm start
```

Then open: **http://localhost:3000**

---

## 📊 Database Tables

### Main Tables:
1. **qr_generator_uploadedfile** - Stores uploaded files with UUID tokens
2. **qr_generator_qrcode** - Stores generated QR codes
3. **qr_generator_scananalytics** - Tracks every QR scan with analytics

### System Tables:
- Django auth tables (users, permissions)
- Django admin tables
- Django session tables

---

## 🔌 API Endpoints

Base URL: `http://localhost:8000/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate/url/` | Generate QR from URL |
| POST | `/generate/file/` | Generate QR from file |
| GET | `/qr-codes/` | List QR codes (with search) |
| GET | `/qr-codes/:id/` | Get QR code details |
| GET | `/qr-codes/:id/analytics/` | Get analytics with filters |

---

## 🎨 Features

### Backend (Django REST API):
- ✅ RESTful API with Django REST Framework
- ✅ CORS enabled for React frontend
- ✅ PostgreSQL database
- ✅ File upload with secure UUID tokens
- ✅ QR code generation in multiple formats
- ✅ Analytics tracking (IP, location, device, browser)
- ✅ Filtering and search

### Frontend (React):
- ✅ Modern React 18 with Hooks
- ✅ React Router for navigation
- ✅ Axios for API calls
- ✅ Clean component structure
- ✅ Responsive design
- ✅ Professional UI with gradients
- ✅ Real-time filtering
- ✅ Multiple download formats

---

## 🔒 Security Features

1. **File Security:**
   - Files accessed via random UUID tokens
   - Original paths never exposed
   - No directory traversal vulnerabilities

2. **API Security:**
   - CORS configured for specific origins
   - CSRF protection enabled
   - Input validation with serializers

3. **Database:**
   - PostgreSQL with proper indexing
   - Foreign key relationships
   - Data integrity constraints

---

## 📦 Technologies Used

### Backend:
- Django 4.2
- Django REST Framework
- PostgreSQL
- qrcode library
- Pillow (image processing)
- requests (IP geolocation)
- user-agents (device detection)

### Frontend:
- React 18
- React Router 6
- Axios
- CSS3 (Flexbox/Grid)

---

## 🛠️ Development Tips

### Backend:
- Admin panel: http://localhost:8000/admin/
- API docs: Use tools like Postman or Thunder Client
- Database: View in pgAdmin

### Frontend:
- Hot reload enabled (changes reflect instantly)
- React DevTools recommended
- Console logs for debugging

---

## 🚢 Production Deployment

### Backend:
1. Set `DEBUG = False` in settings.py
2. Configure `ALLOWED_HOSTS`
3. Use environment variables for secrets
4. Set up static file serving
5. Use Gunicorn/uWSGI
6. Configure Nginx

### Frontend:
1. Run `npm run build`
2. Serve `build/` folder with Nginx
3. Update API base URL to production

---

## 📝 Code Quality

- **Clean Code:** Simple, readable, well-commented
- **Best Practices:** Follows Django and React conventions
- **Maintainable:** Clear structure, separation of concerns
- **Production-Ready:** Error handling, validation, security

---

## 🐛 Troubleshooting

### Backend Issues:
- **Database error:** Check PostgreSQL is running
- **CORS error:** Verify CORS_ALLOWED_ORIGINS in settings.py
- **Import error:** Run `pip install -r requirements.txt`

### Frontend Issues:
- **API error:** Ensure backend is running on port 8000
- **Module not found:** Run `npm install`
- **Port in use:** Kill process on port 3000

---

## 📚 Learning Resources

### Django:
- Official docs: https://docs.djangoproject.com/
- DRF docs: https://www.django-rest-framework.org/

### React:
- Official docs: https://react.dev/
- React Router: https://reactrouter.com/

---

## ✅ Next Steps

1. Test all features
2. Add authentication (JWT tokens)
3. Add rate limiting
4. Implement caching
5. Add unit tests
6. Set up CI/CD
7. Deploy to production

---

**Built with ❤️ using Django + React**
