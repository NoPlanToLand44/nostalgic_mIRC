FROM python:3.90-slim

WORKDIR /app

COPY ./requirements ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./src ./src
expose 8000

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]