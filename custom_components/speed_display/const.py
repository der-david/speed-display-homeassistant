"""Constants for the Speed Display integration."""

from homeassistant.const import Platform

DOMAIN = "speed_display"

CONF_NAME = "name"
CONF_TOPIC_PREFIX = "topic_prefix"

SOURCE_FIRMWARE = "firmware"
SOURCE_SIMULATOR = "simulator"
SOURCE_UNKNOWN = "unknown"

RANGE_ORDER = {
    "safe": 0,
    "neutral": 1,
    "fast": 2,
}

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
