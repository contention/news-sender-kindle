FROM python:3.10-slim

RUN apt-get update && apt-get install -y calibre && pip3 install pypandoc_binary pillow pytz tzlocal

COPY app/ app/

WORKDIR /app

CMD ["python3", "createhtml.py"]