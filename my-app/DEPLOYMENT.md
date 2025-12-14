# ProEduvate - Deployment Guide

This guide covers deploying your ProEduvate React application to production.

## 📋 Pre-Deployment Checklist

- [ ] Backend API is fully functional
- [ ] All environment variables are configured
- [ ] Database is set up and accessible
- [ ] SSL certificate obtained (for HTTPS)
- [ ] Domain name configured
- [ ] Backend CORS settings allow production URL
- [ ] All dependencies are up to date
- [ ] Application tested in production mode locally

## 🏗️ Build Process

### 1. Create Production Build

```bash
cd my-app
npm run build
```

This creates an optimized production build in the `build/` folder with:
- Minified JavaScript
- Optimized CSS
- Compressed assets
- Source maps (optional)

### 2. Test Production Build Locally

```bash
# Install serve globally
npm install -g serve

# Serve the build folder
serve -s build -p 3000
```

Visit `http://localhost:3000` to test the production build.

## 🚀 Deployment Options

### Option 1: Traditional Server (Nginx + Flask)

#### A. Backend Setup (Flask)

1. **Install Python and dependencies on server:**
```bash
cd /var/www/proeduvate/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Install Gunicorn (WSGI Server):**
```bash
pip install gunicorn
```

3. **Create systemd service for Flask:**
```bash
sudo nano /etc/systemd/system/proeduvate-api.service
```

Add:
```ini
[Unit]
Description=ProEduvate Flask API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/proeduvate/backend
Environment="PATH=/var/www/proeduvate/backend/venv/bin"
ExecStart=/var/www/proeduvate/backend/venv/bin/gunicorn -w 4 -b 127.0.0.1:5001 run:app

