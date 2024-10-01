# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.bun/bin:/home/app/.local/bin:/opt/venv/bin:$PATH"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

# Copy project files
COPY . .

# Install Python dependencies
RUN python -m venv /opt/venv
RUN pip install --no-cache-dir -r requirements.txt

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash

# Install Node.js dependencies and build CSS
RUN bun install
RUN bun run tailwindcss -i ./static/css/tailwind.css -o ./static/css/dist/output.css

FROM builder AS runner

RUN addgroup --system --gid 1001 app && adduser --system --uid 1001 app

COPY --from=builder --chown=app:app /app/app.py ./app.py
COPY --from=builder --chown=app:app /app/templates ./templates
COPY --from=builder --chown=app:app /app/static/css/dist ./static/css/dist
COPY --from=builder --chown=app:app /opt/venv /opt/venv

USER app

# Expose port
EXPOSE 3000

# Run the application
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:3000"]