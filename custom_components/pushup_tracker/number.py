"""Number platform for Pushup Tracker integration."""

from homeassistant.components.number import RestoreNumber
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
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
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: callable
) -> None:
    """Set up number entities."""
    numbers = [
        {
            "key": "max_value",
            "default": DEFAULT_MAX_VALUE,
            "min_val": 1,
            "max_val": 100,
            "step": 1,
            "name_suffix": "Max Value",
            "unique_id_suffix": "max_value",
        },
        {
            "key": "tolerance",
            "default": DEFAULT_TOLERANCE,
            "min_val": 0,
            "max_val": 30,
            "step": 1,
            "name_suffix": "Tolerance",
            "unique_id_suffix": "tolerance",
        },
        {
            "key": "rise_time",
            "default": DEFAULT_RISE_TIME,
            "min_val": 0,
            "max_val": 5,
            "step": 0.1,
            "name_suffix": "Rise Time (Seconds)",
            "unique_id_suffix": "rise_time",
        },
        {
            "key": "boost_time",
            "default": DEFAULT_BOOST_TIME,
            "min_val": 0,
            "max_val": 5,
            "step": 0.1,
            "name_suffix": "Boost Time (Seconds)",
            "unique_id_suffix": "boost_time",
        },
        {
            "key": "fall_time",
            "default": DEFAULT_FALL_TIME,
            "min_val": 0,
            "max_val": 5,
            "step": 0.1,
            "name_suffix": "Fall Time (Seconds)",
            "unique_id_suffix": "fall_time",
        },
        {
            "key": "boost_value",
            "default": DEFAULT_BOOST_VALUE,
            "min_val": 0,
            "max_val": 100,
            "step": 1,
            "name_suffix": "Boost Value",
            "unique_id_suffix": "boost_value",
        },
    ]
    entities = [ConfigNumber(config_entry, **params) for params in numbers]
    async_add_entities(entities)


class ConfigNumber(RestoreNumber):
    """A generic number entity for configuration parameters."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        key: str,
        default: float,
        min_val: float,
        max_val: float,
        step: float,
        name_suffix: str,
        unique_id_suffix: str,
    ) -> None:
        """Initialize the number entity."""
        self._config_entry = config_entry
        self.key = key
        self.default = default
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        self.name_suffix = name_suffix
        self.unique_id_suffix = unique_id_suffix

    @property
    def entry_data(self):
        """Return the entry data for this number."""
        return self.hass.data[DOMAIN][self._config_entry.entry_id]

    async def async_added_to_hass(self):
        """Restore state."""
        await super().async_added_to_hass()
        state = await self.async_get_last_number_data()
        if state:
            self.entry_data[self.key] = state.native_value

        self.entry_data["number_update_callbacks"].append(self.async_write_ha_state)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Unregister callbacks."""
        await super().async_will_remove_from_hass()
        self.entry_data["number_update_callbacks"].remove(self.async_write_ha_state)

    @property
    def name(self):
        """Return the name of the number entity."""
        return f"{self._config_entry.data[CONF_NAME]} {self.name_suffix}"

    @property
    def unique_id(self):
        """Return a unique ID for the number entity."""
        return f"{self._config_entry.entry_id}_{self.unique_id_suffix}"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
        }

    @property
    def native_value(self):
        """Return the current value."""
        return self.entry_data.get(self.key, self.default)

    def set_native_value(self, value: float):
        """Set the value and update the sensor."""
        self.entry_data[self.key] = value
        self.schedule_update_ha_state()
