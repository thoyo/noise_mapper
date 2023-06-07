FROM python:3.6

ENV NOISEMAPPER /opt/noisemapper

RUN mkdir -p $NOISEMAPPER

COPY requirements.txt $NOISEMAPPER/requirements.txt
COPY main.py $NOISEMAPPER/main.py
COPY .env $NOISEMAPPER/.env

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

RUN apt update
RUN apt-get -y install ffmpeg
RUN pip install -r $NOISEMAPPER/requirements.txt

WORKDIR $NOISEMAPPER
CMD ["python", "-u", "main.py"]