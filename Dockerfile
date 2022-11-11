FROM python:3.9

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
RUN apt-get update
COPY requirements.txt /usr/src/app/
RUN mkdir -p /usr/src/app/media/images
RUN pip install --no-cache-dir -r requirements.txt
COPY . /usr/src/app
