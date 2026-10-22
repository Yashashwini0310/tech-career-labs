FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
# 2 worker processes, like a small production deployment
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "30", "app:app"]
