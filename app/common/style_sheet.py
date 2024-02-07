# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    LINK_CARD = "link_card"
    SAMPLE_CARD = "sample_card"
    HOME_INTERFACE = "home_interface"
    ICON_INTERFACE = "icon_interface"
    VIEW_INTERFACE = "view_interface"
    SETTING_INTERFACE = "setting_interface"
    GALLERY_INTERFACE = "gallery_interface"
    NAVIGATION_VIEW_INTERFACE = "navigation_view_interface"
    CUSTOM_TREE = "custom_tree"
    SET_CARD = "setting_card"
    STATE_TOOL_TIP = "state_tool_tip"
    CUSTOM_INTERFACE = "custom_frame"
    EXPORT = "export"
    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f":/gallery/qss/{theme.value.lower()}/{self.value}.qss"
