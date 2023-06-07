# import needed modules
import androidhelper as android
import time
import paho.mqtt.client as mqtt
import json
import os
from dotenv import load_dotenv
import logging
import uuid

logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

load_dotenv()

SAMPLING_PERIOD_SECONDS = 60
MAX_LOCATION_EXPIRY_SECONDS = 180

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

TEST = False

USER_UUID = os.getenv("USER_UUID")

AUDIO_PATH = "/storage/emulated/0/python/noisemapper_audio_record.mp4"

# Initiate android-module
droid = android.Android()


def get_location():
    now = time.time()
    droid.startLocating()
    loc = droid.readLocation().result
    if loc == {}:
        loc = droid.getLastKnownLocation().result
        logging.info("Using last known location")
        location_type = "last"
    else:
        location_type = "new"

    try:
        n = loc['gps']
        location_source = "gnss"
    except KeyError:
        logging.info("Using network, not gps")
        n = loc['network']
        location_source = "network"

    time_loc = n["time"]
    logging.debug(f"System time: {int(now)}")
    logging.debug(f"Location time: {time_loc / 1e3}")
    delta = time_loc / 1e3 - now
    logging.debug(f"Delta: {int(delta)}")
    if abs(delta) > MAX_LOCATION_EXPIRY_SECONDS:
        logging.error(f"Delta abs(last known location - now) = abs({delta}) > {MAX_LOCATION_EXPIRY_SECONDS}")
        return None

    lat = n['latitude']
    lon = n['longitude']
    alt = n['altitude']

    return {"lat": lat, "lon": lon, "alt": alt, "source": location_source, "type": location_type, "time": time_loc}


def connect_mqtt(mqttc=None):
    while True:
        if mqttc is not None:
            try:
                mqttc.disconnect()
            except Exception as e:
                logging.error(e)
                time.sleep(10)
                continue

        try:
            mqttc = mqtt.Client()
        except Exception as e:
            logging.error(e)
            time.sleep(10)
            continue

        try:
            mqttc.username_pw_set(username=MQTT_USERNAME, password=MQTT_PASSWORD)
            mqttc.connect(MQTT_HOST, MQTT_PORT)
        except Exception as e:
            logging.error(e)
            time.sleep(10)
            continue

        mqttc.loop_start()
        mqttc.loop_interval = SAMPLING_PERIOD_SECONDS

        return mqttc


def main(session_uuid):
    mqttc = connect_mqtt()
    while True:
        try:
            loc = get_location()
            if loc is None:
                logging.info(f"Go sleep {SAMPLING_PERIOD_SECONDS} seconds")
                time.sleep(SAMPLING_PERIOD_SECONDS)
                logging.info("Wake up")
                continue

            droid.recorderStartMicrophone(AUDIO_PATH)
            time.sleep(5)
            droid.recorderStop()

            MQTT_MSG = json.dumps({"lat": loc["lat"],
                                   "lon": loc["lon"],
                                   "alt": loc["alt"],
                                   "time": loc["time"],
                                   "session_uuid": session_uuid,
                                   "user_uuid": USER_UUID,
                                   "source": loc["source"],
                                   "type": loc["type"],
                                   "test": TEST})

            ret1 = mqttc.publish("pos", MQTT_MSG)
            logging.info(f"pos published, msg={MQTT_MSG}, ret={ret1}")

            ret2 = mqttc.publish(str(loc["time"]), open(AUDIO_PATH, "rb").read())
            logging.info(f"audio published, topic={str(loc['time'])}, ret={ret2}")

            if ret1[0] != 0 or ret2[0] != 0:
                logging.info("Trying to disconnect")
                mqttc.disconnect()
                logging.info("Disconnection executed")
                mqttc = connect_mqtt()
                logging.info("Re-connection executed")
        except Exception as e:
            logging.error(e)
            mqttc = connect_mqtt(mqttc)

        logging.info(f"Go sleep {SAMPLING_PERIOD_SECONDS} seconds")
        time.sleep(SAMPLING_PERIOD_SECONDS)
        logging.info("Wake up")


if __name__ == "__main__":
    session_uuid = str(uuid.uuid4())
    logging.info(f"Session: {session_uuid}")
    main(session_uuid)
