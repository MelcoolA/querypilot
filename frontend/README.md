# QueryPilot web UI

Next.js + TypeScript front end for the QueryPilot agent.

```bash
# In the project root: start the API on http://localhost:8000
make api

# In this folder: start the UI on http://localhost:3000
npm install
npm run dev
```

The UI calls the API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
