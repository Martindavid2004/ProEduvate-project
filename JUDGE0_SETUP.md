# Judge0 Setup Guide

## The Issue
The coding interface is showing "No output" because Judge0 returns an Internal Error (status id 13) with the message: "No such file or directory @ rb_sysopen - /box/script.py"

This means Judge0 is not properly configured with Docker volumes.

## Solution: Set up Judge0 with Docker

### Option 1: Using Docker Compose (Recommended)

1. **Create a docker-compose.yml file** in your project root:

```yaml
version: '3.7'

services:
  judge0-server:
    image: judge0/judge0:1.13.1
    volumes:
      - ./judge0/tmp:/tmp
    ports:
      - "2358:2358"
    privileged: true
    environment:
      - REDIS_HOST=judge0-redis
      - REDIS_PORT=6379
      - POSTGRES_HOST=judge0-db
      - POSTGRES_DB=judge0
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=YourPassword123
    depends_on:
      - judge0-db
      - judge0-redis
    restart: unless-stopped

  judge0-db:
    image: postgres:13
    environment:
      - POSTGRES_DB=judge0
      - POSTGRES_USER=judge0
      - POSTGRES_PASSWORD=YourPassword123
    volumes:
      - judge0-db-data:/var/lib/postgresql/data
    restart: unless-stopped

  judge0-redis:
    image: redis:6
    command: redis-server --appendonly yes
    volumes:
      - judge0-redis-data:/data
    restart: unless-stopped

volumes:
  judge0-db-data:
  judge0-redis-data:
```

2. **Run Docker Compose:**
```bash
docker-compose up -d
```

3. **Verify it's working:**
```bash
curl http://localhost:2358/about
```

### Option 2: Using Official Judge0 Quick Start

1. **Download the official docker-compose.yml:**
```bash
cd ProeduVate-main/backend/judge0/judge0-v1.13.1
wget https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip
unzip judge0-v1.13.1.zip
```

2. **Start Judge0:**
```bash
docker-compose up -d
```

### Option 3: Use Judge0 CE (Community Edition) - Easiest

```bash
# Clone Judge0 CE
git clone https://github.com/judge0/judge0.git
cd judge0

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

## Testing Judge0

After setup, test with this command:

```bash
# PowerShell
$code = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes("print('Hello, World!')"))
$body = @{
    source_code = $code
    language_id = 71
    stdin = ""
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:2358/submissions?base64_encoded=true&wait=true" -Method POST -Body $body -ContentType "application/json"
```

Expected output should have `status.id = 3` and `stdout` should contain the base64-encoded output.

## Alternative: Use Judge0 RapidAPI

If you don't want to run Judge0 locally, you can use the hosted version:

1. Sign up at https://rapidapi.com/judge0-official/api/judge0-ce
2. Get your API key
3. Update the CodingInterface.js to use:
   - URL: `https://judge0-ce.p.rapidapi.com/submissions`
   - Add header: `X-RapidAPI-Key: YOUR_KEY`
   - Add header: `X-RapidAPI-Host: judge0-ce.p.rapidapi.com`

## Troubleshooting

### Error: "No such file or directory"
- Judge0 needs proper Docker volume mounts
- Make sure Docker Desktop is running
- Try: `docker-compose down -v` then `docker-compose up -d`

### Port 2358 already in use
- Check: `netstat -ano | findstr :2358`
- Kill the process or change the port in docker-compose.yml

### Status ID meanings:
- 1: In Queue
- 2: Processing
- 3: Accepted (Success)
- 4: Wrong Answer
- 5: Time Limit Exceeded
- 6: Compilation Error
- 11: Runtime Error (SIGSEGV)
- 12: Runtime Error (SIGXFSZ)
- 13: Internal Error (Configuration issue)
