"""Switch platform for Pushup Tracker."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switches."""
    sensor = hass.data[DOMAIN][entry.entry_id]["sensor"]
    async_add_entities(
        [
            CalibrationSwitch(entry, sensor),
        ]
    )


class CalibrationSwitch(SwitchEntity):
    """Switch to start/stop calibration."""

    def __init__(self, config_entry: ConfigEntry, sensor) -> None:
        """Initialize the switch."""
        self._config_entry = config_entry
        self._sensor = sensor

    @property
    def unique_id(self):
        """Return a unique ID for the switch."""
        return f"{self._config_entry.entry_id}_calibration"

    @property
    def name(self):
        """Return the name of the switch."""
        return f"{self._config_entry.data['name']} Calibration"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }

    @property
    def is_on(self):
        """Return True if the switch is on."""
        return self._sensor.is_calibrating

    async def async_turn_on(self, **kwargs):
        """Handle the switch being turned on."""
        self._sensor.start_calibration()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Handle the switch being turned off."""
        self._sensor.stop_calibration()
        self.async_write_ha_state()
