# ResumeAI — Complete Codebase

## Structure
```
resumeai-backend/     → Flask API (deploy to Render)
resumeai-frontend/    → HTML/CSS/JS (deploy to Vercel)
```

## Quick Start

### Backend
```bash
cd resumeai-backend
cp .env.example .env        # fill in your keys
pip install -r requirements.txt
python app.py               # runs on localhost:5000
```

### Frontend
Open index.html in browser, or:
```bash
cd resumeai-frontend
npx serve .                 # static server on localhost:3000
```

## Keys You Need
1. **Supabase** — create project at supabase.com, run schema.sql, enable Google OAuth
2. **Stripe** — create account, add 2 products ($19 one-time, $29/mo subscription)
3. **Anthropic** — get API key from console.anthropic.com
4. Update SUPABASE_URL and SUPABASE_ANON_KEY in every HTML file (search for YOUR_SUPABASE_URL)
5. Update window.API_BASE in HTML files to your Render backend URL

## Deploy
- Backend → render.com (use render.yaml, set env vars in dashboard)
- Frontend → vercel.com (drag and drop the frontend folder)
- Set Stripe webhook → your-render-url/api/webhook
