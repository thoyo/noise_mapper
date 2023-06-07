FROM python:3.6

ENV NOISEMAPPER /opt/noisemapper

RUN mkdir -p $NOISEMAPPER

COPY requirements.txt $NOISEMAPPER/requirements.txt
COPY main.py $NOISEMAPPER/main.py
COPY folium/ $NOISEMAPPER/folium
COPY templates/ $NOISEMAPPER/templates
COPY run /usr/bin

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

RUN pip install -r $NOISEMAPPER/requirements.txt

WORKDIR $NOISEMAPPER
CMD ["run"]
