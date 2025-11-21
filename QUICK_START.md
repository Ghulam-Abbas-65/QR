# 🚀 Quick Start Guide

## Step-by-Step Setup

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations
```bash
python manage.py migrate
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 4. Start Both Servers

**Option A: Using Scripts (Windows)**
- Double-click `start_backend.bat` (starts Django on port 8000)
- Double-click `start_frontend.bat` (starts React on port 3000)

**Option B: Manual**

Terminal 1:
```bash
python manage.py runserver
```

Terminal 2:
```bash
cd frontend
npm start
```

### 5. Open Browser
Go to: **http://localhost:3000**

---

## ✅ What You Get

### Frontend (React - Port 3000):
- 🏠 Home page with URL and File QR generators
- 📊 Analytics dashboard with filters
- 🔍 Search QR codes
- 💾 Download QR in 6 formats (PNG, JPG, JPEG, WEBP, BMP, SVG)

### Backend (Django - Port 8000):
- 🔌 REST API endpoints
- 📁 File storage with secure tokens
- 📊 Analytics tracking
- 🗄️ PostgreSQL database
- 👨‍💼 Admin panel at /admin/

---

## 🎯 How It Works

1. **User visits** → http://localhost:3000
2. **React frontend** → Makes API calls to Django
3. **Django backend** → Processes requests, saves to PostgreSQL
4. **Response** → React displays results

---

## 📁 Project Structure

```
QR/
├── qr_project/          # Django settings
├── qr_generator/        # Main Django app
│   ├── api_views.py     # REST API endpoints
│   ├── serializers.py   # Data serialization
│   └── models.py        # Database models
├── frontend/            # React app
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable components
│   │   └── services/    # API calls
│   └── package.json
├── media/               # Uploaded files & QR codes
└── requirements.txt     # Python dependencies
```

---

## 🔧 Common Commands

### Backend:
```bash
python manage.py runserver          # Start server
python manage.py migrate            # Run migrations
python manage.py createsuperuser    # Create admin user
python manage.py makemigrations     # Create new migrations
```

### Frontend:
```bash
npm start                           # Start dev server
npm run build                       # Build for production
npm install                         # Install dependencies
```

---

## 🐛 Troubleshooting

**Backend won't start:**
- Check PostgreSQL is running
- Verify database password in `qr_project/settings.py`
- Run `pip install -r requirements.txt`

**Frontend won't start:**
- Run `npm install` in frontend folder
- Check port 3000 is not in use
- Ensure Node.js is installed

**CORS errors:**
- Backend must run on port 8000
- Frontend must run on port 3000
- Check CORS settings in `qr_project/settings.py`

---

## 📚 Full Documentation

See `PROJECT_SETUP.md` for complete documentation.

---

**Ready to code! 🎉**
