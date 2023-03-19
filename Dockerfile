FROM python:3.9.16

WORKDIR /app/

ADD requirements.txt .
RUN pip install -r requirements.txt

ADD bing_chat.py .

EXPOSE 5000
ENTRYPOINT [ "python", "bing_chat.py"]
