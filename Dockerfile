FROM python:3.10-slim

RUN apt-get update && pip3 install pypandoc_binary pillow

COPY app/ app/

WORKDIR /app

#CMD ["python3", "createhtml.py"]