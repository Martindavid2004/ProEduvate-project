# Netlify Deployment Guide

## Prerequisites
- GitHub account connected to Netlify
- Repository: https://github.com/Martindavid2004/ProEduvate-project

## Deployment Steps

### Option 1: Deploy via Netlify Dashboard (Recommended)

1. **Go to Netlify**
   - Visit https://app.netlify.com/
   - Sign in with your GitHub account

2. **Import Project**
   - Click "Add new site" → "Import an existing project"
   - Choose "GitHub"
   - Select your repository: `Martindavid2004/ProEduvate-project`

3. **Configure Build Settings**
   ```
   Base directory: my-app
   Build command: npm run build
   Publish directory: my-app/build
   ```

4. **Environment Variables** (Optional)
   - Go to Site settings → Environment variables
   - Add if needed:
     ```
     REACT_APP_API_URL=https://proeduvate-project.onrender.com/api
     ```
   - Note: This is already configured in the code to use Render URL in production

5. **Deploy**
   - Click "Deploy site"
   - Netlify will build and deploy your frontend
   - You'll get a URL like: `https://your-site-name.netlify.app`

### Option 2: Deploy via Netlify CLI

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**
   ```bash
   netlify login
   ```

3. **Navigate to my-app folder**
   ```bash
   cd my-app
   ```

4. **Build the project**
   ```bash
   npm run build
   ```

5. **Deploy**
   ```bash
   netlify deploy --prod --dir=build
   ```

## Configuration Details

### Backend Integration
- The frontend is configured to use: `https://proeduvate-project.onrender.com`
- In development: Uses `http://127.0.0.1:5000/api`
- In production: Automatically uses Render backend URL

### Build Configuration
- Located in: `my-app/netlify.toml`
- Build command: `npm run build`
- Publish directory: `build`
- Redirects: All routes redirect to `/index.html` (for React Router)

### CORS Configuration
The backend must allow requests from your Netlify domain. Update your backend CORS settings if needed:

```python
# In your Flask backend
CORS(app, origins=[
    "http://localhost:3000",
    "https://your-netlify-site.netlify.app"
])
```

## Post-Deployment

1. **Test the Application**
   - Visit your Netlify URL
   - Test login functionality
   - Verify API calls work with Render backend

2. **Custom Domain** (Optional)
   - Go to Site settings → Domain management
   - Add custom domain
   - Follow DNS configuration instructions

3. **HTTPS**
   - Automatically enabled by Netlify
   - Free SSL certificate included

## Troubleshooting

### API Calls Failing
- Check browser console for CORS errors
- Verify Render backend is running
- Check backend CORS settings allow Netlify domain

### Build Failures
- Check Node version compatibility
- Review build logs in Netlify dashboard
- Ensure all dependencies are in package.json

### Routes Not Working
- Verify `netlify.toml` has proper redirects
- Check `_redirects` file if using one

## Continuous Deployment

Netlify automatically deploys when you push to the main branch:
1. Make changes locally
2. Commit and push to GitHub
3. Netlify detects changes and rebuilds automatically
4. New version is live in 2-3 minutes

## Support

- Netlify Documentation: https://docs.netlify.com/
- Netlify Community: https://answers.netlify.com/
