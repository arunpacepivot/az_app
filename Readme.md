PacePivot

PROJECT STRUCTURE
-----------------
pacepivot/
├── frontend/   
│   └── src/
│       ├── app/        # Page routes
│       ├── components/ # UI components
│       └── lib/        # Utilities
│
└── backend/    # Django Backend
    ├── core/   # Project config
    └── health/ # Health check app

PREREQUISITES
-------------
- Node.js (v20.x)
- Python (3.11)
- Firebase Account
- Azure Account

FRONTEND SETUP
--------------
1. Navigate to frontend/
2. Run: npm install
3. Create .env.local with Firebase credentials
4. Development server: npm run dev

BACKEND SETUP
-------------
1. Navigate to backend/
2. Create virtual environment
   - python -m venv venv
   - source venv/bin/activate
3. Install dependencies
   - pip install -r requirements/base.txt
4. Run migrations
   - python manage.py migrate
5. Start server
   - python manage.py runserver

KEY TECHNOLOGIES
----------------
- Frontend: Next.js 15, React 19, Tailwind
- Backend: Django 5.x, Django REST Framework
- Authentication: Firebase
- Deployment: Azure, GitHub Actions

DEPLOYMENT
----------
- Frontend: Azure Web Apps
- Backend: Azure App Service
- CI/CD: GitHub Actions

FEATURES
---------
- User Authentication
- Responsive Design
- Protected Routes
- Error Handling



