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
"""Custom textlog widget"""

from textual.strip import Strip
from textual.widgets import RichLog


class RichLogUp(RichLog):
    """Custom RichLog widget with bottom-up scrolling view"""

    def render_line(self, y: int) -> Strip:
        content_height = len(self.lines)
        available_height = self.size[1]
        empty_space_top = max(0, available_height - content_height)

        if y < empty_space_top:
            # Render empty lines above the content
            return Strip.blank(self.size.width, self.rich_style)

        content_line_index = y - empty_space_top

        if content_line_index < content_height:
            # render the content lines
            scroll_x, scroll_y = self.scroll_offset
            line = self._render_line(scroll_y + content_line_index, scroll_x,
                                     self.size.width)
            strip = line.apply_style(self.rich_style)
            return strip

        # render empty lines below the content
        return Strip.blank(self.size.width, self.rich_style)
