"""Web authentication endpoint for secure API key entry."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from .nonce_auth import nonce_auth
from ..skyfi.client import SkyFiClient

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/auth/{nonce}", response_class=HTMLResponse)
async def auth_page(nonce: str):
    """Serve the authentication page."""
    # Check if nonce is valid
    status = nonce_auth.check_auth_status(nonce)
    
    if status['status'] == 'invalid':
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SkyFi Authentication - Invalid Link</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .error { color: red; padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Invalid Authentication Link</h1>
            <div class="error">
                This authentication link is invalid or has already been used.
                Please request a new link from Claude.
            </div>
        </body>
        </html>
        """, status_code=404)
    
    if status['status'] == 'expired':
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SkyFi Authentication - Expired</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .error { color: red; padding: 20px; background: #fee; border: 1px solid #fcc; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Authentication Link Expired</h1>
            <div class="error">
                This authentication link has expired. Links are valid for 5 minutes.
                Please request a new link from Claude.
            </div>
        </body>
        </html>
        """, status_code=410)
    
    if status['status'] == 'completed':
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SkyFi Authentication - Success</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .success { color: green; padding: 20px; background: #efe; border: 1px solid #cfc; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>Already Authenticated</h1>
            <div class="success">
                ✅ You've already authenticated successfully!
                You can close this window and return to Claude.
            </div>
        </body>
        </html>
        """)
    
    # Show authentication form
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SkyFi Authentication</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                max-width: 600px; 
                margin: 50px auto; 
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .info {{ 
                background: #e3f2fd; 
                padding: 15px; 
                border-radius: 5px; 
                margin: 20px 0;
            }}
            input[type="password"] {{
                width: 100%;
                padding: 10px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin: 10px 0;
            }}
            button {{
                background: #4CAF50;
                color: white;
                padding: 12px 30px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
            }}
            button:hover {{ background: #45a049; }}
            button:disabled {{ 
                background: #ccc; 
                cursor: not-allowed; 
            }}
            .error {{ 
                color: red; 
                margin: 10px 0;
                padding: 10px;
                background: #fee;
                border: 1px solid #fcc;
                border-radius: 5px;
                display: none;
            }}
            .success {{
                color: green;
                margin: 10px 0;
                padding: 10px;
                background: #efe;
                border: 1px solid #cfc;
                border-radius: 5px;
                display: none;
            }}
            .expires {{
                color: #666;
                font-size: 14px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛰️ SkyFi Authentication</h1>
            
            <div class="info">
                <strong>Secure Authentication</strong><br>
                Enter your SkyFi API key below. This page uses HTTPS encryption 
                and your key will only be stored in memory for your current Claude session.
            </div>
            
            <form id="authForm">
                <label for="apiKey">SkyFi API Key:</label>
                <input 
                    type="password" 
                    id="apiKey" 
                    name="apiKey" 
                    placeholder="sk-..." 
                    required
                    pattern="sk-[a-zA-Z0-9]+"
                    title="API key should start with 'sk-'"
                >
                
                <div id="error" class="error"></div>
                <div id="success" class="success"></div>
                
                <button type="submit" id="submitBtn">Authenticate</button>
            </form>
            
            <div class="expires">
                This link expires at: {status['expires_at']}
            </div>
        </div>
        
        <script>
            document.getElementById('authForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const apiKey = document.getElementById('apiKey').value;
                const submitBtn = document.getElementById('submitBtn');
                const errorDiv = document.getElementById('error');
                const successDiv = document.getElementById('success');
                
                // Reset displays
                errorDiv.style.display = 'none';
                successDiv.style.display = 'none';
                
                // Disable form
                submitBtn.disabled = true;
                submitBtn.textContent = 'Authenticating...';
                
                try {{
                    const response = await fetch('/auth/{nonce}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ api_key: apiKey }})
                    }});
                    
                    const data = await response.json();
                    
                    if (response.ok) {{
                        successDiv.textContent = '✅ ' + data.message;
                        successDiv.style.display = 'block';
                        submitBtn.textContent = 'Success!';
                        
                        // Redirect after 2 seconds
                        setTimeout(() => {{
                            window.close();
                        }}, 2000);
                    }} else {{
                        errorDiv.textContent = '❌ ' + data.detail;
                        errorDiv.style.display = 'block';
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Authenticate';
                    }}
                }} catch (error) {{
                    errorDiv.textContent = '❌ Network error: ' + error.message;
                    errorDiv.style.display = 'block';
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Authenticate';
                }}
            }});
        </script>
    </body>
    </html>
    """)


@app.post("/auth/{nonce}")
async def complete_auth(nonce: str, request: Request):
    """Complete authentication with API key."""
    try:
        data = await request.json()
        api_key = data.get('api_key', '').strip()
        
        if not api_key or not api_key.startswith('sk-'):
            raise HTTPException(
                status_code=400,
                detail="Invalid API key format"
            )
        
        # Validate the API key with SkyFi
        try:
            test_client = SkyFiClient()
            test_client.config.api_key = api_key
            test_client._create_client()
            
            async with test_client:
                user_info = await test_client.get_user()
            
            email = user_info.get('email', 'Unknown')
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            raise HTTPException(
                status_code=401,
                detail="Invalid API key - authentication with SkyFi failed"
            )
        
        # Complete the authentication
        if not nonce_auth.complete_auth(nonce, api_key):
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired authentication link"
            )
        
        return JSONResponse({
            "status": "success",
            "message": f"Successfully authenticated as {email}. You can now close this window and return to Claude."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication failed"
        )