FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./

RUN pip install uv
RUN uv add -r requirements.txt
RUN pip install -r requirements.txt

COPY . .
