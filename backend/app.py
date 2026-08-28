"""
CampusFix AI - Flask Backend
Main application file
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ReturnDocument
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
import re
from functools import wraps
from dotenv import load_dotenv
from bson import ObjectId
from llm_service import get_llm_service
from pathlib import Path

# Load environment variables from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'campusfix-ai-secret-key-2026')
CORS(app)  # Enable CORS for frontend

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    print("✗ MONGO_URI not found in environment variables")
    raise ValueError("MONGO_URI is required")

try:
    client = MongoClient(MONGO_URI)
    # Test connection
    client.admin.command('ping')
    print("✓ MongoDB connected successfully")
except Exception as e:
    error_msg = str(e)
    if 'escaped according to RFC 3986' in error_msg:
        print(f"✗ MongoDB connection failed: {error_msg}")
        print()
        print("SOLUTION:")
        print("Your MongoDB password contains special characters that need URL encoding.")
        print()
        print("Run this command to encode your password:")
        print("  python3 backend/encode_mongo_password.py")
        print()
        print("Then update MONGO_URI in .env with the encoded password")
        print()
    else:
        print(f"✗ MongoDB connection failed: {error_msg}")
    raise

db = client['campusfix_ai']

# Collections
users_collection = db['users']
conversations_collection = db['conversations']
tickets_collection = db['tickets']
knowledge_base_collection = db['knowledge_base']
admins_collection = db['admins']
counters_collection = db['counters']

def ensure_index(collection, keys, name, **options):
    normalized_keys = dict(keys) if isinstance(keys, list) else {keys: 1}
    existing_keys = [dict(index['key']) for index in collection.list_indexes()]
    if normalized_keys not in existing_keys:
        collection.create_index(keys, name=name, **options)

ensure_index(users_collection, 'email', 'users_email_unique', unique=True)
ensure_index(users_collection, 'registration_number', 'users_registration_number_unique', unique=True, sparse=True)
ensure_index(users_collection, 'employee_id', 'users_employee_id_unique', unique=True, sparse=True)
ensure_index(admins_collection, 'email', 'admins_email_unique', unique=True)
ensure_index(tickets_collection, 'ticket_id', 'tickets_ticket_id_unique', unique=True)
ensure_index(tickets_collection, [('user_id', 1), ('created_at', -1)], 'tickets_user_created')
ensure_index(tickets_collection, [('status', 1), ('priority', 1), ('department', 1)], 'tickets_filters')

# ============================================
# HELPER FUNCTIONS
# ============================================

def generate_token(user_id, registration_number):
    """Generate JWT token for user authentication"""
    payload = {
        'user_id': str(user_id),
        'registration_number': registration_number,
        'role': 'user',
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def generate_admin_token(admin):
    payload = {
        'admin_id': str(admin['_id']),
        'role': 'admin',
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def get_bearer_token():
    return request.headers.get('Authorization', '').replace('Bearer ', '').strip()

def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = get_bearer_token()
        payload = verify_token(token) if token else None
        if not payload or payload.get('role') != 'admin' or not payload.get('admin_id'):
            return jsonify({'error': 'Administrator authentication required'}), 403
        admin = admins_collection.find_one({'_id': ObjectId(payload['admin_id'])})
        if not admin:
            return jsonify({'error': 'Administrator not found'}), 403
        request.admin = admin
        return view(*args, **kwargs)
    return wrapped

def require_user(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = get_bearer_token()
        payload = verify_token(token) if token else None
        if not payload or payload.get('role') != 'user' or not payload.get('user_id'):
            return jsonify({'error': 'User authentication required'}), 401
        try:
            user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        except Exception:
            user = None
        if not user:
            return jsonify({'error': 'User not found'}), 401
        return view(*args, **kwargs)
    return wrapped

def serialize_document(document):
    if isinstance(document, ObjectId):
        return str(document)
    if isinstance(document, datetime):
        return document.isoformat()
    if isinstance(document, list):
        return [serialize_document(item) for item in document]
    if isinstance(document, dict):
        return {key: serialize_document(value) for key, value in document.items()}
    return document

def next_ticket_id():
    counter = counters_collection.find_one_and_update(
        {'_id': 'tickets'},
        {'$inc': {'value': 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return f"CF-{datetime.utcnow().year}-{counter['value']:05d}"

def category_department(category):
    return {
        'wifi': 'Network Support',
        'login': 'Account Support',
        'software': 'Software Support',
        'printer': 'Hardware Support',
        'hardware': 'Hardware Support',
        'other': 'General IT Support'
    }.get(category, 'General IT Support')

def retrieve_knowledge_context(user_message):
    terms = [term for term in re.findall(r'[a-zA-Z]{4,}', user_message.lower())[:8]]
    if not terms:
        return ''
    pattern = '|'.join(re.escape(term) for term in terms)
    articles = knowledge_base_collection.find({
        '$or': [
            {'title': {'$regex': pattern, '$options': 'i'}},
            {'category': {'$regex': pattern, '$options': 'i'}},
            {'tags': {'$regex': pattern, '$options': 'i'}},
            {'content': {'$regex': pattern, '$options': 'i'}}
        ]
    }).limit(3)
    return '\n\n'.join(f"{article.get('title', 'Campus IT guidance')}: {article.get('content', '')[:1800]}" for article in articles)

def ticket_category(message):
    normalized = message.lower().replace('wi-fi', 'wifi')
    return next((category for category in ('wifi', 'login', 'software', 'printer', 'hardware') if category in normalized), 'other')

def ticket_issue(conversation_history, latest_message):
    user_messages = [message.get('content', '').strip() for message in conversation_history if message.get('role') == 'user']
    return (user_messages[0] if user_messages else latest_message)[:200]

def ticket_troubleshooting(category):
    steps = {
        'wifi': ['Checked Wi-Fi connection', 'Attempted basic network troubleshooting'],
        'login': ['Checked account credentials', 'Attempted basic sign-in troubleshooting'],
        'software': ['Checked the software setup', 'Attempted basic application troubleshooting'],
        'printer': ['Checked printer connectivity', 'Attempted basic printing troubleshooting'],
        'hardware': ['Checked the hardware connection', 'Attempted basic hardware troubleshooting']
    }
    return steps.get(category, ['Reviewed the reported IT issue', 'Attempted basic troubleshooting']) + ['Issue remained unresolved']

def generate_ticket_summary(issue, troubleshooting_steps=None, category=None, resolved=False):
    return f'User reported: {issue}. AI troubleshooting was attempted but the issue could not be resolved, so it was escalated to IT support.'

def create_ticket_record(user, payload, conversation_id=None, automatic=False):
    existing = tickets_collection.find_one({'user_id': str(user['_id']), 'conversation_id': conversation_id}) if conversation_id else None
    if existing:
        return existing, False

    now = datetime.utcnow()
    category = payload.get('category', 'other')
    department = category_department(category)
    ticket_id = next_ticket_id()
    issue = payload.get('issue', 'Campus IT issue')[:200]
    priority = payload.get('priority', 'medium').lower()
    if priority == 'urgent':
        priority = 'high'
    ticket = {
        'ticket_id': ticket_id,
        'user_id': str(user['_id']),
        'user_type': user.get('usertype', ''),
        'username': user.get('username', ''),
        'registration_number': user.get('registration_number'),
        'employee_id': user.get('employee_id'),
        'email': user.get('email'),
        'issue': issue,
        'category': category,
        'priority': priority,
        'description': payload.get('description', '')[:10000],
        'ai_summary': payload.get('ai_summary') or f'User submitted a {category} support request: {issue}.',
        'troubleshooting_attempted': [str(step)[:300] for step in payload.get('troubleshooting_attempted', [])][:10],
        'conversation_id': conversation_id,
        'status': 'open',
        'department': department,
        'assigned_team': None,
        'assigned_admin': None,
        'admin_notes': [],
        'timeline': [{
            'event': 'Issue reported and ticket created automatically' if automatic else 'Ticket created',
            'actor': 'Fixie AI' if automatic else user.get('username', 'User'),
            'at': now
        }],
        'location': payload.get('location', '')[:200],
        'created_at': now,
        'updated_at': now,
        'resolved_at': None
    }
    tickets_collection.insert_one(ticket)
    if conversation_id:
        try:
            conversations_collection.update_one(
                {'_id': ObjectId(conversation_id), 'user_id': str(user['_id'])},
                {'$set': {'ticket_id': ticket_id, 'status': 'ticket_created'}}
            )
        except Exception:
            pass
    return ticket, True

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def generate_ticket_id():
    """Generate unique ticket ID"""
    year = datetime.now().year
    count = tickets_collection.count_documents({'created_at': {'$gte': datetime(year, 1, 1)}})
    return f"IT-{year}-{str(count + 1).zfill(5)}"

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/api/auth/check-user', methods=['POST'])
def check_user():
    """Check if user exists based on user type and ID"""
    try:
        data = request.json
        
        # Validate required fields
        if 'usertype' not in data or 'id' not in data:
            return jsonify({'error': 'User type and ID are required'}), 400
        
        usertype = data['usertype']
        user_id = data['id'].strip()
        
        if usertype not in ['student', 'employee']:
            return jsonify({'error': 'Invalid user type'}), 400
        
        # Search for user based on type
        if usertype == 'student':
            user = users_collection.find_one({'registration_number': user_id, 'usertype': 'student'})
        else:  # employee
            user = users_collection.find_one({'employee_id': user_id, 'usertype': 'employee'})
        
        if user:
            return jsonify({
                'exists': True,
                'usertype': user['usertype'],
                'firstName': user.get('firstName', user.get('username', '')),
                'id': user.get('registration_number') if usertype == 'student' else user.get('employee_id')
            }), 200
        else:
            return jsonify({
                'exists': False,
                'usertype': usertype,
                'id': user_id
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'password', 'usertype']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate usertype
        if data['usertype'] not in ['student', 'employee']:
            return jsonify({'error': 'Invalid usertype. Must be student or employee'}), 400
        
        # Validate ID based on user type
        if data['usertype'] == 'student':
            if 'registration_number' not in data or not data['registration_number']:
                return jsonify({'error': 'Registration number is required for students'}), 400
            user_identifier = data['registration_number']
            identifier_field = 'registration_number'
        else:  # employee
            if 'employee_id' not in data or not data['employee_id']:
                return jsonify({'error': 'Employee ID is required for employees'}), 400
            user_identifier = data['employee_id']
            identifier_field = 'employee_id'
        
        # Check if user already exists
        existing_user = users_collection.find_one({identifier_field: user_identifier})
        if existing_user:
            return jsonify({'error': f'{identifier_field.replace("_", " ").title()} already exists'}), 409
        
        if users_collection.find_one({'email': data['email']}):
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create user document
        user = {
            'firstName': data['firstName'].strip(),
            'lastName': data['lastName'].strip(),
            'username': f"{data['firstName']} {data['lastName']}".strip(),
            'email': data['email'].lower().strip(),
            'usertype': data['usertype'],
            'password': hash_password(data['password']),
            'phone': data.get('phone', ''),
            'department': data.get('department', ''),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        
        # Add type-specific ID
        if data['usertype'] == 'student':
            user['registration_number'] = user_identifier
        else:
            user['employee_id'] = user_identifier
        
        # Insert user
        result = users_collection.insert_one(user)
        user_id = result.inserted_id
        
        # Generate token
        token = generate_token(user_id, user_identifier)
        
        # Return success response
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': str(user_id),
                'firstName': user['firstName'],
                'lastName': user['lastName'],
                'username': user['username'],
                'email': user['email'],
                'usertype': user['usertype'],
                'registration_number': user.get('registration_number'),
                'employee_id': user.get('employee_id')
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        
        # Validate required fields
        if 'usertype' not in data or 'id' not in data or 'password' not in data:
            return jsonify({'error': 'User type, ID, and password are required'}), 400
        
        usertype = data['usertype']
        user_id = data['id']
        
        # Find user based on type
        if usertype == 'student':
            user = users_collection.find_one({'registration_number': user_id, 'usertype': 'student'})
            identifier = user_id
        elif usertype == 'employee':
            user = users_collection.find_one({'employee_id': user_id, 'usertype': 'employee'})
            identifier = user_id
        else:
            return jsonify({'error': 'Invalid usertype'}), 400
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if not verify_password(data['password'], user['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Check if user is active
        if not user.get('is_active', True):
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Generate token
        token = generate_token(user['_id'], identifier)
        
        # Update last login
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.utcnow()}}
        )
        
        # Return success response
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'firstName': user.get('firstName', ''),
                'lastName': user.get('lastName', ''),
                'username': user.get('username', ''),
                'email': user['email'],
                'usertype': user['usertype'],
                'registration_number': user.get('registration_number'),
                'employee_id': user.get('employee_id'),
                'department': user.get('department', ''),
                'role': user.get('role', 'user')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
@require_user
def get_current_user():
    """Get current user info from token"""
    try:
        # Get token from header
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user
        user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'user': {
                'id': str(user['_id']),
                'firstName': user.get('firstName', ''),
                'lastName': user.get('lastName', ''),
                'username': user.get('username', ''),
                'registration_number': user.get('registration_number'),
                'employee_id': user.get('employee_id'),
                'email': user['email'],
                'usertype': user['usertype'],
                'department': user.get('department', ''),
                'phone': user.get('phone', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user (client-side token removal)"""
    try:
        # In JWT, logout is typically handled client-side by removing the token
        # We can optionally blacklist tokens here if needed
        return jsonify({
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# CHAT ROUTES
# ============================================

@app.route('/api/llm/test', methods=['GET'])
def test_llm():
    """Test LLM connection"""
    try:
        llm_service = get_llm_service()
        result = llm_service.test_connection()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat/send', methods=['POST'])
@require_user
def send_message():
    """Send message to AI and get response using LLM"""
    try:
        print("\n[CHAT DEBUG] Request received")
        
        # Get token and verify user
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            print("[CHAT DEBUG] No token provided")
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            print("[CHAT DEBUG] Invalid token")
            return jsonify({'error': 'Invalid token'}), 401
        
        print(f"[CHAT DEBUG] User authenticated: YES (user_id: {payload['user_id']})")
        
        data = request.json
        user_message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        
        print(f"[CHAT DEBUG] Message received: {'YES' if user_message else 'NO'}")
        if user_message:
            print(f"[CHAT DEBUG] Message preview: {user_message[:50]}...")
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user info
        user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        if not user:
            print("[CHAT DEBUG] User not found in database")
            return jsonify({'error': 'User not found'}), 404
        
        # Get or create conversation
        if not conversation_id:
            conversation = {
                'user_id': payload['user_id'],
                'user_firstName': user.get('firstName', ''),
                'user_lastName': user.get('lastName', ''),
                'user_type': user.get('usertype', ''),
                'started_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'messages': [],
                'status': 'active'
            }
            result = conversations_collection.insert_one(conversation)
            conversation_id = str(result.inserted_id)
            messages_history = []
        else:
            # Get existing conversation
            conversation = conversations_collection.find_one({
                '_id': ObjectId(conversation_id),
                'user_id': payload['user_id']
            })
            if not conversation:
                return jsonify({'error': 'Conversation not found'}), 404
            messages_history = conversation.get('messages', [])
        
        # Add user message to database
        user_msg = {
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.utcnow()
        }
        
        conversations_collection.update_one(
            {'_id': ObjectId(conversation_id)},
            {
                '$push': {'messages': user_msg},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        print("[CHAT DEBUG] Calling LLM")
        
        # Get LLM response
        llm_service = get_llm_service()
        knowledge_context = retrieve_knowledge_context(user_message)
        llm_result = llm_service.get_response(
            user_message=user_message,
            conversation_history=messages_history,
            user_firstName=user.get('firstName'),
            knowledge_context=knowledge_context
        )
        
        print(f"[CHAT DEBUG] LLM response received: {'YES' if llm_result.get('success') else 'NO'}")
        
        if not llm_result['success']:
            print(f"[CHAT DEBUG] LLM error: {llm_result.get('error')}")
            return jsonify({
                'error': 'LLM Error',
                'details': llm_result.get('error', 'Unknown error')
            }), 500

        user_message_count = len(messages_history) // 2 + 1
        it_keywords = ('wifi', 'wi-fi', 'internet', 'network', 'login', 'password',
                       'software', 'install', 'printer', 'hardware', 'vpn')
        unresolved_keywords = ('still', 'unable', 'cannot', "can't", 'not working',
                               "doesn't work", 'failed', 'no')
        normalized_message = user_message.lower()
        conversation_text = ' '.join(msg.get('content', '') for msg in messages_history).lower()
        is_it_issue = any(keyword in f'{conversation_text} {normalized_message}' for keyword in it_keywords)
        needs_human_support = is_it_issue and user_message_count >= 4 and any(
            keyword in normalized_message for keyword in unresolved_keywords
        )

        # Advance the visible workflow as the conversation develops.
        user_message_count = len(messages_history) // 2 + 1
        workflow_stages = ['ai_diagnoses', 'find_solution', 'troubleshoot', 'check_result']
        stage = 'human_support' if needs_human_support else workflow_stages[min(user_message_count - 1, len(workflow_stages) - 1)]

        automatic_ticket = None
        if needs_human_support:
            category = ticket_category(' '.join(msg.get('content', '') for msg in messages_history) + ' ' + user_message)
            issue = ticket_issue(messages_history, user_message)
            automatic_ticket, _ = create_ticket_record(
                user,
                {
                    'issue': issue,
                    'category': category,
                    'priority': 'high',
                    'description': f'AI troubleshooting could not resolve the issue. Latest user message: {user_message}',
                    'ai_summary': generate_ticket_summary(issue, ticket_troubleshooting(category), category, resolved=False),
                    'troubleshooting_attempted': ticket_troubleshooting(category)
                },
                conversation_id=conversation_id,
                automatic=True
            )
        
        # Add assistant message to database
        assistant_msg = {
            'role': 'assistant',
            'content': llm_result['message'],
            'timestamp': datetime.utcnow()
        }
        
        conversations_collection.update_one(
            {'_id': ObjectId(conversation_id)},
            {
                '$push': {'messages': assistant_msg},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )
        
        print("[CHAT DEBUG] Returning response")
        
        return jsonify({
            'conversation_id': conversation_id,
            'response': {
                'message': llm_result['message'],
                'model': llm_result.get('model'),
                'usage': llm_result.get('usage'),
                'stage': stage,
                'quickReplies': [],
                'suggestTicket': bool(automatic_ticket),
                'ticket': {
                    'ticket_id': automatic_ticket['ticket_id'],
                    'status': automatic_ticket['status'],
                    'department': automatic_ticket['department']
                } if automatic_ticket else None
            }
        }), 200
        
    except Exception as e:
        print(f"✗ [CHAT DEBUG] Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET'])
@require_user
def get_chat_history():
    """Get user's chat history"""
    try:
        # Get token and verify user
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get conversations
        conversations = list(conversations_collection.find(
            {'user_id': payload['user_id']},
            {'password': 0}
        ).sort('updated_at', -1).limit(20))
        
        # Convert ObjectId to string
        for conv in conversations:
            conv['_id'] = str(conv['_id'])
            for msg in conv.get('messages', []):
                if 'timestamp' in msg:
                    msg['timestamp'] = msg['timestamp'].isoformat()
        
        return jsonify({'conversations': conversations}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# TICKET ROUTES
# ============================================

@app.route('/api/tickets/create', methods=['POST'])
@app.route('/api/tickets', methods=['POST'])
@require_user
def create_ticket():
    """Create a new support ticket"""
    try:
        # Get token and verify user
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.json or {}
        
        # Validate required fields
        required_fields = ['issue', 'category', 'description', 'priority']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if data.get('category') not in ['wifi', 'login', 'software', 'printer', 'hardware', 'other']:
            return jsonify({'error': 'Invalid ticket category'}), 400
        if data.get('priority', '').lower() not in ['low', 'medium', 'high', 'urgent', 'critical']:
            return jsonify({'error': 'Invalid ticket priority'}), 400

        user = users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        ticket, created = create_ticket_record(user, data, data.get('conversation_id'))
        
        return jsonify({
            'success': True,
            'message': 'Ticket already existed' if not created else 'Ticket created successfully',
            'ticket_id': ticket['ticket_id'],
            'status': ticket['status'].upper(),
            'ticket': serialize_document(ticket)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/my-tickets', methods=['GET'])
@app.route('/api/tickets/my', methods=['GET'])
@require_user
def get_my_tickets():
    """Get user's tickets"""
    try:
        # Get token and verify user
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get tickets
        tickets = list(tickets_collection.find(
            {'user_id': payload['user_id']}
        ).sort('created_at', -1))
        
        # Convert ObjectId and datetime to string
        tickets = [serialize_document(ticket) for ticket in tickets]
        
        return jsonify({'tickets': tickets}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/<ticket_id>', methods=['GET'])
@require_user
def get_ticket(ticket_id):
    """Get ticket details"""
    try:
        # Get token and verify user
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get ticket
        ticket = tickets_collection.find_one({
            'ticket_id': ticket_id,
            'user_id': payload['user_id']
        })
        
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        
        # Convert ObjectId and datetime to string
        ticket = serialize_document(ticket)
        
        return jsonify({'ticket': ticket}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ADMIN ROUTES
# ============================================

@app.route('/api/admin/register', methods=['POST'])
def register_admin():
    data = request.json or {}
    registration_code = os.getenv('ADMIN_REGISTRATION_CODE')
    if not registration_code or data.get('registration_code') != registration_code:
        return jsonify({'error': 'Valid admin registration code required'}), 403
    required = ('name', 'email', 'password')
    if not all(data.get(field) for field in required) or len(data['password']) < 8:
        return jsonify({'error': 'Name, email, and a password of at least 8 characters are required'}), 400
    email = data['email'].lower().strip()
    if admins_collection.find_one({'email': email}):
        return jsonify({'error': 'Admin email already exists'}), 409
    now = datetime.utcnow()
    admin = {
        'admin_id': f"ADM-{ObjectId()}",
        'name': data['name'].strip()[:120],
        'email': email,
        'password_hash': hash_password(data['password']),
        'role': 'admin',
        'created_at': now,
        'updated_at': now
    }
    admins_collection.insert_one(admin)
    return jsonify({'success': True, 'message': 'Admin account created'}), 201

@app.route('/api/admin/login', methods=['POST'])
def login_admin():
    data = request.json or {}
    admin = admins_collection.find_one({'email': data.get('email', '').lower().strip()})
    if not admin or not data.get('password') or not verify_password(data['password'], admin['password_hash']):
        return jsonify({'error': 'Invalid admin credentials'}), 401
    return jsonify({
        'success': True,
        'token': generate_admin_token(admin),
        'admin': {'id': str(admin['_id']), 'name': admin['name'], 'email': admin['email'], 'role': 'admin'}
    }), 200

@app.route('/api/admin/stats', methods=['GET'])
@require_admin
def admin_stats():
    category_counts = {
        category: tickets_collection.count_documents({'category': category})
        for category in ('wifi', 'login', 'software', 'printer', 'hardware', 'other')
    }
    status_counts = {
        status: tickets_collection.count_documents({'status': status})
        for status in ('open', 'assigned', 'in_progress', 'waiting_for_user', 'resolved', 'closed')
    }
    priority_counts = {
        priority: tickets_collection.count_documents({'priority': priority})
        for priority in ('low', 'medium', 'high', 'critical')
    }
    return jsonify({
        'total_users': users_collection.count_documents({}),
        'students': users_collection.count_documents({'usertype': 'student'}),
        'employees': users_collection.count_documents({'usertype': 'employee'}),
        'total': tickets_collection.count_documents({}),
        'open': tickets_collection.count_documents({'status': {'$in': ['open', 'assigned']}}),
        'in_progress': tickets_collection.count_documents({'status': 'in_progress'}),
        'resolved': tickets_collection.count_documents({'status': {'$in': ['resolved', 'closed']}}),
        'high_priority': tickets_collection.count_documents({'priority': {'$in': ['high', 'critical']}}),
        'total_conversations': conversations_collection.count_documents({}),
        'human_escalations': tickets_collection.count_documents({'conversation_id': {'$ne': None}}),
        'ai_resolution_rate': None,
        'category_counts': category_counts,
        'status_counts': status_counts,
        'priority_counts': priority_counts
    }), 200

@app.route('/api/admin/tickets', methods=['GET'])
@require_admin
def admin_tickets():
    query = {}
    for field in ('status', 'priority', 'category', 'department', 'assigned_team'):
        if request.args.get(field):
            query[field] = request.args[field].lower() if field in ('status', 'priority') else request.args[field]
    search = request.args.get('search', '').strip()
    if search:
        query['$or'] = [
            {'ticket_id': {'$regex': search, '$options': 'i'}},
            {'username': {'$regex': search, '$options': 'i'}},
            {'issue': {'$regex': search, '$options': 'i'}}
        ]
    tickets = [serialize_document(ticket) for ticket in tickets_collection.find(query).sort('created_at', -1).limit(200)]
    return jsonify({'tickets': tickets}), 200

@app.route('/api/admin/tickets/<ticket_id>', methods=['GET'])
@require_admin
def admin_ticket_detail(ticket_id):
    ticket = tickets_collection.find_one({'ticket_id': ticket_id})
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    return jsonify({'ticket': serialize_document(ticket)}), 200

@app.route('/api/admin/tickets/<ticket_id>', methods=['PATCH'])
@require_admin
def update_admin_ticket(ticket_id):
    ticket = tickets_collection.find_one({'ticket_id': ticket_id})
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    data = request.json or {}
    allowed = {
        'status': {'open', 'assigned', 'in_progress', 'waiting_for_user', 'resolved', 'closed'},
        'priority': {'low', 'medium', 'high', 'critical'},
        'assigned_team': {'Network Support', 'Hardware Support', 'Software Support', 'Account Support', 'General IT Support'}
    }
    updates = {}
    timeline_event = []
    for field, values in allowed.items():
        if field in data:
            value = str(data[field]).lower() if field in ('status', 'priority') else data[field]
            if value not in values:
                return jsonify({'error': f'Invalid {field}'}), 400
            updates[field] = value
            timeline_event.append(f'{field.replace("_", " ").title()} changed to {value}')
    if 'assigned_admin' in data:
        updates['assigned_admin'] = str(data['assigned_admin'])[:120]
        timeline_event.append('Administrator assignment updated')
    note = str(data.get('note', '')).strip()
    now = datetime.utcnow()
    if note:
        updates.setdefault('admin_notes', ticket.get('admin_notes', []))
        updates['admin_notes'] = ticket.get('admin_notes', []) + [{'note': note[:2000], 'admin': request.admin['name'], 'at': now}]
        timeline_event.append('Administrator note added')
    if not updates:
        return jsonify({'error': 'No valid updates supplied'}), 400
    timeline = ticket.get('timeline', []) + [{'event': event, 'actor': request.admin['name'], 'at': now} for event in timeline_event]
    updates['timeline'] = timeline
    updates['updated_at'] = now
    if updates.get('status') == 'resolved':
        updates['resolved_at'] = now
    tickets_collection.update_one({'_id': ticket['_id']}, {'$set': updates})
    updated = tickets_collection.find_one({'_id': ticket['_id']})
    return jsonify({'success': True, 'ticket': serialize_document(updated)}), 200

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def admin_users():
    users = [serialize_document(user) for user in users_collection.find({}, {'password': 0}).sort('created_at', -1).limit(500)]
    return jsonify({'users': users}), 200

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    health_status = {
        'status': 'ok',
        'mongodb': False,
        'llm_configured': False,
        'model': None,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    try:
        # Check MongoDB connection
        client.admin.command('ping')
        health_status['mongodb'] = True
    except Exception as e:
        health_status['mongodb_error'] = str(e)
        health_status['status'] = 'degraded'
    
    try:
        # Check LLM configuration
        llm_service = get_llm_service()
        health_status['llm_configured'] = True
        health_status['model'] = llm_service.model
    except Exception as e:
        health_status['llm_error'] = str(e)
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'ok' else 503
    return jsonify(health_status), status_code

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        'message': 'CampusFix AI Backend API',
        'version': '2.0.0',
        'description': 'Intelligent campus AI assistant powered by Groq',
        'llm_provider': 'Groq',
        'endpoints': {
            'auth': ['/api/auth/register', '/api/auth/login', '/api/auth/me'],
            'chat': ['/api/chat/send', '/api/chat/history'],
            'tickets': ['/api/tickets/create', '/api/tickets/my-tickets', '/api/tickets/<ticket_id>'],
            'llm': ['/api/llm/test'],
            'health': '/api/health'
        }
    }), 200

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
