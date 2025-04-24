"""Button components for Pushup Tracker."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_BOOST_TIME,
    DEFAULT_BOOST_VALUE,
    DEFAULT_FALL_TIME,
    DEFAULT_MAX_VALUE,
    DEFAULT_RISE_TIME,
    DEFAULT_TOLERANCE,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Set up button platform."""
    async_add_entities([ResetConfigurationButton(config_entry)])


class ResetConfigurationButton(ButtonEntity):
    """Representation of a Reset Configuration Button."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the button entity."""
        self._config_entry = config_entry

    @property
    def entry_data(self):
        """Return the entry data for this button."""
        return self.hass.data[DOMAIN][self._config_entry.entry_id]

    @property
    def name(self):
        """Return the name of the number entity."""
        return f"{self._config_entry.data['name']} Reset Configuration"

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._config_entry.entry_id}_reset_configuration"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }

    async def async_press(self):
        """Handle the button being pressed."""
        default_values = {
            "boost_time": DEFAULT_BOOST_TIME,
            "boost_value": DEFAULT_BOOST_VALUE,
            "fall_time": DEFAULT_FALL_TIME,
            "rise_time": DEFAULT_RISE_TIME,
            "tolerance": DEFAULT_TOLERANCE,
            "max_value": DEFAULT_MAX_VALUE,
        }

        # Reset the configuration to default values
        for key, value in default_values.items():
            self.entry_data[key] = value

        # Update state of number entities
        for callback in self.entry_data["number_update_callbacks"]:
            callback()
