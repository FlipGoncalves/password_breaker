FROM python:3.8-slim-buster

WORKDIR /

COPY slave.py slave.py
COPY server/const.py server/const.py
COPY algorithm.py algorithm.py
COPY Protocolo.py Protocolo.py

CMD [ "python3", "-u", "slave.py"]
