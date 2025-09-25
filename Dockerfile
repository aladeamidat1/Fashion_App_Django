# Use Python 3.13 slim as base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \n    && apt-get install -y --no-install-recommends \n        build-essential \n        default-libmysqlclient-dev \n        pkg-config \n        curl \n    && rm -rf /var/lib/apt/lists/*

# Install UV for faster Python package management
RUN pip install uv

# Copy pyproject.toml and uv.lock first for better caching
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy project
COPY . .

# Create a non-root user
RUN addgroup --system --gid 1001 django \\n    && adduser --system --uid 1001 --ingroup django django

# Change ownership of the app directory
RUN chown -R django:django /app

# Switch to the django user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\n    CMD curl -f http://localhost:8000/api/ || exit 1

# Run the application
CMD [\"uv\", \"run\", \"uvicorn\", \"fashion_app.asgi:application\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]