[Install]
WantedBy=multi-user.target
```

4. **Start the service:**
```bash
sudo systemctl start proeduvate-api
sudo systemctl enable proeduvate-api
```

#### B. Frontend Setup (React)

1. **Copy build files to server:**
```bash
scp -r build/* user@yourserver:/var/www/proeduvate/frontend/
```

2. **Configure Nginx:**
```bash
sudo nano /etc/nginx/sites-available/proeduvate
```

Add:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # React app
    root /var/www/proeduvate/frontend;
    index index.html;
    
    # React Router support
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy to Flask
    location /api {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Login endpoint
    location /login {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Enable site and restart Nginx:**
```bash
sudo ln -s /etc/nginx/sites-available/proeduvate /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

4. **Set up SSL with Let's Encrypt:**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Option 2: Vercel (Frontend Only)

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Deploy:**
```bash
cd my-app
vercel
```

3. **Configure environment variables in Vercel dashboard:**
- Add `REACT_APP_API_URL` pointing to your backend

4. **Set up `vercel.json`:**
```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-backend-api.com/api/$1" },
    { "source": "/(.*)", "destination": "/" }
  ]
}
```

### Option 3: Heroku

#### A. Backend (Flask)

1. **Create `Procfile`:**
```
web: gunicorn run:app
```

2. **Create `runtime.txt`:**
```
python-3.11.0
```

3. **Deploy:**
```bash
cd backend
heroku create proeduvate-api
git push heroku main
```

#### B. Frontend (React)

1. **Create `static.json`:**
```json
{
  "root": "build/",
  "routes": {
    "/**": "index.html"
  },
  "proxies": {
    "/api/": {
      "origin": "https://proeduvate-api.herokuapp.com"
    }
  }
}
```

2. **Add buildpack:**
```bash
heroku buildpacks:set mars/create-react-app
```

3. **Deploy:**
```bash
cd my-app
heroku create proeduvate-app
git push heroku main
```

### Option 4: Docker

#### A. Create Dockerfile for Backend

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "run:app"]
```

#### B. Create Dockerfile for Frontend

```dockerfile
# my-app/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### C. Create docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5001:5001"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./backend/uploads:/app/uploads

  frontend:
    build: ./my-app
    ports:
      - "80:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:5001/api
```

#### D. Deploy

```bash
docker-compose up -d
```

## 🔒 Security Considerations

### 1. Environment Variables

Create `.env` file (never commit to git):
```env
# Backend
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/proeduvate

# Frontend (must start with REACT_APP_)
REACT_APP_API_URL=https://api.yourdomain.com
```

### 2. Update API Configuration

In `src/services/api.js`, update for production:
```javascript
const getApiUrl = () => {
  // Use environment variable if available
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  const protocol = window.location.protocol;
  const host = window.location.host;
  
  if (host.includes('devtunnels.ms') || host.includes('ngrok')) {
    return `${protocol}//${host}/api`;
  }
  
  // Production API URL
  return 'https://api.yourdomain.com/api';
};
```

### 3. Enable CORS on Backend

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://yourdomain.com'], supports_credentials=True)
```

### 4. Secure Cookies

```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

### 5. Content Security Policy

Add to your index.html:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; 
               style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com;">
```

## 📊 Performance Optimization

### 1. Enable Gzip Compression (Nginx)

```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/css text/javascript application/javascript application/json;
```

### 2. Add Caching Headers

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. Enable HTTP/2

```nginx
listen 443 ssl http2;
```

### 4. Lazy Load Images

Update components to use lazy loading:
```javascript
<img src="logo.png" loading="lazy" alt="Logo" />
```

## 🔍 Monitoring

### 1. Set Up Error Logging

Install Sentry:
```bash
npm install @sentry/react
```

Configure in `src/index.js`:
```javascript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: "production"
});
```

### 2. Add Analytics

Add Google Analytics to `public/index.html`:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
```

### 3. Monitor API Performance

Use tools like:
- New Relic
- Datadog
- Application Insights

## 🧪 Testing in Production

### 1. Smoke Tests

```bash
# Test homepage
curl https://yourdomain.com

# Test API
curl https://api.yourdomain.com/api/admin/users

# Test SSL
openssl s_client -connect yourdomain.com:443
```

### 2. Load Testing

Use tools like:
- Apache JMeter
- k6
- Artillery

Example with k6:
```javascript
// load-test.js
import http from 'k6/http';

export default function() {
  http.get('https://yourdomain.com');
}
```

Run:
```bash
k6 run --vus 10 --duration 30s load-test.js
```

## 🔄 CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        cd my-app
        npm install
    
    - name: Build
      run: |
        cd my-app
        npm run build
    
    - name: Deploy to server
      uses: easingthemes/ssh-deploy@v2
      env:
        SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
        SOURCE: "my-app/build/"
        REMOTE_HOST: ${{ secrets.REMOTE_HOST }}
        REMOTE_USER: ${{ secrets.REMOTE_USER }}
        TARGET: "/var/www/proeduvate/frontend"
```

## 📱 PWA Support (Optional)

### 1. Create `manifest.json`

```json
{
  "short_name": "ProEduvate",
  "name": "ProEduvate LMS",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}
```

### 2. Register Service Worker

In `src/index.js`:
```javascript
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

serviceWorkerRegistration.register();
```

## 🐛 Troubleshooting

### Issue: 404 on refresh

**Solution**: Ensure server rewrites all routes to index.html

### Issue: API calls fail

**Solution**: Check CORS settings and API URL configuration

### Issue: White screen

**Solution**: Check browser console, verify build completed successfully

### Issue: Slow load times

**Solution**: Enable gzip, optimize images, implement code splitting

## 📚 Post-Deployment

### 1. Set Up Backup

```bash
# Backup database daily
0 2 * * * pg_dump proeduvate > /backups/proeduvate_$(date +\%Y\%m\%d).sql
```

### 2. Monitor Logs

```bash
# Watch Nginx logs
tail -f /var/log/nginx/access.log

# Watch application logs
journalctl -u proeduvate-api -f
```

### 3. Update DNS

Point your domain to the server IP:
```
A Record: @ -> your.server.ip
A Record: www -> your.server.ip
```

## ✅ Deployment Checklist

- [ ] Production build created and tested
- [ ] Backend deployed and running
- [ ] Frontend deployed and accessible
- [ ] SSL certificate installed
- [ ] DNS configured
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Database backed up
- [ ] Monitoring configured
- [ ] Error tracking enabled
- [ ] Performance optimized
- [ ] Security headers added
- [ ] CI/CD pipeline set up (optional)
- [ ] Load tested
- [ ] Documentation updated

---

**Congratulations!** Your ProEduvate application is now live! 🎉
