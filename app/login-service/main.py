from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
import os
from dotenv import load_dotenv
from database import get_user_by_email, create_user, get_role_by_name

# Load environment variables
load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Updated to Vite's default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add session middleware with secure settings
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "JrFglAnbqZxzSVQ1bar2ZtXbMG8cRvgoi4JWBjXN7dQ"),
    session_cookie="session",
    max_age=3600,  # 1 hour
    same_site="lax",  # Changed to none for cross-origin
    https_only=False,  # Set to True in production
    path="/",  # Ensure cookie is available for all paths
    # domain=None
)

# OAuth2 setup
config = Config('.env')
oauth = OAuth(config)

# Google OAuth2 configuration
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    print("Session before login:", request.session)  # Add this
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth(request: Request):
    # print("Callback request:", request.url)
    print("Session in callback:", request.session)  # Add this

    try:
        # Step 1: Get token from Google
        token = await oauth.google.authorize_access_token(request)
        # print(token)

        # Step 2: Get user info from token
        userinfo = await oauth.google.userinfo(token=token)
        
        email = userinfo.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
            
        # Step 3: Check if user exists
        print("Google email:", email)
        user = get_user_by_email(email)
        if not user and email.endswith('@cse.mrt.ac.lk'):
            # Extract name from email (part before the first dot)
            name = email.split('@')[0].split('.')[0].capitalize()       
                 
            # Determine role based on whether the name contains numbers
            if any(char.isdigit() for char in email):
                role_id = "11111111-1111-1111-1111-111111111111"  # Student role
            else:
                role_id = "22222222-2222-2222-2222-222222222222"  # Faculty role
                
            # Create new user
            user = await create_user(email, name, role_id)
            if not user:
                return RedirectResponse(url='http://localhost:5173?error=Failed to create user')
            else:
                user = get_user_by_email(email)
        
        if not user:
            return RedirectResponse(url='http://localhost:5173?error=User not authorized')
            
        print("User found:", user)
        # Step 4: Extract role name from nested "roles" table
        role_data = user.get('roles')
        
        print("Role data:", role_data)
        role_name = role_data.get('role_name') if role_data else None
        if not role_name:
            return RedirectResponse(url='http://localhost:5173?error=User role not found')
        
        # Step 5: Set session data
        session_data = {
            'id': user['id'],
            'email': email,
            'name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
            'role': role_name
        }
        print("Setting session data:", session_data)
        
        # Create response with session data
        if role_name == 'Student':
            redirect_url = 'http://localhost:5173/student-dashboard'
        elif role_name == 'Faculty':
            redirect_url = 'http://localhost:5173/faculty-dashboard'
        elif role_name == 'Admin':
            redirect_url = 'http://localhost:5173/admin-dashboard'
        else:
            redirect_url = 'http://localhost:5173?error=Unknown role'
        
        # Set session before creating response
        request.session['user'] = session_data
        print("Session after setting:", request.session)
        
        # Create response with session cookie
        response = RedirectResponse(url=redirect_url)
        
        # Debug: Print all cookies being set
        print("Response cookies:", response.headers.get('set-cookie'))
        
        return response
    except Exception as e:
        print(f"Auth error: {str(e)}")
        return RedirectResponse(url='http://localhost:5173?error=Authentication Failed')

@app.get("/user")
async def get_user(request: Request):
    print("Current session:", request.session)
    print("Request cookies:", request.cookies)
    user = request.session.get('user')
    if not user:
        print("No user found in session")
        raise HTTPException(status_code=401, detail="Not authenticated")
    print("Found user in session:", user)
    return user

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return JSONResponse({
        'redirect': 'http://localhost:5173'
    }) 