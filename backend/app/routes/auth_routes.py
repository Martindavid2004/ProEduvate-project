# auth_routes.py

from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from ..database import users_collection
from bson import ObjectId
import jwt
import datetime
import os

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

# Secret key for JWT (should be in environment variable in production)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

def generate_jwt_token(user_id, email, role):
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': str(user_id),
        'email': email,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@auth_bp.route('/register', methods=['POST', 'OPTIONS'])
def register_student():
    """Register a new student user"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['fullName', 'registerNumber', 'email', 'department', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if email already exists
        existing_user = users_collection.find_one({'email': data['email']})
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'An account with this email already exists'
            }), 409
        
        # Check if register number already exists
        existing_register = users_collection.find_one({'registerNumber': data['registerNumber']})
        if existing_register:
            return jsonify({
                'success': False,
                'message': 'This register number is already in use'
            }), 409
        
        # Hash the password
        hashed_password = generate_password_hash(data['password'])
        
        # Create new student user
        new_user = {
            'name': data['fullName'],
            'registerNumber': data['registerNumber'],
            'email': data['email'],
            'department': data['department'],
            'password': hashed_password,
            'role': 'student',
            'rollNo': data['registerNumber'],  # Using register number as roll number
            'attendance': 0,
            'average_score': 0,
            'submittedAssignments': 0,
            'createdAt': datetime.datetime.utcnow(),
            'lastLogin': None,
            'isActive': True
        }
        
        # Insert into database
        result = users_collection.insert_one(new_user)
        user_id = result.inserted_id
        
        # Generate JWT token
        token = generate_jwt_token(user_id, data['email'], 'student')
        
        # Return success response with token
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'token': token,
            'user': {
                'id': str(user_id),
                'name': data['fullName'],
                'email': data['email'],
                'registerNumber': data['registerNumber'],
                'department': data['department'],
                'role': 'student'
            }
        }), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during registration'
        }), 500

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login_student():
    """Login with email and password"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Find user by email
        user = users_collection.find_one({'email': email})
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Verify password
        if not check_password_hash(user['password'], password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
        
        # Update last login
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'lastLogin': datetime.datetime.utcnow()}}
        )
        
        # Generate JWT token
        token = generate_jwt_token(user['_id'], user['email'], user['role'])
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'registerNumber': user.get('registerNumber', ''),
                'department': user.get('department', ''),
                'role': user['role']
            },
            'redirect': f"/{user['role']}"
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred during login'
        }), 500

@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 401
        
        payload = verify_jwt_token(token)
        
        if not payload:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401
        
        return jsonify({
            'success': True,
            'user_id': payload['user_id'],
            'email': payload['email'],
            'role': payload['role']
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
