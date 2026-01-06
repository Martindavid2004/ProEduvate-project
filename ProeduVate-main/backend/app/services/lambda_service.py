"""
AWS Lambda service for Python code execution
This service integrates with AWS Lambda to execute Python code securely
"""

import boto3
import json
import base64
from botocore.exceptions import ClientError
import os

class LambdaCodeExecutor:
    """AWS Lambda code executor for Python"""
    
    def __init__(self):
        """Initialize AWS Lambda client"""
        self.lambda_client = boto3.client(
            'lambda',
            region_name=os.environ.get('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
        )
        self.function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'python-code-executor')
    
    def execute_code(self, source_code, stdin='', timeout=5):
        """
        Execute Python code using AWS Lambda
        
        Args:
            source_code (str): Python source code to execute
            stdin (str): Standard input for the program
            timeout (int): Execution timeout in seconds
            
        Returns:
            dict: Execution result with stdout, stderr, status, time, memory
        """
        try:
            # Prepare payload for Lambda function
            payload = {
                'source_code': source_code,
                'stdin': stdin,
                'timeout': timeout
            }
            
            # Debug: Print payload
            print(f"Lambda Payload - stdin length: {len(stdin)}, stdin: {repr(stdin[:100])}")
            
            # Invoke Lambda function
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            # Debug: Print what we got from Lambda
            print(f"Lambda Response: {response_payload}")
            
            # Check if there was an error in Lambda execution
            if 'errorMessage' in response_payload:
                error_msg = response_payload.get('errorMessage', 'Lambda execution error')
                return {
                    'stdout': None,
                    'stderr': base64.b64encode(error_msg.encode()).decode(),
                    'status': {'id': 13, 'description': 'Internal Error'},
                    'time': None,
                    'memory': None
                }
            
            # Return formatted result (encode output as base64 to match expected format)
            stdout_data = response_payload.get('stdout', '')
            stderr_data = response_payload.get('stderr')
            
            # Handle both string and None cases
            encoded_stdout = None
            if stdout_data is not None:
                if isinstance(stdout_data, str):
                    encoded_stdout = base64.b64encode(stdout_data.encode()).decode()
                else:
                    encoded_stdout = base64.b64encode(str(stdout_data).encode()).decode()
            
            encoded_stderr = None
            if stderr_data:
                if isinstance(stderr_data, str):
                    encoded_stderr = base64.b64encode(stderr_data.encode()).decode()
                else:
                    encoded_stderr = base64.b64encode(str(stderr_data).encode()).decode()
            
            result = {
                'stdout': encoded_stdout,
                'stderr': encoded_stderr,
                'status': response_payload.get('status', {'id': 3, 'description': 'Accepted'}),
                'time': response_payload.get('time', '0.0'),
                'memory': response_payload.get('memory', 0),
                'compile_output': None,
                'message': None,
                'token': None
            }
            
            print(f"Returning to frontend - stdout (base64): {result['stdout'][:50] if result['stdout'] else 'None'}")
            return result
            
        except ClientError as e:
            error_msg = f"AWS Lambda error: {str(e)}"
            return {
                'stdout': None,
                'stderr': base64.b64encode(error_msg.encode()).decode(),
                'status': {'id': 13, 'description': 'Internal Error'},
                'time': None,
                'memory': None,
                'message': base64.b64encode(error_msg.encode()).decode()
            }
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            return {
                'stdout': None,
                'stderr': base64.b64encode(error_msg.encode()).decode(),
                'status': {'id': 13, 'description': 'Internal Error'},
                'time': None,
                'memory': None,
                'message': base64.b64encode(error_msg.encode()).decode()
            }


def execute_python_code_lambda(source_code, stdin='', base64_encoded=False):
    """
    Execute Python code using AWS Lambda
    
    Args:
        source_code (str): Python source code (base64 encoded if base64_encoded=True)
        stdin (str): Standard input (base64 encoded if base64_encoded=True)
        base64_encoded (bool): Whether inputs are base64 encoded
        
    Returns:
        dict: Execution result matching Judge0 API format
    """
    # Decode if base64 encoded
    if base64_encoded:
        try:
            source_code = base64.b64decode(source_code).decode('utf-8')
            stdin = base64.b64decode(stdin).decode('utf-8') if stdin else ''
        except Exception as e:
            return {
                'stdout': None,
                'stderr': base64.b64encode(f"Failed to decode base64: {str(e)}".encode()).decode() if base64_encoded else f"Failed to decode base64: {str(e)}",
                'status': {'id': 11, 'description': 'Runtime Error'},
                'time': None,
                'memory': None
            }
    
    # Debug: Print what we're sending to Lambda
    print(f"Sending to Lambda - stdin: {repr(stdin)}")
    
    # Create executor and run code
    executor = LambdaCodeExecutor()
    result = executor.execute_code(source_code, stdin)
    
    # Output is already base64 encoded in execute_code method
    return result
