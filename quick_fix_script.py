#!/usr/bin/env python3
"""
Quick Fix Script: Add missing Dockerfile for frontend
"""

import os
from pathlib import Path

def create_missing_dockerfiles():
    """Create missing Dockerfile for frontend"""
    
    target_dir = Path("agentic-rag-web")
    
    if not target_dir.exists():
        print("❌ agentic-rag-web directory not found")
        print("Please run the migration script first")
        return False
    
    print("🔧 Adding missing Dockerfile for frontend...")
    
    # Frontend Dockerfile
    frontend_dockerfile = '''FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]'''
    
    # Backend Dockerfile (in case it's missing too)
    backend_dockerfile = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]'''
    
    # Check and create frontend Dockerfile
    frontend_docker_path = target_dir / "frontend" / "Dockerfile"
    if not frontend_docker_path.exists():
        with open(frontend_docker_path, 'w') as f:
            f.write(frontend_dockerfile)
        print("✅ Created frontend/Dockerfile")
    
    # Check and create backend Dockerfile
    backend_docker_path = target_dir / "backend" / "Dockerfile"
    if not backend_docker_path.exists():
        with open(backend_docker_path, 'w') as f:
            f.write(backend_dockerfile)
        print("✅ Created backend/Dockerfile")
    
    # Also create a simpler docker-compose.yml that uses local development
    simple_docker_compose = '''version: '3.8'
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
    
    # Update docker-compose.yml
    docker_compose_path = target_dir / "docker-compose.yml"
    with open(docker_compose_path, 'w') as f:
        f.write(simple_docker_compose)
    print("✅ Updated docker-compose.yml")
    
    print("\n🚀 Files created successfully!")
    return True

def main():
    print("🔧 Quick Fix: Adding missing Docker files...")
    
    if create_missing_dockerfiles():
        print("\n✅ Fix completed!")
        print("\n🚀 Now try:")
        print("cd agentic-rag-web")
        print("docker-compose up -d")
    else:
        print("\n❌ Fix failed")

if __name__ == "__main__":
    main()