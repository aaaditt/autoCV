// ── AutoCV Configuration ─────────────────────────────────
// Sets window globals BEFORE app.js loads
window.RESUMEAI_API_URL = window.RESUMEAI_API_URL || 'https://resumeai-backend-qta5.onrender.com/api';

// Supabase Auth Configuration (PUBLIC keys - safe for frontend)
window.SUPABASE_URL = 'https://zegytszmdcpwctwomqge.supabase.co';
window.SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InplZ3l0c3ptZGNwd2N0d29tcWdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzNDQxODYsImV4cCI6MjA5MDkyMDE4Nn0.Mq6TtNYLVyUtsj9D_ZVlaAs8ph3_TNirA8xrAFlZSjQ';

console.log("AutoCV Config Loaded | API:", window.RESUMEAI_API_URL);
