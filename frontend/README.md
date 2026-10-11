# Competency Twin frontend

React and TypeScript client for the Competency Twin learning application.

## Run locally

From this folder:

```powershell
npm install
npm run dev
```

The development server runs at `http://localhost:5173` and forwards API calls to the local backend at `http://localhost:8000`.

## Configuration

Use a `frontend/.env` file only when the frontend needs to call an API on a different origin:

```env
VITE_API_BASE_URL=https://api.example.com
```

When this variable is omitted, the client uses relative API paths, which keeps the Vite development proxy working. The backend must allow the frontend origin through its `CORS_ORIGINS` setting when the two applications are hosted apart.

## Verify a production build

```powershell
npm run build
```

The build output is written to `dist/`.
