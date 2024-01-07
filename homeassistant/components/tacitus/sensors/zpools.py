"""Definition of all WireGuard sensors supported by tacitus integration."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from ..const import DOMAIN


class ZpoolSensorBase(CoordinatorEntity, SensorEntity):
    """Shared basic structure for all HDD sensor entities."""

    _name_template: str = "{} sensor"
    _attr_name: str | None
    _sensor_posfix = ""
    _attr_device_info: DeviceInfo | None = None
    _attr_unique_id: str | None = None

    def __init__(self, pool_name, coordinator: DataUpdateCoordinator) -> None:
        """Entity is identified by HDDs serial number, path can change."""
        super().__init__(coordinator, pool_name)
        self.pool_name = pool_name
        self._attr_name = self._name_template.format(pool_name)

        # TODO: Include server id in unique id somehow
        self._attr_unique_id = (
            f"{DOMAIN}_drive_{pool_name.lower()}_{self._sensor_posfix}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.pool_name)},
            name=f"Zpool {self.pool_name}",
            manufacturer="JJs homelab",
            model="Erskine",
            sw_version="0.0.1",
        )


class ZpoolSizeSensor(ZpoolSensorBase):
    """Entity that provides information of HDDs model name."""

    _attr_name = "Zpoll size"
    _name_template = "Zpool {} size"
    _sensor_posfix = "size"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("name") == self.pool_name:
                self._attr_native_value = drive.get("size", None)
        self.async_write_ha_state()


class ZpoolAllocatedSensor(ZpoolSensorBase):
    """Entity that provides information of HDDs model name."""

    _attr_name = "Zpoll allocated size"
    _name_template = "Zpool {} allocated size"
    _sensor_posfix = "allocated_size"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("name") == self.pool_name:
                self._attr_native_value = drive.get("alloc", None)
        self.async_write_ha_state()


class ZpoolHealthSensor(ZpoolSensorBase):
    """Entity that provides information of HDDs model name."""

    _attr_name = "Zpoll health"
    _name_template = "Zpool {} health"
    _sensor_posfix = "health"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        for drive in self.coordinator.data.get("result"):
            if drive.get("name") == self.pool_name:
                self._attr_native_value = drive.get("health", None)
        self.async_write_ha_state()
