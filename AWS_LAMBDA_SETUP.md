# AWS Lambda Setup Guide for Python Code Execution

This guide explains how to set up AWS Lambda for executing Python code in the ProeduVate application.

## Overview

The application now uses AWS Lambda instead of Judge0 for executing Python code submissions. This provides a scalable, secure, and serverless solution for code execution.

## Prerequisites

1. **AWS Account**: You need an active AWS account
2. **AWS CLI**: Install and configure AWS CLI (optional but recommended)
3. **IAM Permissions**: Permissions to create and invoke Lambda functions

## Setup Steps

### 1. Create AWS Lambda Function

#### Option A: Using AWS Console

1. Go to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
2. Click "Create function"
3. Choose "Author from scratch"
4. Configure:
   - **Function name**: `python-code-executor`
   - **Runtime**: Python 3.11 or Python 3.12
   - **Architecture**: x86_64
5. Click "Create function"

#### Option B: Using AWS CLI

```bash
aws lambda create-function \
  --function-name python-code-executor \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
```

### 2. Lambda Function Code

Create a Lambda function with the following code:

```python
import json
import sys
import io
import traceback
from contextlib import redirect_stdout, redirect_stderr

def lambda_handler(event, context):
    """
    Execute Python code safely in Lambda environment
    """
    try:
        # Get parameters from event
        source_code = event.get('source_code', '')
        stdin_input = event.get('stdin', '')
        timeout = event.get('timeout', 5)
        
        # Create string buffers for stdout and stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        
        # Set up stdin if provided
        if stdin_input:
            sys.stdin = io.StringIO(stdin_input)
        
        # Redirect stdout and stderr
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # Create restricted globals (only safe built-in functions)
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'range': range,
                    'int': int,
                    'float': float,
                    'str': str,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'bool': bool,
                    'sum': sum,
                    'min': min,
                    'max': max,
                    'abs': abs,
                    'round': round,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'map': map,
                    'filter': filter,
                    'input': input,
                    'isinstance': isinstance,
                    'type': type,
                }
            }
            
            # Execute the code
            exec(source_code, restricted_globals)
        
        # Get output
        stdout_output = stdout_buffer.getvalue()
        stderr_output = stderr_buffer.getvalue()
        
        # Return success response
        return {
            'stdout': stdout_output,
            'stderr': stderr_output if stderr_output else None,
            'status': {'id': 3, 'description': 'Accepted'},
            'time': '0.0',
            'memory': 0
        }
        
    except Exception as e:
        # Capture error traceback
        error_traceback = traceback.format_exc()
        
        return {
            'stdout': stdout_buffer.getvalue() if 'stdout_buffer' in locals() else '',
            'stderr': error_traceback,
            'status': {'id': 11, 'description': 'Runtime Error'},
            'time': None,
            'memory': None
        }
    finally:
        # Reset stdin
        sys.stdin = sys.__stdin__
```

### 3. Configure Lambda Settings

1. **Timeout**: Set to 10 seconds (Configuration → General configuration → Edit)
2. **Memory**: 256 MB should be sufficient
3. **Environment Variables**: None required for basic setup

### 4. Set Up Backend Environment Variables

Create or update your `.env` file in the backend directory:

```env
# AWS Lambda Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_LAMBDA_FUNCTION_NAME=python-code-executor
```

### 5. Install Required Dependencies

In the backend directory, install the AWS SDK:

```bash
pip install boto3
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## AWS IAM Permissions

Your AWS credentials need the following IAM permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": "arn:aws:lambda:*:*:function:python-code-executor"
        }
    ]
}
```

## Testing the Setup

### 1. Test Lambda Function Directly

In AWS Console:
1. Go to your Lambda function
2. Click "Test"
3. Use this test event:

```json
{
  "source_code": "print('Hello from Lambda!')",
  "stdin": "",
  "timeout": 5
}
```

### 2. Test Through Backend API

```bash
curl -X POST http://localhost:5000/api/student/execute-code \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "cHJpbnQoIkhlbGxvLCBXb3JsZCEiKQ==",
    "stdin": "",
    "base64_encoded": true
  }'
```

## Fallback Option: Local Execution

If you don't want to set up AWS Lambda immediately, you can use local Python execution as a fallback. The backend will automatically fall back to local execution if AWS credentials are not configured.

To use local execution only:
1. Don't set AWS environment variables
2. The code will execute using the local Python interpreter

## Cost Considerations

AWS Lambda Free Tier includes:
- 1 million requests per month
- 400,000 GB-seconds of compute time per month

For a small educational platform, this should be more than sufficient and costs should remain within the free tier.

## Security Notes

1. **Restricted Execution**: The Lambda function uses restricted globals to prevent dangerous operations
2. **Timeout**: Set appropriate timeout limits to prevent infinite loops
3. **Resource Limits**: Lambda automatically limits memory and CPU usage
4. **No File System Access**: Code cannot access the Lambda file system
5. **Network Isolation**: Code execution is isolated from other users

## Troubleshooting

### Error: "Unable to import module 'lambda_function'"
- Check that your Lambda handler is set to `lambda_function.lambda_handler`
- Ensure the file is named `lambda_function.py`

### Error: "Task timed out"
- Increase Lambda timeout in Configuration
- Check for infinite loops in test code

### Error: "AWS credentials not found"
- Verify `.env` file exists and contains correct credentials
- Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY

### Error: "Unable to invoke Lambda function"
- Verify IAM permissions
- Check function name matches AWS_LAMBDA_FUNCTION_NAME
- Ensure Lambda function exists in the specified region

## Migration from Judge0

The previous Judge0 setup has been completely removed:
- ✓ Judge0 Docker containers removed
- ✓ Judge0 configuration files removed
- ✓ C programming support removed
- ✓ Backend routes updated to use AWS Lambda
- ✓ Frontend updated to only support Python

## Support

For issues or questions:
1. Check AWS Lambda logs in CloudWatch
2. Check backend logs for error messages
3. Verify environment variables are correctly set
4. Ensure boto3 is installed
