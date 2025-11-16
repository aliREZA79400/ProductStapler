# Quick Start Guide

## Starting the Application

### 1. Make sure the backend is running

The backend should be running on `http://localhost:8000`

```bash
cd ../backend
# Start your FastAPI backend here
uvicorn main:app --reload
```

### 2. Start the frontend development server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## First Time Setup

1. Open your browser to `http://localhost:5173`
2. Click "Register" to create a new account
3. Enter a username (min 3 characters) and password (min 6 characters)
4. You'll be automatically logged in and redirected to the home page

## Using the Application

### Browse Products by Category

1. **Home Page** - View Level 1 categories with sample products
   - Adjust sample size using the dropdown (1, 3, 5, or 10)
   - Click "View Subcategories →" to drill down

2. **Level 2 Page** - View subcategories within a Level 1 category
   - Navigate deeper by clicking "View Sub-subcategories →"
   - Use the "← Back" button to return

3. **Level 3 Page** - View the deepest level of categorization
   - See all products in the sub-subcategory

4. **Product Detail** - Click "View Details →" on any product card
   - See complete product information

### Navigation

- Use the navbar "Kaseb" logo to return home
- "← Back" buttons navigate to the previous page
- "Logout" button in the navbar to sign out

## API Proxy

The frontend uses Vite's proxy to forward API calls:
- Frontend requests to `/api/*` → Backend at `http://localhost:8000/*`

This avoids CORS issues during development.

## Troubleshooting

### Backend Connection Issues

If you see "Failed to load products":
1. Verify the backend is running: `curl http://localhost:8000`
2. Check the browser console for detailed errors
3. Ensure MongoDB is running and accessible

### Authentication Issues

If you're logged out unexpectedly:
1. Check that the backend JWT configuration matches
2. Verify the token in localStorage (Browser DevTools → Application → Local Storage)
3. Try logging in again

### Build Issues

If npm install fails:
1. Clear npm cache: `npm cache clean --force`
2. Delete node_modules: `rm -rf node_modules`
3. Reinstall: `npm install`
