FROM python:3.8

WORKDIR /app

RUN apt-get update
RUN apt-get install tesseract-ocr ffmpeg libsm6 libxext6 poppler-utils -y

ENV SQLALCHEMY_TRACK_MODIFICATIONS 0

COPY requirements.txt .
RUN pip install -r requirements.txt

# COPY . /app
CMD python -m flask run --host=0.0.0.0

