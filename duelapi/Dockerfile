FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

COPY requirements.txt .

RUN pip install -U --force-reinstall setuptools wheel

RUN pip install -r requirements.txt

COPY ./app /app