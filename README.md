# AllWays Ottawa

AI-powered accessible navigation for Ottawa.

## Quick Start

### 1. Clone and enter the repo
```bash
git clone https://github.com/YOUR-USERNAME/allways-ottawa.git
cd allways-ottawa
```

### 2. Start the database
```bash
docker-compose up -d postgres
```

### 3. Start the backend
```bash
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
python app.py
```

### 4. Start the frontend
```bash
cd frontend && npm install && npm start
```

## Tech Stack
- Backend: Python 3.11 + Flask
- Database: PostgreSQL 15 + PostGIS 3
- Routing: OSRM (Docker)
- AI: OpenAI API (gpt-4o-mini)
- Frontend: React 18 + Leaflet
