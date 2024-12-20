FROM python:3.12-slim

WORKDIR /app

COPY . ./

RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
