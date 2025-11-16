# Kaseb Frontend

React frontend application for the Kaseb product categorization system.

## Features

- **Authentication**: User registration and login with JWT tokens
- **Hierarchical Product Browsing**: Navigate through Level 1, Level 2, and Level 3 product categories
- **Product Details**: View detailed information about individual products
- **Responsive Design**: Built with Tailwind CSS for a modern, responsive UI
- **Protected Routes**: Secure pages that require authentication

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **React Router 6** - Client-side routing
- **Axios** - HTTP client
- **Tailwind CSS** - Utility-first CSS framework

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist` directory.

## Project Structure

```
src/
├── components/          # React components
│   ├── Home.jsx        # Level 1 categories
│   ├── Level2.jsx      # Level 2 subcategories
│   ├── Level3.jsx      # Level 3 sub-subcategories
│   ├── ProductDetail.jsx
│   ├── ProductCard.jsx
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Navbar.jsx
│   └── ProtectedRoute.jsx
├── context/            # React context providers
│   └── AuthContext.jsx
├── services/           # API services
│   └── api.js
├── App.jsx            # Main app component
├── main.jsx           # Entry point
└── index.css          # Global styles

```

## API Endpoints

The frontend connects to the following backend endpoints:

### Authentication
- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Products
- `GET /` - Get Level 1 categories with sample products
- `GET /sub/{level1_id}` - Get Level 2 subcategories
- `GET /sub/{level1_id}/sub-sub/{level2_id}` - Get Level 3 sub-subcategories
- `GET /product/{product_id}` - Get individual product details

## Environment Configuration

The Vite proxy is configured to forward `/api` requests to `http://localhost:8000`.
To change the backend URL, edit `vite.config.js`.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
