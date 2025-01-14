FROM python:3.10

RUN apt-get update && apt-get install -y calibre && pip3 install pillow pytz flask

RUN mkdir -p /output
RUN chmod 777 /output

COPY app /app

WORKDIR /app

CMD ["python", "app.py"]

