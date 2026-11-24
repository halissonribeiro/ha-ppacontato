"""Support for PPA Contatto binary sensors."""

from __future__ import annotations

from typing import Any, Dict, Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .config_entities import get_device_display_name
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the PPA Contatto binary sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    async_add_entities(
        PPAContattoConnectivitySensor(coordinator, device)
        for device in coordinator.data.get("devices", [])
        if device.get("serial")
    )


class PPAContattoConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    """Whether the PPA Contatto device is connected to the cloud.

    Seeded from the ``online`` flag of ``/devices`` and updated in real time by
    the ``device/connected`` / ``device/disconnected`` WebSocket events.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device: Dict[str, Any]) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._serial = device.get("serial")
        self._attr_unique_id = f"{self._serial}_online"
        self._attr_name = f"{get_device_display_name(device)} Online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=get_device_display_name(device),
            manufacturer="PPA Contatto",
            model="Gate Controller",
            sw_version=device.get("version"),
            serial_number=self._serial,
        )

    def _get_device_data(self) -> Optional[Dict[str, Any]]:
        """Get current device data from coordinator."""
        for device in (self.coordinator.data or {}).get("devices", []):
            if device.get("serial") == self._serial:
                return device
        return None

    @property
    def available(self) -> bool:
        """Stay available while we have data, so offline shows as 'off', not 'unavailable'."""
        return self._get_device_data() is not None

    @property
    def is_on(self) -> Optional[bool]:
        """Return True if the device is online."""
        device = self._get_device_data()
        if device is None or device.get("online") is None:
            return None
        return bool(device.get("online"))
