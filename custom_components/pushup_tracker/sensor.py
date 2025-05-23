"""Sensor platform for Pushup Tracker."""

from datetime import datetime, timedelta
import enum

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    ATTR_CALIBRATING,
    ATTR_DIRECTION,
    ATTR_MAX_DISTANCE,
    ATTR_MIN_DISTANCE,
    CONF_INPUT_ENTITY,
    DEFAULT_BOOST_TIME,
    DEFAULT_BOOST_VALUE,
    DEFAULT_FALL_TIME,
    DEFAULT_MAX_VALUE,
    DEFAULT_RISE_TIME,
    DEFAULT_TOLERANCE,
    DOMAIN,
    MANUFACTURER,
    MAX_DISTANCE,
    MODEL,
    SW_VERSION,
)

SCAN_INTERVAL = timedelta(milliseconds=100)
DATA_TIMEOUT = 0.5  # seconds without data before decay starts


class PushupDirection(enum.Enum):
    """Direction enum for pushup detection."""

    UP = "up"
    DOWN = "down"


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: callable
):
    """Set up sensor platform."""
    input_entity = config_entry.data[CONF_INPUT_ENTITY]
    sensor = PushupSensor(config_entry, input_entity)
    async_add_entities([sensor])

    hass.data[DOMAIN][config_entry.entry_id]["sensor"] = sensor


class PushupSensor(RestoreEntity, SensorEntity):
    """Representation of a Pushup Tracker Sensor."""

    def __init__(self, config_entry: ConfigEntry, input_entity: str) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._input_entity = input_entity
        self._state = 0
        self._calibrating = False
        self._min_distance = None
        self._max_distance = None

        self._current_direction = PushupDirection.DOWN
        self._active_boosts = []

    @property
    def entry_data(self):
        """Return the entry data for this number."""
        return self.hass.data[DOMAIN][self._config_entry.entry_id]

    async def async_added_to_hass(self):
        """Restore state and register callbacks."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            self._min_distance = state.attributes.get(ATTR_MIN_DISTANCE)
            self._max_distance = state.attributes.get(ATTR_MAX_DISTANCE)

        async_track_state_change_event(
            self.hass, self._input_entity, self._async_input_changed
        )

    @callback
    def _async_input_changed(self, event: Event[EventStateChangedData]) -> None:
        """Input handling."""
        new_state = event.data.get("new_state")
        if not new_state or new_state.state in {"unknown", "unavailable", None}:
            return

        try:
            current_distance = float(new_state.state)
        except ValueError:
            return

        if self._calibrating:
            self._update_calibration(current_distance)
            return

        self._process_boost_detection(current_distance)

    def _update_calibration(self, current_distance: float) -> None:
        """Calibration of min max."""
        if current_distance is None:
            return
        self._min_distance = (
            min(self._min_distance, current_distance)
            if self._min_distance
            else current_distance
        )
        self._max_distance = (
            max(self._max_distance, current_distance, MAX_DISTANCE)
            if self._max_distance
            else current_distance
        )

    def _process_boost_detection(self, current_distance: float) -> None:
        """Detect pushup using calibrated values."""
        if None in (self._min_distance, self._max_distance):
            return

        # Calculate thresholds based on tolerance
        tolerance = self.tolerance
        lower_threshold = self._min_distance + (tolerance / 100) * (
            self._max_distance - self._min_distance
        )
        upper_threshold = self._max_distance - (tolerance / 100) * (
            self._max_distance - self._min_distance
        )

        # Toggle direction based on thresholds
        if (
            self._current_direction == PushupDirection.UP
            and current_distance <= lower_threshold
        ):
            self._current_direction = PushupDirection.DOWN
            self._add_boost()
        elif (
            self._current_direction == PushupDirection.DOWN
            and current_distance >= upper_threshold
        ):
            self._current_direction = PushupDirection.UP

    def _add_boost(self):
        """Add a new boost when a pushup is detected."""
        self._active_boosts.append({"start_time": datetime.now(), "expired": False})

    def _process_boosts(self, current_time: datetime) -> None:
        """Update boost values with proper timing."""
        for boost in self._active_boosts:
            elapsed = (current_time - boost["start_time"]).total_seconds()
            if elapsed <= self.rise_time:
                boost["value"] = self.boost_value * (elapsed / self.rise_time)
            elif elapsed <= self.rise_time + self.boost_time:
                boost["value"] = self.boost_value
            else:
                decay_time = elapsed - self.rise_time - self.boost_time
                boost["value"] = self.boost_value * max(
                    0, 1 - (decay_time / self.fall_time)
                )

    async def async_update(self) -> None:
        """Update the sensor state."""
        if self._calibrating:
            return

        current_time = datetime.now(tz=None)

        self._process_boosts(current_time)
        max_value = self.max_value
        total_boost = sum(b["value"] for b in self._active_boosts)
        self._state = min(
            round((total_boost / 100) * max_value),
            max_value,
        )
        # Cleanup expired boosts
        self._active_boosts = [
            b
            for b in self._active_boosts
            if (current_time - b["start_time"]).total_seconds()
            <= self.rise_time + self.boost_time + self.fall_time
        ]

        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current sensor value."""
        if self._calibrating:
            return 0
        return self._state

    @property
    def extra_state_attributes(self):
        """Return additional sensor attributes."""
        return {
            ATTR_MIN_DISTANCE: self._min_distance,
            ATTR_MAX_DISTANCE: self._max_distance,
            ATTR_DIRECTION: self._current_direction.value,
            ATTR_CALIBRATING: self._calibrating,
        }

    @property
    def name(self):
        """Return the sensor name."""
        return f"{self._config_entry.data[CONF_NAME]} Pushup Tracker"

    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._config_entry.entry_id}_sensor"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self._config_entry.data[CONF_NAME],
            "sw_version": SW_VERSION,
        }

    @property
    def state_class(self):
        """Return the state class."""
        return SensorStateClass.MEASUREMENT

    def start_calibration(self):
        """Start calibration."""
        self._calibrating = True
        self._min_distance = None
        self._max_distance = None
        self._active_boosts = []
        self._state = 0
        self._current_direction = PushupDirection.DOWN

    def stop_calibration(self):
        """Stop calibration."""
        self._calibrating = False

    @property
    def tolerance(self):
        """Return the tolerance value."""
        return self.entry_data.get("tolerance", DEFAULT_TOLERANCE)

    @property
    def max_value(self):
        """Return the maximum value."""
        return self.entry_data.get("max_value", DEFAULT_MAX_VALUE)

    @property
    def rise_time(self):
        """Return the rise time."""
        return self.entry_data.get("rise_time", DEFAULT_RISE_TIME)

    @property
    def boost_time(self):
        """Return the boost time."""
        return self.entry_data.get("boost_time", DEFAULT_BOOST_TIME)

    @property
    def fall_time(self):
        """Return the fall time."""
        return self.entry_data.get("fall_time", DEFAULT_FALL_TIME)

    @property
    def boost_value(self):
        """Return the boost value."""
        return self.entry_data.get("boost_value", DEFAULT_BOOST_VALUE)

    @property
    def is_calibrating(self):
        """Return True if the sensor is calibrating."""
        return self._calibrating
