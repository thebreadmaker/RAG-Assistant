# Refactored YodeL - ngrok Setup & Port Forwarding Guide

This guide covers setting up ngrok to forward your local Ollama instance to Codespaces.

---

## Part 1: Initial ngrok Setup (One-Time)

### What is ngrok?
ngrok creates a secure tunnel from your local machine (Windows) to the internet. This allows your Codespaces environment to reach Ollama running on your Windows machine.

**Flow:**
```
Windows Machine (Ollama on localhost:11434)
           ↓
       ngrok tunnel
           ↓
   Public HTTPS URL
           ↓
Codespaces Backend (connects via https)
```

---

## Section 1.1: Install ngrok on Windows

### Step 1: Download ngrok
1. Go to https://ngrok.com/download
2. Click "Windows" (choose 64-bit if you have modern Windows)
3. Extract the ZIP file to a folder (e.g., `C:\ngrok`)

### Step 2: Verify Installation
Open **Command Prompt** or **PowerShell** and run:
```powershell
cd C:\ngrok
ngrok version
```

**Expected output:**
```
ngrok version 3.x.x
```

### Step 3: Create ngrok Account (Optional but Recommended)
1. Go to https://dashboard.ngrok.com
2. Sign up for free account
3. Go to **Auth** → copy your authtoken
4. Run in terminal:
```powershell
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

**Benefits of authenticated ngrok:**
- Longer session timeouts (1 hour vs 2 hours)
- No "ngrok has opened" browser warning
- Better reliability

---

## Section 1.2: Setup Traffic Policy (Windows)

### Why a Traffic Policy?
Ollama expects `Host: localhost` in requests. Without the policy, it rejects requests from the ngrok tunnel.

### Step 1: Create Policy File
In `C:\ngrok\` folder, create a file named `ollama.yaml`:

**File: `C:\ngrok\ollama.yaml`**
```yaml
on_http_request:
  - actions:
      - type: add-headers
        config:
          headers:
            host: localhost
```

**Save the file** (make sure it's `.yaml` not `.yaml.txt`)

### Step 2: Verify File Creation
```powershell
cd C:\ngrok
Get-Content ollama.yaml
```

Should output the YAML content above.

---

## Section 1.3: Get a Static ngrok Domain (Optional but Highly Recommended)

### Why Static Domain?
Every time ngrok restarts, you get a new URL. A static domain stays the same.

### Step 1: Create Paid Account or Use Free Tier
- **Free users:** Get 1 free static domain
- **Paid users:** Get multiple domains

### Step 2: Reserve Domain
1. Go to https://dashboard.ngrok.com/cloud-edge/domains
2. Click **Create Domain**
3. Choose a name (e.g., `my-ollama-tunnel`)
4. You'll get: `https://my-ollama-tunnel.ngrok.io`

### Step 3: Update Start Command
Use the domain in your ngrok start command (see next section).

---

## Part 2: Starting ngrok (Every Session)

### Two Options:

#### Option A: Using Static Domain (Recommended)
```powershell
cd C:\ngrok
ngrok http 11434 --domain=my-ollama-tunnel.ngrok.io --traffic-policy-file ollama.yaml
```

Replace `my-ollama-tunnel` with your reserved domain name.

#### Option B: Without Static Domain (Gets New URL Each Time)
```powershell
cd C:\ngrok
ngrok http 11434 --traffic-policy-file ollama.yaml
```

### Expected Output
```
ngrok                                                 (Ctrl+C to quit)

Add connectivity to localhost:11434 with ngrok

Session Status                online
Account                       your-email@gmail.com
Version                       3.x.x
Region                        us
Hostname                      my-ollama-tunnel.ngrok.io
Forwarding                    https://my-ollama-tunnel.ngrok.io -> http://localhost:11434

Connections                   ttl     opn     rt1     rt5     p50     p95
                              0       0       0.00    0.00    0.00    0.00
```

**Key Line:** `Forwarding: https://my-ollama-tunnel.ngrok.io -> http://localhost:11434`

### Copy the HTTPS URL
This is your tunnel URL: `https://my-ollama-tunnel.ngrok.io`

---

## Section 2.1: Test ngrok Connection (Windows)

### Step 1: Open New Command Prompt
While ngrok is still running in the first terminal...

### Step 2: Test the Tunnel
```powershell
curl https://my-ollama-tunnel.ngrok.io/api/tags
```

Replace URL with your actual ngrok domain.

**Expected output:**
```json
{
  "models": [
    {
      "name": "llama3.2:3b:latest",
      "modified_at": "2024-01-15T10:30:00.000Z",
      ...
    }
  ]
}
```

If you get an error, troubleshoot below.

---

## Part 3: Connect Codespaces to ngrok

### Section 3.1: Update Backend `.env` File

**File: `refactored-yodel/backend/.env`**

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# LLM Configuration - NOW POINTING TO NGROK TUNNEL
OLLAMA_HOST=https://my-ollama-tunnel.ngrok.io
OLLAMA_MODEL=llama3.2:3b

# Cache Configuration
CUSTOMER_CACHE_TTL=86400
QUERY_CACHE_TTL=1800

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

**Replace `my-ollama-tunnel.ngrok.io` with YOUR actual ngrok URL**

### Section 3.2: Restart Backend

If backend is already running, stop it and restart:

