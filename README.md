# Bharath German Practice

A Flask + PostgreSQL German A1/A2 vocabulary and listening practice app.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Open `http://127.0.0.1:5000`. Without `DATABASE_URL`, local development uses SQLite.
With `DATABASE_URL` (or the Supabase/Vercel-provided `DATABASE_POSTGRES_URL`),
the app uses PostgreSQL and initializes the persistent schema
and seed data automatically on first start.

Audio uses the browser Web Speech API with a German `de-DE` utterance and prefers an installed German voice. Browser speech permissions and available voices vary by operating system.

## Free Vercel deployment

This project includes `vercel.json` and `api/index.py` for Vercel's Python runtime.

```powershell
npx vercel login
npx vercel --prod
```

## Persistent PostgreSQL setup

Create a free PostgreSQL database with a provider such as Neon or Supabase, then
Set the connection string as `DATABASE_URL` (primary). If your integration
provides `DATABASE_POSTGRES_URL`, it is accepted as a fallback. Never commit
either value.

```powershell
$env:DATABASE_URL = "postgresql://user:password@host/database?sslmode=require"
py init_db.py
py seed_database.py
py app.py
```

The seed is safe to run repeatedly: topics, vocabulary, words, and listening
questions use PostgreSQL conflict-safe inserts.

To migrate an existing local SQLite database before switching Vercel over:

```powershell
$env:DATABASE_URL = "postgresql://user:password@host/database?sslmode=require"
py migrate_sqlite_to_postgres.py
```

For Vercel:

```powershell
npx vercel env add DATABASE_URL production
npx vercel --prod --name german-practise
```

Use the same `DATABASE_URL` for Preview if preview deployments should share the
same persistent data. Existing browser audio continues to use the Web Speech API.
