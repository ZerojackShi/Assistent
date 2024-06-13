# coding: utf-8
from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme


class Icon(FluentIconBase, Enum):

    GRID = "Grid"
    MENU = "Menu"
    TEXT = "Text"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"
    FRAME_ALALYSIC = "frameanalysic"
    ERROR = "Error"
    REPLAY = "Replay"
    REGION = "Region"
    def path(self, theme=Theme.AUTO):
        return f":/gallery/images/icons/{self.value}_{getIconColor(theme)}.svg"


