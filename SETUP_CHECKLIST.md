# ✅ Setup Checklist

Follow these steps in order to get your application running.

## Backend Setup

- [ ] 1. Install Python dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] 2. Open pgAdmin and create database
  ```sql
  CREATE DATABASE qr_database;
  ```

- [ ] 3. Update database password in `qr_project/settings.py`
  - Find line: `'PASSWORD': '12345678',`
  - Change to your PostgreSQL password

- [ ] 4. Run database migrations
  ```bash
  python manage.py migrate
  ```

- [ ] 5. (Optional) Create admin user
  ```bash
  python manage.py createsuperuser
  ```

- [ ] 6. Test backend server
  ```bash
  python manage.py runserver
  ```
  - Should start on http://localhost:8000
  - Press Ctrl+C to stop

## Frontend Setup

- [ ] 7. Navigate to frontend folder
  ```bash
  cd frontend
  ```

- [ ] 8. Install Node.js dependencies
  ```bash
  npm install
  ```
  - This may take 2-3 minutes

- [ ] 9. Go back to root folder
  ```bash
  cd ..
  ```

## Running the Application

- [ ] 10. Start backend (Terminal 1)
  ```bash
  python manage.py runserver
  ```
  - Keep this terminal open
  - Backend runs on port 8000

- [ ] 11. Start frontend (Terminal 2)
  ```bash
  cd frontend
  npm start
  ```
  - Keep this terminal open
  - Frontend runs on port 3000
  - Browser should open automatically

- [ ] 12. Test the application
  - Visit: http://localhost:3000
  - Try generating a QR code from URL
  - Try uploading a file and generating QR
  - Check analytics dashboard

## Verification

- [ ] Backend is running on http://localhost:8000
- [ ] Frontend is running on http://localhost:3000
- [ ] Can generate QR from URL
- [ ] Can generate QR from file
- [ ] Can download QR in different formats
- [ ] Can view analytics
- [ ] Can filter analytics
- [ ] Can search QR codes

## If Something Goes Wrong

### Backend Issues:
- **Error: "No module named 'rest_framework'"**
  - Run: `pip install djangorestframework django-cors-headers`

- **Error: "database does not exist"**
  - Create database in pgAdmin: `CREATE DATABASE qr_database;`

- **Error: "password authentication failed"**
  - Update password in `qr_project/settings.py`

### Frontend Issues:
- **Error: "npm: command not found"**
  - Install Node.js from https://nodejs.org/

- **Error: "Cannot find module"**
  - Run: `cd frontend && npm install`

- **Error: "Port 3000 is already in use"**
  - Kill the process or use different port

### CORS Issues:
- **Error: "CORS policy blocked"**
  - Make sure backend runs on port 8000
  - Make sure frontend runs on port 3000
  - Check CORS settings in `qr_project/settings.py`

## Quick Commands Reference

### Backend:
```bash
python manage.py runserver          # Start server
python manage.py migrate            # Run migrations
python manage.py createsuperuser    # Create admin
python manage.py makemigrations     # Create migrations
```

### Frontend:
```bash
npm start                           # Start dev server
npm install                         # Install dependencies
npm run build                       # Build for production
```

## Next Steps After Setup

1. ✅ Test all features
2. ✅ Generate some QR codes
3. ✅ Check analytics dashboard
4. ✅ Try filtering analytics
5. ✅ Download QR in different formats
6. ✅ Explore the code structure
7. ✅ Read the documentation files

## Documentation Files

- `README.md` - Project overview
- `QUICK_START.md` - Quick setup guide
- `PROJECT_SETUP.md` - Complete documentation
- `MIGRATION_GUIDE.md` - Architecture explanation
- `frontend/README.md` - React app docs

---

**Once all checkboxes are checked, you're ready to go! 🎉**
