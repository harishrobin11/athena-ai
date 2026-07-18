# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir --default-timeout=1000 -r requirements.txt
# Ensure scripts in .local are usable for spacy download:
ENV PATH=/root/.local/bin:$PATH
RUN python -m spacy download en_core_web_sm

# Stage 2: Production
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

# Ensure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
