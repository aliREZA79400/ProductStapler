#!/bin/bash

# GitHub Pages Setup Script for Mangane Project
# This script helps configure your project for GitHub Pages deployment

set -e

echo "🚀 Starting GitHub Pages Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo -e "${YELLOW}⚠️  Please run this script from the project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📋 GitHub Pages Setup Configuration${NC}"
echo "This will configure your project for GitHub Pages deployment"
echo ""

# Get GitHub username
read -p "Enter your GitHub username (default: aliREZA79400): " github_user
github_user=${github_user:-aliREZA79400}

# Get repository name
read -p "Enter your repository name (default: ProductStapler): " repo_name
repo_name=${repo_name:-ProductStapler}

# Get backend API URL
echo ""
echo -e "${BLUE}Backend API Configuration${NC}"
echo "Enter your backend API URL for deployment"
echo "Examples:"
echo "  - Local: http://localhost:8000"
echo "  - Deployed: https://api.yourdomain.com"
echo "  - Leave blank to use relative URLs"
read -p "Backend API URL (optional): " api_url

# Create GitHub Pages configuration
echo ""
echo -e "${GREEN}✅ Creating configuration files...${NC}"

# Update .github/workflows/deploy.yml with user input
WORKFLOW_FILE=".github/workflows/deploy.yml"
if [ -f "$WORKFLOW_FILE" ]; then
    if [ -n "$api_url" ]; then
        sed -i.bak "s|VITE_API_URL: .*|VITE_API_URL: $api_url|g" "$WORKFLOW_FILE"
        rm -f "$WORKFLOW_FILE.bak"
        echo "✓ Updated workflow with API URL: $api_url"
    fi
fi

# Create .github/settings.json for documentation
mkdir -p .github
cat > ".github/GITHUB_PAGES_CONFIG.json" << EOF
{
  "github_username": "$github_user",
  "repository_name": "$repo_name",
  "github_pages_url": "https://$github_user.github.io/$repo_name",
  "deployment_type": "GitHub Actions",
  "branch": "main",
  "backend_api_url": "${api_url:-relative}",
  "configured_at": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
}
EOF

echo ""
echo -e "${GREEN}✅ Configuration Complete!${NC}"
echo ""
echo -e "${BLUE}📝 Next Steps:${NC}"
echo ""
echo "1. Push your changes to GitHub:"
echo "   git add .github/"
echo "   git commit -m 'Configure GitHub Pages deployment'"
echo "   git push origin main"
echo ""
echo "2. Enable GitHub Pages:"
echo "   - Go to: https://github.com/$github_user/$repo_name/settings/pages"
echo "   - Source: Select 'GitHub Actions'"
echo "   - Save"
echo ""
echo "3. View your deployment:"
echo "   - Actions: https://github.com/$github_user/$repo_name/actions"
echo "   - Your site: https://$github_user.github.io/$repo_name"
echo ""
echo -e "${GREEN}🎉 Setup complete! Your site will be live in a few minutes.${NC}"
echo ""
echo -e "${BLUE}ℹ️  Configuration Summary:${NC}"
echo "  GitHub User: $github_user"
echo "  Repository: $repo_name"
echo "  GitHub Pages URL: https://$github_user.github.io/$repo_name"
if [ -n "$api_url" ]; then
    echo "  Backend API: $api_url"
fi
echo ""
