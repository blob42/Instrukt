##
##  Copyright (c) 2023 Chakib Ben Ziane <contact@blob42.xyz> . All rights reserved.
##
##  SPDX-License-Identifier: AGPL-3.0-or-later
##
##  This file is part of Instrukt.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU Affero General Public License as
##  published by the Free Software Foundation, either version 3 of the
##  License, or (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU Affero General Public License for more details.
##
##  You should have received a copy of the GNU Affero General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Binding management."""
from dataclasses import dataclass
from typing import Literal

from textual.binding import Binding, BindingType

ButtonVariant = Literal["default", "primary", "success", "warning", "error"]


#NOTE: the filter is exptecing native textual Bindings
def is_binding_action(b: BindingType) -> bool:
    return isinstance(b, ActionBinding)


@dataclass(frozen=True)
class ActionBinding(Binding):
    """Inherits textual Binding class with extra properties."""
    variant: ButtonVariant = "default"
    """button variant used for this action"""

    btn_id: str | None = None
    """Custom button id used in the action bar."""

    # predicate
    """Conditional function that returns True if the action should be displayed."""
