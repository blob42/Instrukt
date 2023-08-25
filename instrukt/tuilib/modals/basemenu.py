## 
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz>. All rights reserved.
## 
##  SPDX-License-Identifier: AGPL-3.0-or-later
## 
##  This file is part of Instrukt.
## 
##  This program is free software: you can redistribute it and/or modify it under
##  the terms of the GNU Affero General Public License as published by the Free
##  Software Foundation, either version 3 of the License, or (at your option) any
##  later version.
## 
##  This program is distributed in the hope that it will be useful, but WITHOUT
##  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
##  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
##  details.
## 
##  You should have received a copy of the GNU Affero General Public License along
##  with this program.  If not, see <http://www.gnu.org/licenses/>.
## 
from typing import Any

from textual import events, on
from textual.app import App
from textual.geometry import Offset, Region
from textual.screen import ModalScreen, Screen

from ...types import InstruktDomNodeMixin


class BaseModalMenu(ModalScreen[Any], InstruktDomNodeMixin):

    BINDINGS = [
            ("D", "dev_console", "dev console"),
                ("escape", "dismiss", "Dismiss"),
                ]

    @on(events.Click)
    def close_modal(self, event: events.Click) -> None:
        if event.button == 3:
            self.dismiss()
        elif event.button == 1:
            wid, region = self.get_widget_at(event.screen_x, event.screen_y)
            #instance of wid
            if isinstance(wid, ModalScreen):
                self.dismiss()



    async def action_dev_console(self) -> None:
        await self._app.action_dev_console()


#FIXME: on resize the menu offset is adjusted after the second display
#NOTE: use the tooltip offest algorithm from textual
def set_screen_menu_position(app: App[Any], menu_modal: Screen[Any] | str, region: Region) -> None:
    """Set the position of a menu modal relative to region."""
    menu_modal = app.get_screen(menu_modal)
    menu = menu_modal.query_one("#menu")
    menu.offset = Offset(
            region.x + region.width - menu.size.width,
            region.y + region.height)
    menu.refresh()
