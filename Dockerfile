FROM python:3.9.16

WORKDIR /app/

ADD requirements.txt ./
RUN pip install -r requirements.txt


ADD bing_chat.py ./
ADD backend_entry.sh ./
RUN chmod +x backend_entry.sh

EXPOSE 5000
ENTRYPOINT  ["sh", "backend_entry.sh"]
