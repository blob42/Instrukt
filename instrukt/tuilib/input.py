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
from typing import Any, Callable

from textual import events


def blur_on(key: str) -> Callable[..., Any]:
    """Decorator class to allow bluring a focusable widgets."""

    def decorator_unfocusable(cls) -> Callable[..., Any]:
        if not cls.can_focus:
            return cls

        async def on_key(self, event: events.Key) -> None:
            if event.key == key:
                self.blur()

        cls.on_key = on_key
        return cls

    return decorator_unfocusable


