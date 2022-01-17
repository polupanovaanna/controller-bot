FROM python:3.8-slim-buster
RUN apt-get update && apt-get -y upgrade
RUN pip3 install requests
RUN python3 -m pip install -U matplotlib
RUN apt-get install -y python-pip
RUN apt-get install -y libpq-dev python-dev
RUN pip install psycopg2
COPY . /bot
CMD echo "start" && python3 /bot/main.py
#CMD bash