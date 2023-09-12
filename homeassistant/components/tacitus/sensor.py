"""Platform for sensor integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import requests

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_HOST, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN


class GetCached:
    def __init__(self, url, minimum_delay_sec=60) -> None:
        self.url = url
        self.last_reponse = None
        self.last_update = None
        self.delay = minimum_delay_sec

    def __call__(self) -> Any:
        if self.last_update is None or self.last_update < datetime.now():
            self.last_reponse = requests.get(self.url)
            self.last_update = datetime.now() + timedelta(seconds=self.delay)
        return self.last_reponse


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    # add_entities([HDDTemperatureSensor(hdd_serial="J3320082G9J6BA")])
    host = config[CONF_HOST]
    # TODO: Do it better
    cached = GetCached(f"{host}/smartctl/")
    resp = cached()

    if resp.status_code == 200:
        data = resp.json()
        for drive in data.get("result"):
            serial = drive.get("serial_number")
            path = drive.get("block_device_path")
            add_entities(
                [
                    HDDPowerState(
                        hdd_serial=serial, device_path=path, cached_request=cached
                    ),
                    HDDTemperatureSensor(
                        hdd_serial=serial, device_path=path, cached_request=cached
                    ),
                    HDDModelName(
                        hdd_serial=serial, device_path=path, cached_request=cached
                    ),
                    HDDSmartError(
                        hdd_serial=serial, device_path=path, cached_request=cached
                    ),
                    HDDType(hdd_serial=serial, device_path=path, cached_request=cached),
                ]
            )


class HDDSensorBase:
    _name_template = "{} sensor"

    def __init__(self, hdd_serial, device_path, cached_request: GetCached) -> None:
        super().__init__()
        self.serial = hdd_serial
        self._attr_name = self._name_template.format(device_path)
        self._path = device_path
        self._get_data = cached_request

    # This is not working yet. TODO: Resolve it later # https://developers.home-assistant.io/docs/device_registry_index
    @property
    def device_info(self) -> DeviceInfo | None:
        return {
            "identifiers": {(DOMAIN, self.serial)},
            "name": f"HDD {self._path}",
            "manufacturer": "JJs homelab",
            "model": "Carbon",
            "sw_version": "0.0.1",
        }


class HDDSensor(HDDSensorBase, SensorEntity):
    pass


class HDDBinnarySensor(HDDSensorBase, BinarySensorEntity):
    pass


class HDDTemperatureSensor(HDDSensor):
    """Representation of a Sensor."""

    _attr_name = "HDD temperature"
    _name_template = "HDD {} temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def update(self) -> None:
        self._attr_native_value = None
        resp = self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("temperature", None)


class HDDPowerState(HDDSensor):
    _attr_name = "HDD Power State"
    _name_template = "HDD {} Power State"

    def update(self) -> None:
        self._attr_native_value = None
        resp = self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("power_mode", None)


class HDDModelName(HDDSensor):
    _attr_name = "HDD Model Name"
    _name_template = "HDD {} Model Name"

    def update(self) -> None:
        self._attr_native_value = None
        resp = self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("model_name", None)


class HDDSmartError(HDDBinnarySensor):
    _attr_name = "HDD error S.M.A.R.T. "
    _name_template = "HDD {} error S.M.A.R.T. "
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def update(self) -> None:
        self._attr_is_on = None
        resp = self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_is_on = not drive.get("smart_status_passed")


class HDDType(HDDSensor):
    _attr_name = "HDD type"
    _name_template = "HDD {} type"

    def update(self) -> None:
        self._attr_native_value = None
        resp = self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("drive_type", None)
