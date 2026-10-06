# Bharath German Practice

A Flask + SQLite German A1/A2 vocabulary and listening practice app.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
py app.py
```

Open `http://127.0.0.1:5000`. The database is created and seeded automatically on first launch with 2,000 vocabulary records across the 40 requested topics.

Audio uses the browser Web Speech API with a German `de-DE` utterance and prefers an installed German voice. Browser speech permissions and available voices vary by operating system.

## Free Vercel deployment

This project includes `vercel.json` and `api/index.py` for Vercel's Python runtime.

```powershell
npx vercel login
npx vercel --prod
```

SQLite data on Vercel is ephemeral because serverless filesystems are not
persistent. The vocabulary is recreated automatically per serverless instance.
For persistent attempts and progress, connect a hosted database such as
Neon/Postgres or Turso/SQLite after deployment.
