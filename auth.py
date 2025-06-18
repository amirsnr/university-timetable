from flask import Blueprint, request, jsonify, current_app
from db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime
import psycopg2

auth_bp = Blueprint('auth', __name__)

# ---------------------- TOKEN DECORATORS ---------------------- #

def token_required(f):
    """Decorator to validate JWT tokens for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Extracts token from Authorization header (Bearer <token>)
        if 'Authorization' in request.headers:
            bearer = request.headers['Authorization']
            token = bearer.split()[1] if len(bearer.split()) > 1 else None

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired! Login again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(user_id, *args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator to restrict access to admin-only routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            admin_id = data['user_id']
            is_admin = data.get('is_admin', False)

            if not is_admin:
                return jsonify({'message': 'Admin access required!'}), 403

            return f(admin_id, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

    return decorated

# ---------------------- USER ROUTES ---------------------- #

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'message': 'All fields required!'}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'User registered!'}), 201
    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticatea a user or admin and returna a JWT."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required!'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
        is_admin = False

        if not user:
            cur.execute('SELECT * FROM admins WHERE email = %s', (email,))
            user = cur.fetchone()
            is_admin = True if user else False

        if user and check_password_hash(user[3], password):
            token = jwt.encode({
                'user_id': user[0],
                'is_admin': is_admin,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')

            return jsonify({'token': token, 'is_admin': is_admin}), 200
        else:
            return jsonify({'message': 'Invalid credentials!'}), 401
    finally:
        if conn:
            conn.close()

# ---------------------- ADMIN ROUTES ---------------------- #

@auth_bp.route('/admin-register', methods=['POST'])
def admin_register():
    """Register a new admin (admin-only in production)."""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    admin_code = data.get('admin_code') or data.get('adminCode')

    if not all([username, email, password, admin_code]):
        return jsonify({'error': 'All fields required!'}), 400

    if admin_code != "unime":
        return jsonify({'error': 'Invalid admin code'}), 403

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO admins (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()
        return jsonify({'message': 'Admin registered!'}), 201
    except psycopg2.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()


@auth_bp.route('/admin-login', methods=['POST'])
def admin_login():
    """Login route for admin (optional if using common /login)."""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password required!'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM admins WHERE email = %s', (email,))
        admin = cur.fetchone()

        if admin and check_password_hash(admin[3], password):
            token = jwt.encode({
                'user_id': admin[0],
                'is_admin': True,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'token': token, 'is_admin': True}), 200
        else:
            return jsonify({'message': 'Invalid admin credentials!'}), 401
    except Exception:
        return jsonify({'message': 'Server error!'}), 500
    finally:
        if conn:
            conn.close()

# ---------------------- PROTECTED ROUTE EXAMPLE ---------------------- #

@auth_bp.route('/protected', methods=['GET'])
@token_required
def protected_route(current_user_id):
    """Example protected route (requires valid JWT)."""
    return jsonify({'message': f'Authenticated user ID: {current_user_id}'}), 200


# ---------------------- HELPER FUNCTION ---------------------- #

def decode_token(token):
    """Decode JWT token and return payload or None."""
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        return data
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None