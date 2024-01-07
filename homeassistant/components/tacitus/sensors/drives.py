"""Definitions of all HDD sensors supoorted by tacitus integration."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from ..const import DOMAIN


class HDDSensorBase(CoordinatorEntity):
    """Shared basic structure for all HDD sensor entities."""

    _name_template: str = "{} sensor"
    _attr_name: str | None
    _sensor_posfix = ""
    _attr_device_info: DeviceInfo | None = None
    _attr_unique_id: str | None = None

    def __init__(
        self, hdd_serial, device_path, coordinator: DataUpdateCoordinator
    ) -> None:
        """Entity is identified by HDDs serial number, path can change."""
        super().__init__(coordinator, hdd_serial)
        self.serial = hdd_serial
        self._attr_name = self._name_template.format(device_path)
        self._path = device_path

        # TODO: Include server id in unique id somehow
        self._attr_unique_id = (
            f"{DOMAIN}_drive_{device_path.lower()}_{self._sensor_posfix}"
        )

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

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("serial_number") == self.serial:
                self._attr_native_value = drive.get("temperature", None)
        self.async_write_ha_state()


class HDDPowerState(HDDSensor):
    """Entity that provides information of HDDs power state."""

    _attr_name = "HDD Power State"
    _name_template = "HDD {} Power State"
    _sensor_posfix = "power_state"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("serial_number") == self.serial:
                self._attr_native_value = drive.get("power_mode", None)
        self.async_write_ha_state()


class HDDModelName(HDDSensor):
    """Entity that provides information of HDDs model name."""

    _attr_name = "HDD Model Name"
    _name_template = "HDD {} Model Name"
    _sensor_posfix = "model_name"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("serial_number") == self.serial:
                self._attr_native_value = drive.get("model_name", None)
        self.async_write_ha_state()


class HDDSmartError(HDDBinnarySensor):
    """Entity that provides information of healt status of HDD."""

    _attr_name = "HDD error S.M.A.R.T. "
    _name_template = "HDD {} error S.M.A.R.T. "
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _sensor_posfix = "smart_error"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("serial_number") == self.serial:
                self._attr_is_on = not drive.get("smart_status_passed")
        self.async_write_ha_state()


class HDDType(HDDSensor):
    """Entity that provides information of connection type HDD uses."""

    _attr_name = "HDD type"
    _name_template = "HDD {} type"
    _sensor_posfix = "type"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("serial_number") == self.serial:
                self._attr_native_value = drive.get("drive_type", None)
        self.async_write_ha_state()
