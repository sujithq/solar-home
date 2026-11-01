"""Atomic entity for the existing DSMR acquisition loop; opens no reader."""

from datetime import datetime, timezone
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_call_later

from .atomic_sample import SampleTracker

_LOGGER = logging.getLogger(__name__)


class AtomicGridSensor(SensorEntity):
    _attr_name = "DSMR atomic grid sample"
    _attr_should_poll = False
    _attr_force_update = True

    def __init__(self, entry, telegram):
        self._attr_unique_id = f"{entry.entry_id}_atomic_grid_sample"
        self.tracker = SampleTracker()
        self._cancel_expiry = None
        self.update_data(telegram)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._schedule_expiry()

    async def async_will_remove_from_hass(self):
        if self._cancel_expiry:
            self._cancel_expiry()
        await super().async_will_remove_from_hass()

    def _schedule_expiry(self):
        if self._cancel_expiry:
            self._cancel_expiry()
            self._cancel_expiry = None
        if self.tracker.error is None:
            stamp = datetime.fromisoformat(self.tracker.attributes["meter_timestamp"])
            remaining = 30 - (datetime.now(timezone.utc) - stamp).total_seconds()
            self._cancel_expiry = async_call_later(self.hass, max(0, min(30, remaining)), self._expire)

    def _expire(self, _now):
        self._cancel_expiry = None
        self.tracker.reject("sample_expired")
        _LOGGER.warning("Atomic DSMR sample expired")
        self.async_write_ha_state()

    def update_data(self, telegram):
        previous_error = self.tracker.error
        if telegram is None:
            self.tracker.reject("transport_unavailable")
        else:
            self.tracker.accept(telegram, datetime.now(timezone.utc))
        if self.tracker.error and self.tracker.error != previous_error:
            _LOGGER.warning("Atomic DSMR sample rejected: %s", self.tracker.error)
        if self.hass:
            self._schedule_expiry()
            self.async_write_ha_state()

    @property
    def available(self):
        return self.tracker.error is None

    @property
    def native_value(self):
        return self.tracker.sequence if self.available else None

    @property
    def extra_state_attributes(self):
        return dict(self.tracker.attributes)
