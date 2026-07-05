# Simple, production-ready image for the HRATIX Flask app.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer between builds
# unless requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application.
COPY . .

# Render/Railway/Dokploy all set PORT themselves; 8000 is just the local
# default when running the container directly (e.g. `docker run -p 8000:8000`).
ENV PORT=8000
EXPOSE 8000

# Gunicorn, not Flask's own dev server — this is the same production
# entrypoint used by every deployment path in DEPLOYMENT_GUIDE.md.
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT} --workers 2 --timeout 60"]
