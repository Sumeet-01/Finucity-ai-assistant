import os
import requests
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")

ROOT = Path(__file__).parent

# 1) Check template files
templates = [
    ROOT / "finucity" / "templates" / "auth" / "login.html",
    ROOT / "finucity" / "templates" / "auth" / "auth_callback.html",
]
missing = [str(p) for p in templates if not p.exists()]
print("Template files missing:" if missing else "All template files present.")
for m in missing:
    print("  -", m)

# 2) Check required environment variables
required_env = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_KEY",
    "SUPABASE_JWT_SECRET",
]
env_missing = [k for k in required_env if not os.getenv(k)]
print("Missing env vars:" if env_missing else "All required env vars present.")
for k in env_missing:
    print("  -", k)

# 3) Check HTTP endpoints
BASE = "http://localhost:3000"
endpoints = [
    ("/auth/login", 200, "login page"),
    ("/api/health", 200, "health"),
    ("/api/stats", 200, "stats"),
]

for path, expected, label in endpoints:
    url = BASE + path
    try:
        r = requests.get(url, timeout=5)
        status_ok = (r.status_code == expected)
        print(f"{label:12s} {url:40s} -> {r.status_code} ({'OK' if status_ok else 'FAIL'})")
        if not status_ok:
            print("  Body:", r.text[:300])
    except Exception as e:
        print(f"{label:12s} {url:40s} -> ERROR {e}")

# 4) Optional: quick content check for login page
try:
    r = requests.get(BASE + "/auth/login", timeout=5)
    if r.ok:
        if "{{ SUPABASE_URL }}" in r.text or "supabase.createClient" in r.text:
            print("Login page renders with Supabase placeholders/JS.")
        else:
            print("Login page rendered but did not detect Supabase JS markers.")
except Exception:
    pass