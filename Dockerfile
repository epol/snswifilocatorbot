FROM python:3.6
MAINTAINER Enrico Polesel <epol@autistici.org>

RUN pip install pysnmp python-telegram-bot==3.4
ADD bot.py /
CMD [ "python", "/bot.py", "/config.ini" ]
