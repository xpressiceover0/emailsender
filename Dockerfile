FROM python:latest

WORKDIR /usr/src/emailsender

EXPOSE 8000

RUN apt-get update
RUN apt-get -y upgrade

COPY . .
RUN pip3 install --upgrade pip
RUN apt-get -y install vim
RUN apt install -y apt-transport-https curl
RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64] https://brave-browser-apt-release.s3.brave.com/ stable main"|tee /etc/apt/sources.list.d/brave-browser-release.list
RUN apt update -y
RUN apt install -y brave-browser
RUN pip install -r requirements.txt
#RUN python emailapp.py
