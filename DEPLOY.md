# AutoCV — Deploy Guide
# Estimated time: 45 minutes

## ─── STEP 1: Supabase Setup (10 min) ───────────────────

1. Go to https://supabase.com → New project
2. Note your Project URL and anon/service keys
3. Go to SQL Editor → paste entire contents of backend/schema.sql → Run
4. Go to Authentication → Providers → Enable Google
   - Add OAuth credentials from Google Cloud Console
   - Authorized redirect URI: https://xxx.supabase.co/auth/v1/callback

## ─── STEP 2: Stripe Setup (10 min) ─────────────────────

1. Go to https://stripe.com → Dashboard
2. Create two products:
   Product 1: "AutoCV Single"
     → Price: $19.00 USD, one-time
     → Copy the Price ID → paste into .env as STRIPE_PRICE_SINGLE
   Product 2: "AutoCV Pro"
     → Price: $29.00 USD, recurring monthly
     → Copy the Price ID → paste into .env as STRIPE_PRICE_PRO
3. Get your Secret Key (sk_live_...) → STRIPE_SECRET_KEY
4. Webhook setup: come back after Step 3 (need Render URL first)

## ─── STEP 3: Deploy Backend to Render (10 min) ──────────

1. Push the /backend folder to a GitHub repo
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Settings:
   - Root directory: (leave blank or set to backend/)
   - Build command: pip install -r requirements.txt
   - Start command: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2
5. Add Environment Variables (from your .env.example):
   SECRET_KEY          → click "Generate" in Render
   ANTHROPIC_API_KEY   → sk-ant-...
   STRIPE_SECRET_KEY   → sk_live_...
   STRIPE_PRICE_SINGLE → price_...
   STRIPE_PRICE_PRO    → price_...
   SUPABASE_URL        → https://xxx.supabase.co
   SUPABASE_SERVICE_KEY→ eyJ...
   FRONTEND_URL        → (set after Step 4)
6. Deploy → note your URL: https://autocv-backend.onrender.com

## ─── STEP 4: Deploy Frontend to Vercel (10 min) ─────────

1. Push the /frontend folder to a GitHub repo
2. Go to https://vercel.com → New Project → Import repo
3. Framework: Other (plain HTML)
4. Root directory: frontend/
5. No build command needed
6. Deploy → note your URL: https://autocv.vercel.app

## ─── STEP 5: Wire everything together (5 min) ───────────

1. Update frontend/static/js/config.js:
   window.RESUMEAI_API_URL = 'https://autocv-backend.onrender.com/api';

2. In Render dashboard → update FRONTEND_URL env var:
   https://autocv.vercel.app

3. In Stripe Dashboard → Webhooks → Add endpoint:
   URL: https://autocv-backend.onrender.com/api/webhook
   Events to listen for:
     - checkout.session.completed
     - customer.subscription.deleted
   Copy the Webhook Signing Secret → add as STRIPE_WEBHOOK_SECRET in Render

4. In Supabase → Authentication → URL Configuration:
   Site URL: https://autocv.vercel.app
   Redirect URLs: https://autocv.vercel.app/*

## ─── STEP 6: Test the full flow ─────────────────────────

[ ] Landing page loads at your Vercel URL
[ ] "Continue with Google" opens Google OAuth
[ ] After login → redirects to /pages/welcome.html
[ ] Upload a PDF resume + paste a job description
[ ] Click "Analyze My Resume Free" → score appears
[ ] Click "Optimize Now" → redirects to Stripe checkout
[ ] Use test card: 4242 4242 4242 4242, exp 12/26, CVC 123
[ ] After payment → /pages/payment-success.html animates
[ ] Results appear at /pages/results.html
[ ] Download PDF and DOCX both work
[ ] /pages/account.html shows user info

## ─── STEP 7: Go live checklist ──────────────────────────

[ ] Switch Stripe from test mode to live mode (swap sk_test → sk_live keys)
[ ] Set up custom domain in Vercel
[ ] Update FRONTEND_URL in Render to custom domain
[ ] Update Stripe webhook URL to custom domain
[ ] Update Supabase redirect URLs to custom domain
[ ] Add Privacy Policy and Terms links verified working
[ ] Test payment with real card (refund immediately after)

## ─── Local Development ───────────────────────────────────

Backend:
  cd backend
  cp .env.example .env
  # Fill in .env values
  pip install -r requirements.txt
  python app.py
  # Runs at http://localhost:5000

Frontend:
  cd frontend
  # Edit static/js/config.js → set API URL to http://localhost:5000/api
  # Open with Live Server (VS Code) or:
  python -m http.server 3000
  # Open http://localhost:3000

Stripe webhooks locally (requires Stripe CLI):
  stripe login
  stripe listen --forward-to localhost:5000/api/webhook
  # Copy the webhook secret → set as STRIPE_WEBHOOK_SECRET in .env
