import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import json
from moviepy.editor import AudioFileClip
import audio2numpy as a2n
import numpy as np
import os
from dotenv import load_dotenv
import uuid
import logging
import os

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")

load_dotenv()

INFLUX_PORT = 8086
INFLUX_DATABASE = "noisemapper"
if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
    INFLUX_HOST = "influxdb"
else:
    INFLUX_HOST = "0.0.0.0"

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

INFLUXDBCLIENT = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DATABASE)

point = {}


def mp4_audio_to_arr(mp4_audio):
    filename = str(uuid.uuid4())
    with open(f"{filename}.mp4", "wb") as f:
        f.write(mp4_audio)
    mp4_without_frames = AudioFileClip(f"{filename}.mp4")
    mp4_without_frames.write_audiofile(f"{filename}.mp3")
    x, _ = a2n.audio_from_file(f"{filename}.mp3")
    os.remove(f"{filename}.mp3")
    os.remove(f"{filename}.mp4")
    return x


def on_message(client, userdata, message):
    global point
    logging.info("Received message")

    if message.topic == "pos":
        logging.info(f"Message received: {str(message.payload.decode('utf-8'))}")
        data = json.loads(message.payload)
        test = data.get("test", None)

        lat = data.get("lat", None)
        lon = data.get("lon", None)
        alt = data.get("alt", None)
        session_uuid = data.get("session_uuid", None)
        user_uuid = data.get("user_uuid", None)
        location_type = data.get("type", None)
        location_source = data.get("source", None)
        rx_time = data.get("time", None)

        if point.get(rx_time, None) is None:
            point[rx_time] = {}

        point[rx_time]["lat"] = lat
        point[rx_time]["lon"] = lon
        point[rx_time]["alt"] = alt
        point[rx_time]["session_uuid"] = session_uuid
        point[rx_time]["user_uuid"] = user_uuid
        point[rx_time]["type"] = location_type
        point[rx_time]["source"] = location_source
        point[rx_time]["test"] = test
    else:
        rx_time = int(message.topic)
        logging.info(f"Received audio file in topic {message.topic}")
        try:
            audio_arr = mp4_audio_to_arr(message.payload)
        except Exception as e:
            logging.error(f"Failed to do mp4 to audio arr, {e}")
            del point[rx_time]
            return
        if point.get(rx_time, None) is None:
            point[rx_time] = {}

        point[rx_time]["sound"] = np.mean(abs(audio_arr))

    if len(point[rx_time].keys()) == 9:
        session_uuid = point[rx_time]["session_uuid"]
        del point[rx_time]["session_uuid"]
        user_uuid = point[rx_time]["user_uuid"]
        del point[rx_time]["user_uuid"]
        location_type = point[rx_time]["type"]
        del point[rx_time]["type"]
        location_source = point[rx_time]["source"]
        del point[rx_time]["source"]
        test = point[rx_time]["test"]
        del point[rx_time]["test"]
        try:
            point_out = {
                "measurement": "samples",
                "fields": point[rx_time],
                "time": int(rx_time * 1e6)
            }
            ret = INFLUXDBCLIENT.write_points([point_out],
                                              tags={"session_uuid": session_uuid,
                                                    "user_uuid": user_uuid,
                                                    "type": location_type,
                                                    "source": location_source,
                                                    "test": test})
            logging.info(f"Point inserted in influx. ret={ret}. Point={point_out}")
            del point[rx_time]
        except Exception as e:
            logging.info(f"Error writing point {point_out}: {e}")


if __name__ == "__main__":
    client = mqtt.Client()
    client.on_message = on_message
    client.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
    client.connect(MQTT_HOST)
    logging.info("Broker connection established")
    client.subscribe("#")
    client.on_message = on_message
    client.loop_forever()
