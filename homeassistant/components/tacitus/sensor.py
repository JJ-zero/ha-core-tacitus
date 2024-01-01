"""Platform for sensor integration."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import httpx

from homeassistant import config_entries, core
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
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


class GetCached:
    """Super simple cache for repeated request to Tacitus API. Have to be rewritten later."""

    def __init__(self, url, minimum_delay_sec=60) -> None:
        """Set target url and maximum delay between requests."""
        self.url = url
        self.last_reponse: httpx.Response | None = None
        self.last_update: datetime | None = None
        self.delay = minimum_delay_sec

    async def __call__(self) -> Any:
        """With this call you can get a new or cached response. By reading this docstring you can gues that I despise this docstring linter."""
        if self.last_update is None or self.last_update < datetime.now():
            async with httpx.AsyncClient() as client:
                self.last_reponse = await client.get(self.url)
            self.last_update = datetime.now() + timedelta(seconds=self.delay)
        return self.last_reponse


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setups sensors from a config entry created in the integrations UI."""

    host = config_entry.data[CONF_HOST]
    if host[-1] == "/":
        host = host[:-1]
    cached = GetCached(f"{host}/drives/")
    resp = await cached()

    if resp.status_code == 200:
        data = resp.json()
        for drive in data.get("result"):
            serial = drive.get("serial_number")
            path = drive.get("block_device_path")
            async_add_entities(
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
                ],
                update_before_add=True,
            )


class HDDSensorBase:
    """Shared basic structure for all HDD sensor entities."""

    _name_template: str = "{} sensor"
    _attr_name: str | None
    _sensor_posfix = ""
    _attr_device_info: DeviceInfo | None = None
    _attr_unique_id: str | None = None

    def __init__(self, hdd_serial, device_path, cached_request: GetCached) -> None:
        """Entity is identified by HDDs serial number, path can change."""
        super().__init__()
        self.serial = hdd_serial
        self._attr_name = self._name_template.format(device_path)
        self._path = device_path
        self._get_data = cached_request

        # TODO: Include server id in unique id somehow
        self._attr_unique_id = f"{DOMAIN}_{device_path.lower()}_{self._sensor_posfix}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            name=f"HDD {self._path}",
            manufacturer="JJs homelab",
            model="Carbon",
            sw_version="0.0.1",
        )


class HDDSensor(HDDSensorBase, SensorEntity):
    """SensorEntity extended of HDD basic functions."""

    pass


class HDDBinnarySensor(HDDSensorBase, BinarySensorEntity):
    """BinarySensorEntity extended of HDD basic functions."""

    pass


class HDDTemperatureSensor(HDDSensor):
    """Representation of a Sensor."""

    _attr_name = "HDD temperature"
    _name_template = "HDD {} temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _sensor_posfix = "temperature"

    async def async_update(self) -> None:
        """Update method. What docstring you want here?."""
        self._attr_native_value = None
        resp = await self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("temperature", None)


class HDDPowerState(HDDSensor):
    """Entity that provides information of HDDs power state."""

    _attr_name = "HDD Power State"
    _name_template = "HDD {} Power State"
    _sensor_posfix = "power_state"

    async def async_update(self) -> None:
        """Update method. What docstring you want here?."""
        self._attr_native_value = None
        resp = await self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("power_mode", None)


class HDDModelName(HDDSensor):
    """Entity that provides information of HDDs model name."""

    _attr_name = "HDD Model Name"
    _name_template = "HDD {} Model Name"
    _sensor_posfix = "model_name"

    async def async_update(self) -> None:
        """Update method. What docstring you want here?."""
        self._attr_native_value = None
        resp = await self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("model_name", None)


class HDDSmartError(HDDBinnarySensor):
    """Entity that provides information of healt status of HDD."""

    _attr_name = "HDD error S.M.A.R.T. "
    _name_template = "HDD {} error S.M.A.R.T. "
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _sensor_posfix = "smart_error"

    async def async_update(self) -> None:
        """Update method. What docstring you want here?."""
        self._attr_is_on = None
        resp = await self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_is_on = not drive.get("smart_status_passed")


class HDDType(HDDSensor):
    """Entity that provides information of connection type HDD uses."""

    _attr_name = "HDD type"
    _name_template = "HDD {} type"
    _sensor_posfix = "type"

    async def async_update(self) -> None:
        """Update method. What docstring you want here?."""
        self._attr_native_value = None
        resp = await self._get_data()
        if resp.status_code == 200:
            data = resp.json()
            for drive in data.get("result"):
                if drive.get("serial_number") == self.serial:
                    self._attr_native_value = drive.get("drive_type", None)
