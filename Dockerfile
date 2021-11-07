FROM python:3.8-slim-buster
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install postgresql
RUN pip3 install requests
COPY . /bot
CMD python3 /bot/main.py
