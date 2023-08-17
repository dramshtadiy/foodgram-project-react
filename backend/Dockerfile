FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip 
RUN pip3 install -r requirements.txt --no-cache-dir

COPY foodgram/ .

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:7000" ]