# VisionInspect AI — Frontend (Week 1)

## Setup

```bash
npm install
cp .env.local.example .env.local
```

Make sure `.env.local` points at your running backend:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Run

```bash
npm run dev
```

Visit http://localhost:3000 — it redirects to `/login`.

## Pages

- `/login` — sign in, stores JWT in localStorage
- `/signup` — create account (inspector / admin role)
- `/dashboard` — upload a product image + view recent uploads (protected, redirects to `/login` if not signed in)

## Requirements

The backend (`visioninspect-backend`) must be running on port 8000, with at least one row in the `categories` table (so `category_id` on upload doesn't fail).
