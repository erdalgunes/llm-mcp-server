FROM python:3.11-alpine

RUN apk add --no-cache gcc musl-dev

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3000

CMD ["python", "server.py"]