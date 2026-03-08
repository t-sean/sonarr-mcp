# Use uv-based Python image for fast dependency installation
FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv sync --no-dev

# Final runtime image
FROM python:3.14-alpine

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY main.py tools.py ./

# Set PATH to use venv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
CMD ["python", "main.py"]
