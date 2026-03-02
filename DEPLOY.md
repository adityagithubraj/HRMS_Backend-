# Deploy HRMS Backend to Render

## 1. Push your code to GitHub

Make sure your project is in a Git repo and pushed to GitHub (or GitLab/Bitbucket). **Do not push `.env`** — add it to `.gitignore` so your MongoDB URL stays private.

```bash
# If .env is not ignored yet:
echo ".env" >> .gitignore
git add .
git commit -m "Add Render deployment config"
git push origin main
```

## 2. Create a Web Service on Render

1. Go to [render.com](https://render.com) and sign in (or sign up with GitHub).
2. Click **Dashboard** → **New** → **Web Service**.
3. Connect your repository: choose the **HRMS_Backend-** repo and click **Connect**.

## 3. Configure the service

Use these settings (Render may prefill some from `render.yaml`):

| Setting | Value |
|--------|--------|
| **Name** | `hrms-backend` (or any name) |
| **Region** | Choose closest to your users |
| **Branch** | `main` (or your default branch) |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

## 4. Add environment variables

In the same screen, open **Environment** and add:

| Key | Value | Secret? |
|-----|--------|--------|
| `MONGODB_URI` | Your MongoDB Atlas connection string (e.g. `mongodb+srv://user:pass@cluster0.xxx.mongodb.net/`) | Yes |
| `MONGODB_DB_NAME` | `hrms_lite` | No |

Paste your real MongoDB URL from `.env` into `MONGODB_URI` and mark it as **Secret** so it’s hidden in the dashboard.

## 5. Deploy

Click **Create Web Service**. Render will:

- Clone your repo
- Run `pip install -r requirements.txt`
- Start the app with the start command above

When the build finishes, your API will be live at:

**`https://hrms-backend.onrender.com`** (or the URL Render shows).

- Root: `GET https://<your-app>.onrender.com/` → `{"message": "HRMS Lite API is running"}`
- API: `https://<your-app>.onrender.com/api/...`

## 6. (Optional) Use Blueprint instead

If you use **New → Blueprint** and point Render at this repo, it will read `render.yaml` and create the web service. You still must set **MONGODB_URI** in the Dashboard (Environment) because it’s not stored in the repo.

---

## Notes

- **Free tier:** The service may spin down after 15 minutes of no traffic; the first request after that can be slow (cold start).
- **MongoDB:** Use your existing MongoDB Atlas URL; no need to run MongoDB on Render.
- **CORS:** The app allows all origins (`allow_origins=["*"]`). For production, restrict this to your frontend domain in `app/main.py`.
