FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# In production this should run behind a process manager / multiple workers;
# for local/pilot this single-worker form is sufficient and simplest.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
