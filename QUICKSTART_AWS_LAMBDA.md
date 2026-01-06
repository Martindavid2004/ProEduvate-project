# Quick Start Guide - AWS Lambda Python Code Execution

## ⚡ Quick Setup (5 Minutes)

### 1. Install Dependencies
```bash
cd ProeduVate-main/backend
pip install boto3
```

### 2. Create AWS Lambda Function

**Go to AWS Console:**
1. Visit: https://console.aws.amazon.com/lambda/
2. Click "Create function"
3. Function name: `python-code-executor`
4. Runtime: Python 3.11
5. Click "Create function"

**Add this code to Lambda:**
```python
import json, sys, io, traceback
from contextlib import redirect_stdout, redirect_stderr

def lambda_handler(event, context):
    try:
        source_code = event.get('source_code', '')
        stdin_input = event.get('stdin', '')
        
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        if stdin_input:
            sys.stdin = io.StringIO(stdin_input)
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(source_code, {
                '__builtins__': {
                    'print': print, 'len': len, 'range': range,
                    'int': int, 'float': float, 'str': str,
                    'list': list, 'dict': dict, 'tuple': tuple,
                    'set': set, 'bool': bool, 'sum': sum,
                    'min': min, 'max': max, 'abs': abs,
                    'round': round, 'sorted': sorted,
                    'enumerate': enumerate, 'zip': zip,
                    'map': map, 'filter': filter, 'input': input,
                    'isinstance': isinstance, 'type': type,
                }
            })
        
        return {
            'stdout': stdout_buffer.getvalue(),
            'stderr': stderr_buffer.getvalue() or None,
            'status': {'id': 3, 'description': 'Accepted'},
            'time': '0.0',
            'memory': 0
        }
    except Exception as e:
        return {
            'stdout': stdout_buffer.getvalue() if 'stdout_buffer' in locals() else '',
            'stderr': traceback.format_exc(),
            'status': {'id': 11, 'description': 'Runtime Error'},
            'time': None,
            'memory': None
        }
    finally:
        sys.stdin = sys.__stdin__
```

**Set Timeout:** Configuration → Edit → Timeout: 10 seconds

### 3. Get AWS Credentials

**Option A - Create IAM User (Recommended):**
1. Go to: https://console.aws.amazon.com/iam/
2. Users → Add users
3. User name: `proedu-lambda-executor`
4. Attach policy: Create custom policy with:
```json
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["lambda:InvokeFunction"],
        "Resource": "arn:aws:lambda:*:*:function:python-code-executor"
    }]
}
```
5. Create user → Security credentials → Create access key
6. Copy Access Key ID and Secret Access Key

**Option B - Use Root Credentials (Not Recommended for Production):**
1. Go to: AWS Console → Security Credentials
2. Create Access Key

### 4. Configure Backend

Create `.env` file in `ProeduVate-main/backend/`:
```env
# MongoDB
MONGO_URI=mongodb://localhost:27017/
DATABASE_NAME=proedu_db

# Google AI (for chatbot)
GOOGLE_API_KEY=your_google_api_key

# AWS Lambda (REQUIRED)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_LAMBDA_FUNCTION_NAME=python-code-executor

FLASK_ENV=development
UPLOAD_FOLDER=uploads
```

Replace with your actual AWS credentials!

### 5. Start Application

```bash
# Terminal 1 - Backend
cd ProeduVate-main/backend
python run.py

# Terminal 2 - Frontend
cd my-app
npm start
```

## 🧪 Test It Works

1. Open browser: http://localhost:3000
2. Login as student
3. Navigate to "Programming and Coding"
4. Click "Python Programming"
5. Try running this code:
```python
print("Hello from AWS Lambda!")
```

You should see the output!

## ❓ Troubleshooting

### Error: "AWS credentials not found"
**Fix:** Check your `.env` file has correct AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

### Error: "Unable to invoke Lambda"
**Fix:** 
1. Verify function name is `python-code-executor`
2. Check IAM permissions
3. Ensure region matches (default: us-east-1)

### Error: "Module 'boto3' not found"
**Fix:** 
```bash
pip install boto3
```

### No Output / Blank Response
**Fix:**
1. Check Lambda CloudWatch logs
2. Verify Lambda function code is correct
3. Test Lambda directly in AWS Console

## 📊 What Changed?

### ✅ Added
- AWS Lambda integration for code execution
- Python-only training (C removed)
- Serverless scalability

### ❌ Removed
- Judge0 Docker setup
- C programming support
- Local code execution with subprocess

### 🎯 Benefits
- No Docker needed
- Faster execution
- Better security
- Auto-scaling
- Free tier: 1M requests/month

## 📚 More Information

- Full Setup Guide: `AWS_LAMBDA_SETUP.md`
- Migration Details: `MIGRATION_SUMMARY.md`

## 💡 Tips

1. **Free Tier**: Lambda is free for 1M requests/month
2. **Testing**: Test Lambda function directly in AWS Console first
3. **Logs**: Check CloudWatch Logs if issues occur
4. **Security**: Never commit .env file with real credentials
5. **Region**: Use the closest AWS region for better performance

## 🚀 You're Ready!

Your application now uses AWS Lambda for Python code execution. Students can practice Python programming with automatic code evaluation!

---

Need help? Check the full documentation in `AWS_LAMBDA_SETUP.md`
