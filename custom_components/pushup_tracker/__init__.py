"""The Pushup Tracker integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_INPUT_ENTITY, DOMAIN

PLATFORMS = [Platform.BUTTON, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up Pushup Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize state storage
    entry_id = entry.entry_id
    hass.data[DOMAIN][entry_id] = {
        "calibrating": False,
        "input_entity": entry.data[CONF_INPUT_ENTITY],
        "number_update_callbacks": [],
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
