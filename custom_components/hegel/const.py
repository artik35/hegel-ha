from __future__ import annotations

DOMAIN = "hegel"
PLATFORMS = ["media_player", "select"]

CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"
CONF_MODEL = "model"

# ECO / pseudo-standby (to jest jedyne zdalne "power" w Twoim opisie)
CONF_POWER_ON_VALUE = "power_on_value"    # domyślnie "1"
CONF_POWER_OFF_VALUE = "power_off_value"  # domyślnie "0"

# Źródła: mapowanie "kod wejścia" -> "nazwa"
# (ułatwia to też auto-extend jeśli pojawi się nieznany kod)
CONF_SOURCES_MAP = "sources_map"

DEFAULT_PORT = 50001
DEFAULT_NAME = "Hegel"

# Safety-first
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 3
POLL_INTERVAL_CHOICES = [1, 2, 3, 5]
MIN_SEND_INTERVAL_MS = 120
SOCKET_TIMEOUT = 5.0
CONNECT_TIMEOUT = 3.0
RECONNECT_BACKOFF_S = 2.0

CR = "\r"

# Status requests
CMD_POWER_Q = "-p.?"
CMD_INPUT_Q = "-i.?"
CMD_VOLUME_Q = "-v.?"
CMD_MUTE_Q = "-m.?"

# Setters
def cmd_power(v: str) -> str:
  return f"-p.{v}"

def cmd_input(code: int) -> str:
  return f"-i.{code}"

def cmd_volume(percent: int) -> str:
  # percent: 0..100
  return f"-v.{percent}"

def cmd_mute_toggle() -> str:
  return "-m.t"

def cmd_mute(v: str) -> str:
  # v: "0" lub "1"
  return f"-m.{v}"


# Domyślne mapy wejść (baseline). Użytkownik może edytować w Options.
# UWAGA: H590 wg Twojego działającego Node-RED ma 12 wejść (w tym ANALOG3 i NETWORK).
DEFAULT_SOURCES_BY_MODEL: dict[str, dict[int, str]] = {
  "H590": {
    1: "XLR1",
    2: "XLR2",
    3: "ANALOG1",
    4: "ANALOG2",
    5: "ANALOG3",
    6: "BNC",
    7: "COAXIAL",
    8: "OPTICAL1",
    9: "OPTICAL2",
    10: "OPTICAL3",
    11: "USB",
    12: "NETWORK",
  },
  # dla innych modeli wypełnimy później (albo z PDF, albo po zgłoszeniach użytkowników)
  "H390": {},
  "H190": {},
  "H120": {},
  "H95": {},
}

SUPPORTED_MODELS = list(DEFAULT_SOURCES_BY_MODEL.keys())
