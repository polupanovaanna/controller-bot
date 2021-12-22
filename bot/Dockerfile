FROM python:3.8-slim-buster
RUN apt-get update && apt-get -y upgrade
RUN pip3 install requests
COPY . /bot
CMD echo "start" && python3 /bot/main.py