```bash
# Press Ctrl+C to stop backend

# Restart with new configuration
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Section 3.3: Verify Connection

```bash
# Test health check (in new Codespaces terminal)
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "redis": true,
  "ollama": true
}
```

If `"ollama": false`, see troubleshooting below.

---

## Part 4: Daily Workflow

### Every Time You Start Working

**Terminal 1 - Windows (Keep Running):**
```powershell
# Ensure Ollama is running
ollama serve

# Keep it running in background
```

**Terminal 2 - Windows (Keep Running):**
```powershell
cd C:\ngrok
ngrok http 11434 --domain=my-ollama-tunnel.ngrok.io --traffic-policy-file ollama.yaml
```

**Terminal 3 - Codespaces:**
```bash
source venv/bin/activate
docker-compose up -d
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 4 - Codespaces:**
```bash
cd frontend
npm run dev
```

---

## Troubleshooting

### Issue: "Connection refused" when testing ngrok

**Cause:** Ollama not running or not on port 11434

**Solution:**
```powershell
# Check if Ollama is running
ollama serve

# Verify it's on port 11434
netstat -ano | findstr :11434

# If you see a process, Ollama is running
```

### Issue: ngrok connection works but backend says `"ollama": false`

**Cause:** HTTPS certificate issue or ngrok URL not in `.env`

**Solution:**
1. Check `.env` has correct URL:
   ```bash
   cat backend/.env | grep OLLAMA_HOST
   ```
   Should show: `OLLAMA_HOST=https://my-ollama-tunnel.ngrok.io`

2. Test from Codespaces terminal:
   ```bash
   curl https://my-ollama-tunnel.ngrok.io/api/tags
   ```
   Should return model list

3. If curl works but backend doesn't, restart backend:
   ```bash
   cd backend
   python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Issue: "Get new ngrok URL every time" - URLs keep changing

**Solution:** Use static domain (see Section 1.3)

Free accounts get 1 free static domain. Once set up, URL never changes.

### Issue: ngrok says "Too many connections" or "Rate limited"

**Cause:** Free tier ngrok has limits

**Solutions:**
- Create paid ngrok account for higher limits
- Reduce request frequency
- Create authenticated account (higher limits)

To authenticate:
```powershell
ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
```

### Issue: Traffic policy not working - still getting 502 errors

**Solution:** Verify traffic policy file exists and is correct:

```powershell
cd C:\ngrok
Get-Content ollama.yaml
```

Should output:
```
on_http_request:
  - actions:
      - type: add-headers
        config:
          headers:
            host: localhost
```

If wrong, delete and recreate the file.

### Issue: "SSL certificate verification failed"

**Cause:** Python requests library being strict about certificates

**Solution (last resort):** In `backend/departments/retail_digital/modules/general/generator.py`, modify the LLM call:

```python
response = requests.post(
    self.ollama_url, 
    json=payload, 
    timeout=120,
    verify=False  # Only if necessary
)
```

**Note:** This is not recommended for production but OK for development.

---

## Quick Reference

### Command Checklist

**Windows - Terminal 1 (Start once, leave running):**
```powershell
ollama serve
```

**Windows - Terminal 2 (Start once, leave running):**
```powershell
cd C:\ngrok
ngrok http 11434 --domain=YOUR_DOMAIN.ngrok.io --traffic-policy-file ollama.yaml
```

**Codespaces - Terminal 1:**
```bash
source venv/bin/activate
docker-compose up -d
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Codespaces - Terminal 2:**
```bash
cd frontend
npm run dev
```

### Files to Update/Create

| File | Action | Content |
|------|--------|---------|
| `C:\ngrok\ollama.yaml` | **CREATE** | Traffic policy YAML |
| `refactored-yodel/backend/.env` | **UPDATE** | Set `OLLAMA_HOST=https://YOUR_DOMAIN.ngrok.io` |

### URLs to Know

| Service | URL |
|---------|-----|
| ngrok Dashboard | https://dashboard.ngrok.com |
| Ollama (via ngrok) | `https://your-domain.ngrok.io` |
| Codespaces Backend | `http://localhost:8000` |
| Codespaces Frontend | `http://localhost:5173` |
| API Docs | `http://localhost:8000/docs` |

---

## Advanced: Updating ngrok Domain Without Restarting

If you need to change your ngrok domain without restarting the backend:

**On Windows (ngrok terminal):**
```powershell
# Stop ngrok (Ctrl+C)
# Start with new domain
ngrok http 11434 --domain=new-domain.ngrok.io --traffic-policy-file ollama.yaml
```

**On Codespaces:**
```bash
# Update .env
nano backend/.env
# Change OLLAMA_HOST=https://new-domain.ngrok.io

# Restart backend
# Press Ctrl+C
cd backend
python3 -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Security Notes

⚠️ **Important for Production:**
- ngrok URLs are publicly accessible - anyone with the URL can access Ollama
- For production, use authentication or firewall rules
- ngrok free tier is fine for development
- For production, consider:
  - VPN instead of ngrok
  - Authentication layer in Ollama
  - Firewall to restrict IPs

---

## Summary

1. **Install ngrok** on Windows
2. **Create traffic policy** (`ollama.yaml`)
3. **Reserve static domain** (optional but recommended)
4. **Start Ollama** on Windows
5. **Start ngrok tunnel** with domain
6. **Update Codespaces `.env`** with ngrok URL
7. **Test health check** in Codespaces
8. **Happy coding!** 🚀

