"""
CampusFix AI - Database Initialization
Creates collections and indexes for optimal performance
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
DATABASE_NAME = 'campusfix_ai'

def init_database():
    """Initialize database with collections and indexes"""
    
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    print(f"Initializing database: {DATABASE_NAME}")
    
    # ============================================
    # USERS COLLECTION
    # ============================================
    print("\n1. Setting up 'users' collection...")
    users_collection = db['users']
    
    # Create indexes
    try:
        users_collection.create_index([('registration_number', ASCENDING)], unique=True, sparse=True)
    except:
        pass  # Index already exists
    
    try:
        users_collection.create_index([('employee_id', ASCENDING)], unique=True, sparse=True)
    except:
        pass  # Index already exists
    
    try:
        users_collection.create_index([('email', ASCENDING)], unique=True)
    except:
        pass  # Index already exists
    
    try:
        users_collection.create_index([('usertype', ASCENDING)])
    except:
        pass  # Index already exists
    
    try:
        users_collection.create_index([('created_at', DESCENDING)])
    except:
        pass  # Index already exists
    
    print("   ✓ Created indexes for users collection")
    
    # ============================================
    # CONVERSATIONS COLLECTION
    # ============================================
    print("\n2. Setting up 'conversations' collection...")
    conversations_collection = db['conversations']
    
    # Create indexes
    conversations_collection.create_index([('user_id', ASCENDING)])
    conversations_collection.create_index([('registration_number', ASCENDING)])
    conversations_collection.create_index([('updated_at', DESCENDING)])
    conversations_collection.create_index([('status', ASCENDING)])
    
    print("   ✓ Created indexes for conversations collection")
    
    # ============================================
    # TICKETS COLLECTION
    # ============================================
    print("\n3. Setting up 'tickets' collection...")
    tickets_collection = db['tickets']
    
    # Create indexes
    tickets_collection.create_index([('ticket_id', ASCENDING)], unique=True)
    tickets_collection.create_index([('user_id', ASCENDING)])
    tickets_collection.create_index([('registration_number', ASCENDING)])
    tickets_collection.create_index([('status', ASCENDING)])
    tickets_collection.create_index([('priority', ASCENDING)])
    tickets_collection.create_index([('category', ASCENDING)])
    tickets_collection.create_index([('department', ASCENDING)])
    tickets_collection.create_index([('created_at', DESCENDING)])
    
    print("   ✓ Created indexes for tickets collection")
    
    # ============================================
    # KNOWLEDGE BASE COLLECTION
    # ============================================
    print("\n4. Setting up 'knowledge_base' collection...")
    knowledge_base_collection = db['knowledge_base']
    
    # Create indexes
    knowledge_base_collection.create_index([('category', ASCENDING)])
    knowledge_base_collection.create_index([('tags', ASCENDING)])
    knowledge_base_collection.create_index([('title', 'text'), ('content', 'text')])
    
    print("   ✓ Created indexes for knowledge_base collection")
    
    # ============================================
    # INSERT SAMPLE KNOWLEDGE BASE DATA
    # ============================================
    print("\n5. Inserting sample knowledge base articles...")
    
    sample_kb = [
        {
            'title': 'Campus Wi-Fi Connection Guide',
            'category': 'wifi',
            'tags': ['network', 'connectivity', 'wireless'],
            'content': '''
            Step-by-step guide to connect to campus Wi-Fi:
            1. Open Wi-Fi settings on your device
            2. Look for "Campus_WiFi" network
            3. Connect and enter your campus credentials
            4. Accept the security certificate if prompted
            
            Troubleshooting:
            - If network doesn't appear, restart Wi-Fi adapter
            - Ensure you're in a Wi-Fi coverage area
            - Contact IT if problems persist
            ''',
            'views': 0,
            'helpful_count': 0,
            'created_at': None,
            'updated_at': None
        },
        {
            'title': 'Password Reset Instructions',
            'category': 'login',
            'tags': ['password', 'authentication', 'account'],
            'content': '''
            How to reset your campus password:
            1. Visit password.campus.edu
            2. Enter your registration number or email
            3. Verify your identity (email or SMS)
            4. Create a new password meeting requirements:
               - At least 8 characters
               - One uppercase letter
               - One lowercase letter
               - One number
               - One special character
            5. Confirm your new password
            
            Note: Your password will be updated across all campus systems within 15 minutes.
            ''',
            'views': 0,
            'helpful_count': 0,
            'created_at': None,
            'updated_at': None
        },
        {
            'title': 'Software Installation from Campus Portal',
            'category': 'software',
            'tags': ['software', 'installation', 'licenses'],
            'content': '''
            Access free campus software:
            1. Visit software.campus.edu
            2. Log in with campus credentials
            3. Browse available software
            4. Download software with included license key
            
            Available software includes:
            - Microsoft Office Suite
            - Adobe Creative Cloud
            - MATLAB
            - Python and development tools
            - Antivirus software
            
            For unlisted software, submit a request through the IT support portal.
            ''',
            'views': 0,
            'helpful_count': 0,
            'created_at': None,
            'updated_at': None
        },
        {
            'title': 'Campus Printer Setup',
            'category': 'printer',
            'tags': ['printer', 'printing', 'hardware'],
            'content': '''
            How to print on campus:
            1. Connect to campus Wi-Fi
            2. Open your document
            3. Select Print
            4. Choose a campus printer (format: Campus_Building_Floor_Room)
            5. Send your print job
            6. Go to the printer and authenticate with your campus ID
            
            Print Credits:
            - Students: 500 pages per semester (free)
            - Additional pages: $0.05 per page
            
            Supported formats: PDF, Word, PowerPoint, Images
            Color printing available in main library only
            ''',
            'views': 0,
            'helpful_count': 0,
            'created_at': None,
            'updated_at': None
        }
    ]
    
    # Check if knowledge base is empty
    if knowledge_base_collection.count_documents({}) == 0:
        from datetime import datetime
        for article in sample_kb:
            article['created_at'] = datetime.utcnow()
            article['updated_at'] = datetime.utcnow()
        
        knowledge_base_collection.insert_many(sample_kb)
        print(f"   ✓ Inserted {len(sample_kb)} sample articles")
    else:
        print("   ✓ Knowledge base already contains data, skipping sample insert")
    
    # ============================================
    # VERIFY COLLECTIONS
    # ============================================
    print("\n6. Verifying collections...")
    collections = db.list_collection_names()
    
    expected = ['users', 'conversations', 'tickets', 'knowledge_base']
    for collection in expected:
        if collection in collections:
            count = db[collection].count_documents({})
            print(f"   ✓ {collection}: {count} documents")
        else:
            print(f"   ✗ {collection}: NOT FOUND")
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "="*60)
    print("Database initialization complete!")
    print("="*60)
    print(f"\nDatabase: {DATABASE_NAME}")
    print(f"Collections created: {len(expected)}")
    print(f"Total indexes created: 15+")
    print(f"\nYour backend is ready to use! 🚀")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the backend: python app.py")
    print("3. Test the API: curl http://localhost:5001/api/health")
    
    client.close()

if __name__ == '__main__':
    try:
        init_database()
    except Exception as e:
        print(f"\n❌ Error initializing database: {str(e)}")
        print("Please check your MONGO_URI in .env file")
