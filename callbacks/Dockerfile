FROM python:3.9

WORKDIR /code

COPY requirements.txt .

RUN pip install -U --force-reinstall setuptools wheel

RUN pip install -r requirements.txt

COPY src/ .

CMD ["python", "main.py"]