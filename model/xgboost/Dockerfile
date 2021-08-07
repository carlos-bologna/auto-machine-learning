FROM python:3.8.5
LABEL maintainer="[carlos.bologna@hotmail.com]"

# Update Ubuntu
RUN apt-get update

# Update PIP
RUN /usr/local/bin/python -m pip install --upgrade pip

COPY requirements.txt /home/requirements.txt

WORKDIR /home

RUN pip install -r requirements.txt

COPY . /home/

#ENTRYPOINT ["python"]
ENTRYPOINT ["python", "main.py"]
