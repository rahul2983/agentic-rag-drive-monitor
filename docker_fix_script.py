#!/usr/bin/env python3
"""
Docker Fix Script: Fix npm ci issue by updating Dockerfile
"""

import os
from pathlib import Path

def fix_docker_issues():
    """Fix Docker build issues"""
    
    target_dir = Path("agentic-rag-web")
    
    if not target_dir.exists():
        print("❌ agentic-rag-web directory not found")
        return False
    
    print("🔧 Fixing Docker build issues...")
    
    # Updated frontend Dockerfile (use npm install instead of npm ci)
    frontend_dockerfile = '''FROM node:18-alpine as build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config for SPA
RUN echo 'server { listen 80; location / { try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'''
    
    # Updated backend Dockerfile 
    backend_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'''
    
    # Development-friendly docker-compose.yml
    docker_compose = '''version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: drive_monitor
      POSTGRES_USER: postgres  
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/drive_monitor
      REDIS_URL: redis://redis:6379
      SECRET_KEY: dev-secret-key-change-in-production
      CORS_ORIGINS: http://localhost:3000
    depends_on:
      - postgres
      - redis
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend  
    restart: unless-stopped

volumes:
  postgres_data:'''
    
    # Write updated files
    files_to_update = {
        "frontend/Dockerfile": frontend_dockerfile,
        "backend/Dockerfile": backend_dockerfile,
        "docker-compose.yml": docker_compose
    }
    
    for file_path, content in files_to_update.items():
        full_path = target_dir / file_path
        with open(full_path, 'w') as f:
            f.write(content)
        print(f"✅ Updated {file_path}")
    
    # Also create a development script for easier local development
    dev_script = '''#!/bin/bash
# Development startup script

echo "🚀 Starting Agentic RAG Drive Monitor in development mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down > /dev/null 2>&1

# Start services
echo "📦 Starting database services..."
docker-compose up -d postgres redis

echo "⏳ Waiting for database to be ready..."
sleep 5

echo "🔧 Starting backend..."
docker-compose up -d backend

echo "🎨 Starting frontend..."
docker-compose up -d frontend

echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Your application is available at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "📊 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
'''
    
    dev_script_path = target_dir / "start-dev.sh"
    with open(dev_script_path, 'w') as f:
        f.write(dev_script)
    
    # Make it executable
    try:
        os.chmod(dev_script_path, 0o755)
        print("✅ Created start-dev.sh script")
    except:
        print("✅ Created start-dev.sh script (you may need to make it executable)")
    
    print("\n🚀 Docker fixes applied!")
    return True

def main():
    print("🔧 Fixing Docker build issues...")
    
    if fix_docker_issues():
        print("\n✅ All fixes applied!")
        print("\n🚀 Now try one of these options:")
        print("\nOption 1 - Use Docker:")
        print("cd agentic-rag-web")
        print("docker-compose down  # Clean up")
        print("docker-compose up -d # Start fresh")
        print("\nOption 2 - Use development script:")
        print("cd agentic-rag-web") 
        print("./start-dev.sh")
        print("\nOption 3 - Manual development (no Docker):")
        print("cd agentic-rag-web/backend && pip install -r requirements.txt && python -m app.main &")
        print("cd agentic-rag-web/frontend && npm install && npm run dev")
    else:
        print("\n❌ Fix failed")

if __name__ == "__main__":
    main()