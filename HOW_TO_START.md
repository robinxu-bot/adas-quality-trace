# How to Start PQRETS V6.2

## Prerequisites

- Rancher Desktop (Docker) must be running
- Node.js must be installed

---

## Every Time You Start the System

You need **two terminal windows** open at the same time.

---

### Terminal 1 — Start Backend + Database

Open PowerShell, go to the project folder:

```powershell
cd C:\Users\RobinXu(WovenbyToyot\Desktop\WR\adas-quality-trace
docker compose -f docker-compose.dev.yml up
```

Wait until you see:
```
INFO:     Application startup complete.
```

**Keep this terminal open.** Do not close it.

---

### Terminal 2 — Start Frontend

Open a second PowerShell window:

```powershell
cd C:\Users\RobinXu(WovenbyToyot\Desktop\WR\adas-quality-trace\frontend
npm run dev
```

Wait until you see:
```
VITE v5.4.21  ready in 380 ms
➜  Local:   http://localhost:5174/
```

**Keep this terminal open.** Do not close it.

---

### Open the App

Go to: **http://localhost:5174**

> Note: Port 5173 is used by another app on this machine. Always use **5174**.

---

## First Time Only — Seed Demo Data

After starting for the first time (or after a full reset), run this once in any terminal:

```powershell
curl.exe -X POST http://localhost:9000/api/v1/admin/seed-demo
```

You should see:
```json
{"seeded":2,"skipped":0,"projects":["PRJ_ADAS_L2_001","PRJ_ADAS_L3_002"]}
```

---

## Stopping the System

- **Terminal 1:** Press `Ctrl+C` to stop backend + database
- **Terminal 2:** Press `Ctrl+C` to stop frontend

---

## Full Reset (Delete All Data and Start Fresh)

```powershell
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build
```

Then seed demo data again:
```powershell
curl.exe -X POST http://localhost:9000/api/v1/admin/seed-demo
```

---

## Useful URLs

| URL | Purpose |
|---|---|
| http://localhost:5174 | Main application |
| http://localhost:9000/docs | Backend API documentation (Swagger UI) |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Page shows "无法访问此网站" | Frontend is not running. Go to Terminal 2 and run `npm run dev` |
| Page shows wrong app (Static Docker V5.2) | Wrong port. Use **http://localhost:5174** not 5173 |
| "Failed to load common model" error on page | Backend is not running. Go to Terminal 1 and run `docker compose -f docker-compose.dev.yml up` |
| Backend shows port already allocated error | Run `docker compose -f docker-compose.dev.yml down -v` first, then start again |
