"""
A sensor created to read temperature from swimareas in Karlshamn Sweden
For more details about this platform, please refer to the documentation at
https://github.com/kayjei/badtemp_karlshamn
"""
import logging
import json
import urllib
import voluptuous as vol
import datetime
import secrets
import requests
import lxml
from lxml import html
from bs4 import BeautifulSoup

from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import (PLATFORM_SCHEMA)
from homeassistant.const import (TEMP_CELSIUS)
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

URL = 'https://www.karlshamnenergi.se/app/badtemperaturer/'
PERS_JSON = '.badtemp_karlshamn.json'

UPDATE_INTERVAL = datetime.timedelta(minutes=30)

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the sensor platform"""

    response = urllib.request.urlopen(URL)
    soup = BeautifulSoup(response,'html.parser')
    ## Scraper
    path = soup.body.div.div.main.article.div.script

    response_json = json.loads(path.string.split("'")[1])
    _LOGGER.debug("Response: " + str(response_json))
    with open(PERS_JSON, "w") as outfile:
        json.dump(json.dumps(response_json), outfile)

    poller_entity = response_json[0]["entity_id"]
    _LOGGER.debug("Creating poller device: " + poller_entity)

    devices = []

    for jsonr in response_json:
        _LOGGER.debug("Device: " + str(jsonr))
        name = str(jsonr["name"]).capitalize()
        id = str(jsonr["entity_id"])
        lat = str(jsonr["location"]["lat"])
        lon = str(jsonr["location"]["lng"])
        entity = str(jsonr["entity_id"])
        timestamp = datetime.datetime.now()

        devices.append(SensorDevice(id, None, lat, lon, timestamp, name, poller_entity))
        _LOGGER.info("Adding sensor: " + str(id))

    add_devices(devices)

class SensorDevice(Entity):
    def __init__(self, id, temperature, latitude, longitude, timestamp, name, poller_entity):
        self._device_id = id
        self._state = temperature
        self._entity_id = 'sensor.badtemp_' + str(name.lower().replace("\xe5","a").replace("\xe4","a").replace("\xf6","o"))
        self._latitude = latitude
        self._longitude = longitude
        self._timestamp = timestamp
        self._friendly_name = name
        self._poller = poller_entity
        self.update()

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Temperature"""

        if self._device_id == self._poller:
            ApiRequest.call()

        jsonr = ReadJson().json_data()
        for ent in jsonr:
            if ent["id"] == self._device_id:
                self._state = round(float(ent["value"]), 1)
                self._timestamp = datetime.datetime.fromtimestamp(ent["ts"] / 1000).replace(microsecond=0)
                _LOGGER.debug("Temp is " + str(self._state) + " for " + str(self._friendly_name))

    @property
    def entity_id(self):
        """Return the id of the sensor"""
        return self._entity_id
        _LOGGER.debug("Updating device " + self._entity_id)

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return '°C'

    @property
    def name(self):
        """Return the name of the sensor"""
        return self._friendly_name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def state(self):
        """Return the state of the sensor"""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor"""
        return 'mdi:coolant-temperature'

    @property
    def device_class(self):
        """Return the device class of the sensor"""
        return 'temperature'

    @property
    def device_state_attributes(self):
        """Return the attribute(s) of the sensor"""
        if self._latitude is None or self._longitude is None:
            return {
                "lastUpdate": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
        else:
            return {
                "latitude": self._latitude,
                "longitude": self._longitude,
                "lastUpdate": self._timestamp
                }

class ApiRequest:

    def call():
        """Temperature"""
        entities = []

        with open(PERS_JSON, "r") as json_file:
            json_data = json.loads(json.load(json_file))
            if json_data[0].get("name") is not None:
                for ent in json_data:
                    entities.append(ent["entity_id"])
            else:
                for ent in json_data:
                    entities.append(ent["id"])

        URL = 'https://www.karlshamnenergi.se/wp-content/themes/karlshamnenergi/ajax/iot-ansluten/IOTAnsluten.php'
        
        headers = {"Content": "application/json", "Content-Type": "application/json"}
        payload = json.dumps(entities)
        _LOGGER.debug("Sending API request to: " + URL + ", posting data " + str(payload))

        response = requests.post(URL, headers=headers, data=payload)
        response_json = json.loads(response.content)
        _LOGGER.debug("Response: " + str(response_json))

        with open(PERS_JSON, "w") as outfile:
            json.dump(json.dumps(response_json), outfile)

        return True

class ReadJson:
    def __init__(self):
        self.update()

    @Throttle(UPDATE_INTERVAL)
    def update(self):
        """Temperature"""
        _LOGGER.debug("Reading " + PERS_JSON + " for device")
        with open(PERS_JSON, "r") as json_file:
            json_datas = json.loads(json.load(json_file))
        self._json_response = json_datas

    def json_data(self):
        """Keep json data"""
        return self._json_response
