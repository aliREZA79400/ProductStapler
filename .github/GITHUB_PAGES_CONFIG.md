# GitHub Pages Configuration Reference

## Files Overview

### 1. GitHub Actions Workflow
**File**: `.github/workflows/deploy.yml`

Automatically deploys to GitHub Pages on every push to main branch.

**What it does**:
- Installs Node.js 20
- Builds React app with Vite
- Uploads build to GitHub Pages
- Deploys automatically

**Trigger**: Any push to `main` branch

### 2. Vite Configuration
**File**: `frontend/vite.config.js`

Updated to support GitHub Pages base URL.

**Key settings**:
```javascript
base: process.env.VITE_BASE_URL || '/',
```

This ensures your site works at any URL path, including `https://user.github.io/repo-name/`

### 3. Package Configuration
**File**: `frontend/package.json`

Build scripts for deployment:

```json
{
  "scripts": {
    "dev": "vite",           // Development server
    "build": "vite build",   // Production build
    "preview": "vite preview" // Preview build locally
  }
}
```

## Environment Variables

### GitHub Actions Workflow

**File**: `.github/workflows/deploy.yml`

```yaml
env:
  VITE_API_URL: https://your-backend-api.com  # Change this!
```

### Local Development

**File**: `frontend/.env` (create if needed)

```env
VITE_API_URL=http://localhost:8000
VITE_BASE_URL=/KASEB/
```

## Deployment Process

### Step 1: GitHub Pages Settings

**Location**: Repository → Settings → Pages

```
Build and deployment
├── Source: GitHub Actions ✓
└── Branch: main ✓
```

### Step 2: Repository Structure

```
KASEB/
├── .github/
│   └── workflows/
│       └── deploy.yml         # <-- Workflow file
├── frontend/
│   ├── src/
│   ├── dist/                  # <-- Gets deployed
│   ├── vite.config.js         # <-- Updated
│   └── package.json
└── README.md
```

### Step 3: Deployment Flow

```
1. git push origin main
        ↓
2. GitHub detects push
        ↓
3. Workflow triggers (.github/workflows/deploy.yml)
        ↓
4. npm install & npm run build
        ↓
5. Upload dist/ to GitHub Pages
        ↓
6. Site live at https://user.github.io/KASEB
```

## Configuration Examples

### Example 1: Local Backend

**GitHub Actions Workflow**:
```yaml
env:
  VITE_API_URL: http://localhost:8000
```

**When to use**: Testing locally, development

### Example 2: Deployed Backend

**GitHub Actions Workflow**:
```yaml
env:
  VITE_API_URL: https://api.yourdomain.com
```

**When to use**: Production deployment

### Example 3: Relative URLs

**GitHub Actions Workflow**:
```yaml
env:
  VITE_API_URL: /api
```

**When to use**: Same server hosts both frontend and backend

## Build Configuration

### Vite Config (frontend/vite.config.js)

```javascript
export default defineConfig({
  base: process.env.VITE_BASE_URL || '/',  // <-- Supports GitHub Pages path
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

### Build Output

**Output directory**: `frontend/dist/`

**Contents**:
- `index.html` - Main entry point
- `assets/` - JavaScript, CSS bundles
- All static assets (images, fonts)

## Monitoring & Debugging

### Check Build Status

1. Go to: `https://github.com/aliREZA79400/KASEB/actions`
2. Click latest workflow run
3. View "Build" and "Deploy" logs

### Common Issues

| Issue | Solution |
|-------|----------|
| 404 errors | Check base URL configuration |
| API calls fail | Update VITE_API_URL in workflow |
| Pages not updating | Wait 2 mins, hard refresh (Ctrl+Shift+R) |
| Build fails | Check Actions logs for error details |

## Performance Optimization

### Build Size

**Current setup**:
- React 18 (optimized)
- Tailwind CSS (tree-shaking)
- Vite (fast builds)
- Result: ~200KB gzipped

### Deployment Speed

- **Build time**: ~30 seconds
- **Deploy time**: ~10 seconds
- **Total**: ~40 seconds from push to live

### Caching

GitHub Pages automatically:
- Caches builds
- Uses CDN for fast delivery
- Enables browser caching

## Security

### What's Protected

- ✅ HTTPS automatic (GitHub Pages)
- ✅ No API keys in code
- ✅ Environment variables for secrets
- ✅ Branch protection (recommended)

### What You Should Do

1. Never commit `.env` files
2. Use GitHub Secrets for sensitive data
3. Keep dependencies updated
4. Review GitHub Actions logs

## Rollback

If deployment goes wrong:

```bash
# Revert to previous version
git revert HEAD
git push origin main

# Workflow will rebuild with previous version
```

Or manually in GitHub Actions:

1. Go to Actions tab
2. Find the good deployment
3. Re-run it
4. Site will rollback to that version

## Manual Deployment (Alternative)

If automated workflow fails:

```bash
# Build locally
cd frontend
npm run build

# The dist/ folder is what gets deployed
# Commit and push
git add frontend/dist
git commit -m "Manual deployment"
git push origin main

# Trigger workflow again
```

## Advanced: Custom Domain

### Setup Custom Domain

1. Update DNS with registrar:
   - `A` record: `185.199.108.153` (GitHub Pages IP)
   - Or `CNAME` record: `user.github.io`

2. Add domain in GitHub:
   - Settings → Pages → Custom domain
   - Enter domain
   - GitHub verifies DNS
   - HTTPS cert issued automatically

### Configuration Files

If using custom domain, GitHub creates:
- `CNAME` file in branch
- SSL cert (automatic)
- Redirects properly configured

## Useful Commands

```bash
# Build locally to test
npm run build -w frontend

# Preview build
npm run preview -w frontend

# Check if build succeeds
npm run build -w frontend 2>&1 | tail -20

# View deployed files (after push)
# No command needed - check GitHub Actions status

# Check site status
curl -I https://aliREZA79400.github.io/KASEB
```

## GitHub Actions Secrets (Advanced)

For sensitive variables:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add secret (e.g., `API_KEY`)
4. Use in workflow:

```yaml
env:
  API_KEY: ${{ secrets.API_KEY }}
```

## Workflow Triggers

Currently configured to trigger on:

```yaml
on:
  push:
    branches:
      - main
```

Can be modified to also trigger on:
- Pull requests
- Scheduled times (cron)
- Manual trigger
- Other branches

## Additional Resources

- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)
- [React Deployment](https://react.dev/learn/deployment)

## Quick Reference

| Item | Value |
|------|-------|
| **Site URL** | `https://aliREZA79400.github.io/KASEB` |
| **Build tool** | Vite |
| **Framework** | React 18 |
| **Trigger** | Push to main |
| **Build time** | ~30 seconds |
| **Deploy time** | ~10 seconds |
| **Hosting** | GitHub Pages (free) |
| **HTTPS** | Automatic |
| **Custom domain** | Supported |

---

**Last Updated**: December 4, 2025
