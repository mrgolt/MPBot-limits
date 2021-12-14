FROM python


WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -r requirements.txt

RUN apt-get -y update
RUN apt-get -y install locales
RUN locale-gen ru_RU.UTF-8
RUN apt-get install -y libfontconfig
RUN apt-get install -y firefox-esr

COPY . .

CMD ["python", "-u", "./tg_bot.py"]