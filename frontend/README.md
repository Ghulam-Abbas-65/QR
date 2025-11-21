# QR Code Generator - React Frontend

Professional React frontend for the QR Code Generator with Analytics.

## Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm start
```

The app will open at http://localhost:3000

## Features

- Generate QR codes from URLs
- Generate QR codes from uploaded files
- Download QR codes in multiple formats (PNG, JPG, WEBP, BMP, SVG)
- View comprehensive analytics with filters
- Search and browse QR codes
- Clean, modern UI with gradient design

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.js
│   │   └── Header.css
│   ├── pages/
│   │   ├── Home.js
│   │   ├── QRResult.js
│   │   ├── Analytics.js
│   │   ├── Analytics.css
│   │   └── CheckAnalytics.js
│   ├── services/
│   │   └── api.js
│   ├── App.js
│   ├── App.css
│   ├── index.js
│   └── index.css
└── package.json
```

## Technologies

- React 18
- React Router 6
- Axios for API calls
- CSS3 with Flexbox/Grid

## API Endpoints

All API calls go to `http://localhost:8000/api/`

- POST `/generate/url/` - Generate QR from URL
- POST `/generate/file/` - Generate QR from file
- GET `/qr-codes/` - List QR codes
- GET `/qr-codes/:id/` - Get QR code details
- GET `/qr-codes/:id/analytics/` - Get analytics

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.
