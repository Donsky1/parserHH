FROM python:3.10
WORKDIR /app
RUN apt-get update && apt-get -y upgrade && apt install nano
COPY . .
RUN pip install --upgrade pip && pip install -r requirements.txt
VOLUME ["/app/base"]
CMD python run.py