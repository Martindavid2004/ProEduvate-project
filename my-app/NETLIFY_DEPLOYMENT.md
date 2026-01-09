# Netlify Deployment Guide for ProeduVate Frontend

## Prerequisites

1. A [Netlify account](https://app.netlify.com/signup) (free)
2. Your backend hosted on Render: `https://proeduvate-project.onrender.com`
3. Git repository (GitHub, GitLab, or Bitbucket)

## Option 1: Deploy via Netlify Dashboard (Recommended)

### Step 1: Prepare Your Repository

1. Make sure all changes are committed to Git:
```bash
cd my-app
git add .
git commit -m "Prepare for Netlify deployment"
git push origin main
```

### Step 2: Connect to Netlify

1. Go to [Netlify](https://app.netlify.com/)
2. Click **"Add new site"** → **"Import an existing project"**
3. Choose your Git provider (GitHub/GitLab/Bitbucket)
4. Authorize Netlify to access your repositories
5. Select your ProeduVate repository

### Step 3: Configure Build Settings

Configure the following settings:

- **Base directory**: `my-app`
- **Build command**: `npm run build`
- **Publish directory**: `my-app/build`
- **Node version**: `18`

### Step 4: Add Environment Variables

In the Netlify dashboard, go to:
**Site settings** → **Environment variables** → **Add a variable**

Add this variable:
```
Key: REACT_APP_API_URL
Value: https://proeduvate-project.onrender.com/api
```

### Step 5: Deploy

1. Click **"Deploy site"**
2. Wait for the build to complete (2-5 minutes)
3. Your site will be live at a Netlify URL like: `https://your-site-name.netlify.app`

### Step 6: Custom Domain (Optional)

1. Go to **Site settings** → **Domain management**
2. Click **"Add custom domain"**
3. Follow the instructions to configure your DNS

---

## Option 2: Deploy via Netlify CLI

### Step 1: Install Netlify CLI

```bash
npm install -g netlify-cli
```

### Step 2: Login to Netlify

```bash
netlify login
```

### Step 3: Initialize Netlify

```bash
cd my-app
netlify init
```

Follow the prompts:
- Choose **"Create & configure a new site"**
- Select your team
- Enter a site name
- Build command: `npm run build`
- Publish directory: `build`

### Step 4: Set Environment Variables

```bash
netlify env:set REACT_APP_API_URL "https://proeduvate-project.onrender.com/api"
```

### Step 5: Deploy

```bash
# Deploy to production
netlify deploy --prod
```

---

## Option 3: Deploy via Drag & Drop (Quick Test)

### Step 1: Build Locally

```bash
cd my-app
npm install
npm run build
```

### Step 2: Deploy to Netlify

1. Go to [Netlify Drop](https://app.netlify.com/drop)
2. Drag and drop the `my-app/build` folder
3. Your site will be deployed instantly

**Note**: Environment variables must be set in Netlify dashboard after deployment.

---

## Backend CORS Configuration

Make sure your Render backend allows requests from your Netlify domain.

### Update Backend CORS Settings

In `ProeduVate-main/backend/app/__init__.py`, ensure CORS is configured:

```python
from flask_cors import CORS

# Allow your Netlify domain
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "https://your-site-name.netlify.app",  # Add your Netlify URL
            "https://*.netlify.app"  # Allow all Netlify preview deployments
        ],
        "supports_credentials": True
    }
})
```

Redeploy your backend after making this change.

---

## Verify Deployment

### Test Your Deployed Site

1. Open your Netlify URL
2. Try to register a new student
3. Login with credentials
4. Test the chatbot
5. Upload a resume
6. Submit an assignment

### Check Console for Errors

Open browser DevTools (F12) → Console tab and verify:
- No CORS errors
- API calls are going to your Render backend
- No 404 or 500 errors

### Check Network Tab

In DevTools → Network tab:
- Filter by "Fetch/XHR"
- Verify API requests are going to `https://proeduvate-project.onrender.com/api`

---

## Troubleshooting

### Issue: "Failed to fetch" or CORS errors

**Solution**: Update backend CORS to include your Netlify domain

### Issue: API calls going to wrong URL

**Solution**: 
1. Check environment variables in Netlify dashboard
2. Rebuild and redeploy: `netlify deploy --prod`

### Issue: 404 on page refresh

**Solution**: Already configured in `netlify.toml` with redirect rules

### Issue: Environment variables not working

**Solution**:
1. Environment variables must start with `REACT_APP_`
2. Rebuild after adding/changing environment variables
3. Clear cache: **Site settings** → **Build & deploy** → **Clear cache and deploy**

---

## Continuous Deployment

Once connected to Git, Netlify will automatically:
- Build and deploy on every push to main branch
- Create preview deployments for pull requests
- Roll back to previous versions if needed

---

## Netlify Features to Explore

- **Branch deploys**: Test different branches
- **Deploy previews**: Preview PRs before merging
- **Split testing**: A/B test different versions
- **Functions**: Add serverless functions
- **Forms**: Handle form submissions
- **Analytics**: Track site performance

---

## Cost

- Free tier includes:
  - 100 GB bandwidth/month
  - 300 build minutes/month
  - Unlimited sites
  - HTTPS included
  - Custom domains

---

## Next Steps

1. ✅ Deploy frontend to Netlify
2. ✅ Configure environment variables
3. ✅ Update backend CORS settings
4. ✅ Test all features
5. 🔜 Add custom domain (optional)
6. 🔜 Enable form notifications (optional)
7. 🔜 Set up monitoring and analytics

---

## Important URLs

- **Netlify Dashboard**: https://app.netlify.com/
- **Your Backend**: https://proeduvate-project.onrender.com
- **Your Frontend**: https://your-site-name.netlify.app (after deployment)

---

## Support

- [Netlify Documentation](https://docs.netlify.com/)
- [Netlify Community](https://answers.netlify.com/)
- [Netlify Status](https://www.netlifystatus.com/)
