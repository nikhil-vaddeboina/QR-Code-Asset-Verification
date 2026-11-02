FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5013

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5013

# Create the schema and initial admin account, then serve the Flask app.
CMD ["sh", "-c", "flask --app app init-db && waitress-serve --listen=0.0.0.0:${PORT:-5013} --call app:create_app"]
