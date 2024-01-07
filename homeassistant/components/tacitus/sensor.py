"""Platform for sensor integration."""
from __future__ import annotations

from asyncio import timeout
from datetime import timedelta
import logging

from homeassistant import config_entries, core
from homeassistant.const import CONF_HOST
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .sensors.drives import (
    HDDModelName,
    HDDPowerState,
    HDDSmartError,
    HDDTemperatureSensor,
    HDDType,
)
from .sensors.zpools import ZpoolAllocatedSensor, ZpoolHealthSensor, ZpoolSizeSensor
from .tacitus_api import TacitusAPI

_LOGGER = logging.getLogger(__name__)


class BasicCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, api_callback):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Tacitus callback coordinator",
            update_interval=timedelta(seconds=60),
        )
        self.callback = api_callback

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        async with timeout(10):
            return await self.callback()


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setups sensors from a config entry created in the integrations UI."""

    host = config_entry.data[CONF_HOST]
    if host[-1] == "/":
        host = host[:-1]
    tacitus = TacitusAPI(host)
    coordinator_drives = BasicCoordinator(hass, tacitus.get_drives)

    await coordinator_drives.async_config_entry_first_refresh()

    data = coordinator_drives.data
    for drive in data.get("result"):
        serial = drive.get("serial_number")
        path = drive.get("block_device_path")
        async_add_entities(
            [
                HDDPowerState(
                    hdd_serial=serial, device_path=path, coordinator=coordinator_drives
                ),
                HDDTemperatureSensor(
                    hdd_serial=serial, device_path=path, coordinator=coordinator_drives
                ),
                HDDModelName(
                    hdd_serial=serial, device_path=path, coordinator=coordinator_drives
                ),
                HDDSmartError(
                    hdd_serial=serial, device_path=path, coordinator=coordinator_drives
                ),
                HDDType(
                    hdd_serial=serial, device_path=path, coordinator=coordinator_drives
                ),
            ],
            update_before_add=True,
        )

    coordinator_zpools = BasicCoordinator(hass, tacitus.get_zpools)
    await coordinator_zpools.async_config_entry_first_refresh()
    for pool in coordinator_zpools.data.get("result"):
        async_add_entities(
            [
                ZpoolSizeSensor(
                    pool_name=pool.get("name"), coordinator=coordinator_zpools
                ),
                ZpoolAllocatedSensor(
                    pool_name=pool.get("name"), coordinator=coordinator_zpools
                ),
                ZpoolHealthSensor(
                    pool_name=pool.get("name"), coordinator=coordinator_zpools
                ),
            ],
            update_before_add=True,
        )
