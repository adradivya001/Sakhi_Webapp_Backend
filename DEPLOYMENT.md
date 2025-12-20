# Quick Deployment Steps

## On Your Windows Machine

1. **Ensure all files are ready:**
   - ✅ Dockerfile
   - ✅ docker-compose.yml
   - ✅ requirements.txt
   - ✅ .dockerignore
   - ⚠️  .env (prepare this separately)

## On Your Server (via PuTTY)

### First Time Setup

```bash
# 1. Navigate to your directory
cd /home/username

# 2. Transfer files (choose one method)
# Method A: Using Git
git clone <your-repo-url>
cd Sakhi-Whatsapp-Backend

# Method B: After using SCP/WinSCP from Windows
cd Sakhi-Whatsapp-Backend

# 3. Create .env file
nano .env
# Paste your environment variables, save (Ctrl+X, Y, Enter)

# 4. Build and run
docker-compose up -d --build

# 5. Check if running
docker ps

# 6. View logs
docker logs -f sakhi-whatsapp-backend

# 7. Test
curl http://localhost:8100/
```

### Updating After Changes

```bash
cd /home/username/Sakhi-Whatsapp-Backend
git pull  # if using Git
docker-compose up -d --build
docker logs -f sakhi-whatsapp-backend
```

### Essential Commands

| Action | Command |
|--------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Restart | `docker-compose restart` |
| Logs | `docker logs -f sakhi-whatsapp-backend` |
| Rebuild | `docker-compose up -d --build` |
| Status | `docker ps` |

## Environment Variables (.env)

Make sure your .env file includes:

```env
SUPABASE_URL=your_url
SUPABASE_SERVICE_ROLE=your_key
OPENAI_API_KEY=your_key
SLM_ENDPOINT=your_endpoint  # if using SLM
PORT=8100
```

## Firewall (if needed)

```bash
sudo ufw allow 8100
sudo ufw status
```

## Access Your API

- Local: `http://localhost:8100/`
- External: `http://your-server-ip:8100/`
- With domain: `http://your-domain.com/` (if using Nginx)
