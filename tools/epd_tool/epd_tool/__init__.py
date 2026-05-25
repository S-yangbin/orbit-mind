"""EPD-nRF5 电子墨水屏 BLE 命令行工具包"""

__version__ = "2.0.0"

from .cli import main
from .commands import app
from .ble_client import EPDClient
from .constants import EPD_MODELS, Cmd
