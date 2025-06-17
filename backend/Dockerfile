FROM python:3.13.5-slim

WORKDIR /code

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


