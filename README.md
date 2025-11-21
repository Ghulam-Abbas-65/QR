# 🔲 QR Code Generator - Full Stack Application

Production-grade QR Code Generator with Django REST API backend and React frontend.

## ✨ Features

- 🔗 Generate QR codes from URLs
- 📁 Generate QR codes from uploaded files (with secure random links)
- 💾 Download QR codes in 6 formats (PNG, JPG, JPEG, WEBP, BMP, SVG)
- 📊 Comprehensive analytics dashboard
- 🔍 Filter analytics by country, city, device, browser
- 🔎 Search and browse QR codes
- 🎨 Modern, professional UI with gradient design
- 🔒 Secure file access via UUID tokens
- 📱 Responsive design

---

## 🚀 Quick Start

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Database
Create PostgreSQL database in pgAdmin:
```sql
CREATE DATABASE qr_database;
```

Update password in `qr_project/settings.py`

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 5. Start Both Servers

**Terminal 1 - Backend:**
```bash
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 6. Open Browser
Visit: **http://localhost:3000**

---

## 📁 Project Structure

```
QR/
├── qr_project/              # Django project settings
├── qr_generator/            # Main Django app
│   ├── models.py            # Database models
│   ├── api_views.py         # REST API endpoints
│   ├── serializers.py       # API serializers
│   ├── api_urls.py          # API routing
│   └── analytics.py         # Analytics helpers
├── frontend/                # React application
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service
│   │   └── App.js           # Main app
│   └── package.json
├── media/                   # Uploaded files & QR codes
├── requirements.txt         # Python dependencies
└── manage.py
```

---

## 🛠️ Technologies

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

## 📊 Database

### Tables:
1. **qr_generator_uploadedfile** - Uploaded files with UUID tokens
2. **qr_generator_qrcode** - Generated QR codes
3. **qr_generator_scananalytics** - Scan analytics data

### Analytics Tracked:
- Total scans
- Unique users
- Countries & Cities (IP geolocation)
- Device types (iPhone, Android, Desktop, etc.)
- Browsers & Operating Systems
- Time of day distribution
- Traffic sources

---

## 🔌 API Endpoints

Base URL: `http://localhost:8000/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate/url/` | Generate QR from URL |
| POST | `/generate/file/` | Generate QR from file |
| GET | `/qr-codes/` | List QR codes |
| GET | `/qr-codes/:id/` | Get QR details |
| GET | `/qr-codes/:id/analytics/` | Get analytics |

---

## 🔒 Security

- Files accessed via random UUID tokens (not direct paths)
- CORS configured for specific origins
- CSRF protection enabled
- Input validation with serializers
- PostgreSQL with proper indexing
- No directory traversal vulnerabilities

---

## 📚 Documentation

- **QUICK_START.md** - Quick setup guide
- **PROJECT_SETUP.md** - Complete documentation
- **MIGRATION_GUIDE.md** - Architecture explanation
- **frontend/README.md** - React app documentation

---

## 🎯 How It Works

1. User visits React frontend (port 3000)
2. React makes API calls to Django backend (port 8000)
3. Django processes requests, saves to PostgreSQL
4. Django returns JSON responses
5. React updates UI dynamically

---

## 🚢 Production Deployment

### Backend:
- Set `DEBUG = False`
- Configure `ALLOWED_HOSTS`
- Use environment variables
- Set up Gunicorn/uWSGI
- Configure Nginx

### Frontend:
- Run `npm run build`
- Serve `build/` folder
- Update API base URL

---

## 🐛 Troubleshooting

**Backend won't start:**
- Check PostgreSQL is running
- Verify database credentials
- Run `pip install -r requirements.txt`

**Frontend won't start:**
- Run `npm install` in frontend folder
- Check port 3000 is available
- Ensure Node.js is installed

**CORS errors:**
- Backend must run on port 8000
- Frontend must run on port 3000

---

## 📝 Code Quality

- ✅ Clean, readable code
- ✅ Well-commented
- ✅ Follows best practices
- ✅ Separation of concerns
- ✅ Production-ready
- ✅ Easy to maintain

---

## 🎓 Learning Resources

- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- React: https://react.dev/
- React Router: https://reactrouter.com/

---

## 📄 License

This project is for educational purposes.

---

**Built with ❤️ using Django + React**

For detailed setup instructions, see `QUICK_START.md`
