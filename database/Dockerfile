FROM ubuntu:18.04
RUN apt-get update && apt-get -y upgrade
RUN apt-get -y install postgresql
RUN apt-get -y install sudo
COPY run_database.sh run_database.sh
EXPOSE 80
CMD sudo ./run_database.sh
