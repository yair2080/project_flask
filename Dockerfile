# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN apt-get update && apt-get install -y wait-for-it curl

CMD ["wait-for-it", "db:5432", "--", "flask", "run", "--host=0.0.0.0"]