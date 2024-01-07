"""Tacitus API."""

import httpx

from homeassistant.helpers.update_coordinator import UpdateFailed


class TacitusAPI:
    """Tacitus API."""

    def __init__(self, host: str) -> None:
        """Initialize."""
        self._host = host

    @property
    def host(self) -> str:
        """Return host."""
        return self._host

    async def get_drives(self):
        """Return data."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.host}/drives/")
            if response.status_code == 200:
                return await response.json()
            else:
                raise UpdateFailed(f"HTTP status code {response.status_code}")

    async def get_wiregurad(self):
        """Return data."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.host}/wireguard/")
            if response.status_code == 200:
                return await response.json()
            else:
                raise UpdateFailed(f"HTTP status code {response.status_code}")
