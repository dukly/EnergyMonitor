FROM python:3.12-slim

WORKDIR /app

COPY src/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY src /app/src

CMD ["python", "src/main.py"]
