FROM python:3.11-alpine

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip pipenv && \
    pipenv install --system --deploy --ignore-pipfile

# Requires secret.py to be mounted at /app/secret.py
CMD ["python", "main.py"]
