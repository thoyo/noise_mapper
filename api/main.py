from influxdb import InfluxDBClient
from datetime import datetime
import folium
from folium.plugins import HeatMap
import folium.plugins
import numpy as np
import scipy.signal
import branca
import flask
from matplotlib.colors import LinearSegmentedColormap
import logging
import os

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")

CMAP = LinearSegmentedColormap.from_list('rg', ["g", "y", "r"], N=256)

ZOOM_LEVEL_START = 17

INFLUX_PORT = 8086
INFLUX_DATABASE = "noisemapper"
if os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False):
    INFLUX_HOST = "influxdb"
else:
    INFLUX_HOST = "0.0.0.0"

LAT_LON_BOUNDS = [[41.357742, 2.109375], [41.429342, 2.230225]]
PIXEL_SIZE_DEG_LAT = 0.00025
PIXEL_SIZE_DEG_LON = 0.0004

MAX_NOISE_RANGE = 0.02

INFLUXDBCLIENT = InfluxDBClient(host=INFLUX_HOST, port=INFLUX_PORT, database=INFLUX_DATABASE)

app = flask.Flask(__name__)


def generate_array():
    lat_size = abs(int((LAT_LON_BOUNDS[1][0] - LAT_LON_BOUNDS[0][0]) / PIXEL_SIZE_DEG_LAT))
    lon_size = abs(int((LAT_LON_BOUNDS[1][1] - LAT_LON_BOUNDS[0][1]) / PIXEL_SIZE_DEG_LON))
    return np.zeros([lat_size, lon_size, 2])


def fill_array(arr, lat, lon, sound):
    lat_offset_px = int((lat - LAT_LON_BOUNDS[0][0]) / PIXEL_SIZE_DEG_LAT)
    lon_offset_px = int((lon - LAT_LON_BOUNDS[0][1]) / PIXEL_SIZE_DEG_LON)
    arr[lat_offset_px, lon_offset_px, 0] = \
        (arr[lat_offset_px, lon_offset_px, 0] * arr[lat_offset_px, lon_offset_px, 1] + sound) / \
        (arr[lat_offset_px, lon_offset_px, 1] + 1)
    arr[lat_offset_px, lon_offset_px, 1] += 1


def generate_image_from_array(arr):
    arr[..., 0][arr[..., 0] > MAX_NOISE_RANGE] = MAX_NOISE_RANGE
    arr[..., 0] -= np.min(arr[..., 0])
    arr[..., 0] /= np.max(arr[..., 0])
    arr[..., 0] = scipy.ndimage.morphology.grey_dilation(arr[..., 0], size=(3, 3))

    arr[..., 1][arr[..., 1] > 0] = 1
    filter_kernel = [[0.25, 0.5, 0.25],
                     [0.5, 0.5, 0.5],
                     [0.25, 0.5, 0.25]]
    arr[..., 1] = scipy.ndimage.morphology.grey_dilation(arr[..., 1], size=(3, 3), structure=filter_kernel) - 0.5


def measurements_list_to_field_value(measurements, field_key):
    ret = []
    for measurement in measurements:
        ret.append(measurement[field_key])
    return ret


@app.route('/')
def index():
    return flask.render_template('./index.html')


@app.route('/noisemap')
def noisemap():
    t_i = datetime.now()

    samples = list(INFLUXDBCLIENT.query("select * from samples where test!='True';"))[0]
    lats = measurements_list_to_field_value(samples, "lat")
    lons = measurements_list_to_field_value(samples, "lon")
    sounds = measurements_list_to_field_value(samples, "sound")
    # alts = measurements_list_to_field_value(samples, "alt")
    # times = measurements_list_to_field_value(samples, "time")

    mean_coords = [np.mean(lats), np.mean(lons)]
    m = folium.Map(location=mean_coords, zoom_start=ZOOM_LEVEL_START)

    arr = generate_array()
    for i, sound in enumerate(sounds):
        if sound is None:
            continue
        fill_array(arr, lats[i], lons[i], sound)
    generate_image_from_array(arr)

    img = folium.raster_layers.ImageOverlay(
        name="",
        image=arr,
        mercator_project=True,
        origin="lower",
        bounds=LAT_LON_BOUNDS,
        colormap=CMAP,
        zindex=1,
    )
    img.add_to(m)

    fig = branca.element.Figure(height="100%")
    fig.add_child(m)

    t_f = datetime.now()
    point_out = {
        "measurement": "metrics",
        "fields": {"api_response_time": (t_f - t_i).total_seconds()},
        "time": t_f
    }
    ret = INFLUXDBCLIENT.write_points([point_out])
    logging.info(f"Point inserted in influx. ret={ret}. Point={point_out}")

    return m._repr_html_()


@app.route('/heatmap')
def heatmap():
    samples = list(INFLUXDBCLIENT.query("select * from samples where test!='True';"))[0]
    lats = measurements_list_to_field_value(samples, "lat")
    lons = measurements_list_to_field_value(samples, "lon")

    mean_coords = [np.mean(lats), np.mean(lons)]
    m = folium.Map(location=mean_coords, zoom_start=ZOOM_LEVEL_START)

    heat_data = []
    for i, lat in enumerate(lats):
        heat_data.append([lat, lons[i]])
    HeatMap(heat_data).add_to(m)

    fig = branca.element.Figure(height="100%")
    fig.add_child(m)

    return m._repr_html_()


@app.route('/last-location/')
def last():
    samples = list(INFLUXDBCLIENT.query("select * from samples where test!='True' order by time desc limit 1;"))[0]
    lat = samples[0]["lat"]
    lon = samples[0]["lon"]
    sound = samples[0]["sound"]
    time = samples[0]["time"]

    m = folium.Map(location=[lat, lon], zoom_start=ZOOM_LEVEL_START)
    folium.Marker([lat, lon], popup=f"<i>Time: {time}, sound: {sound}</i>").add_to(m)

    fig = branca.element.Figure(height="100%")
    fig.add_child(m)

    return m._repr_html_()


@app.route('/last-session/')
def last_session():
    last_sample = list(INFLUXDBCLIENT.query("select * from samples where test!='True' order by time desc limit 1;"))[0]
    last_session = last_sample[0]["session_uuid"]
    samples = list(INFLUXDBCLIENT.query(f"select * from samples where test!='True' and session_uuid='{last_session}';"))[0]
    lats = measurements_list_to_field_value(samples, "lat")
    lons = measurements_list_to_field_value(samples, "lon")
    sounds = measurements_list_to_field_value(samples, "sound")
    times = measurements_list_to_field_value(samples, "time")

    mean_coords = [np.mean(lats), np.mean(lons)]
    m = folium.Map(location=mean_coords, zoom_start=ZOOM_LEVEL_START)

    for i, lat in enumerate(lats):
        folium.Marker([lat, lons[i]], popup=f"<i>Time: {times[i]}, sound: {sounds[i]}</i>").add_to(m)

    fig = branca.element.Figure(height="100%")
    fig.add_child(m)

    return m._repr_html_()


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
