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
"""ActionBar for quick actions."""

import typing as t
from collections import defaultdict

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button

from ...binding import ActionBinding, is_binding_action


class ActionBar(Horizontal):

    def __init__(self, label: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.label = label

        # dict{id: action}
        self._button_actions: dict[str, str] = dict()
        self._buttons: list[Button] = list()


#TODO: handle typle bindings

    def _build_bar(self) -> ComposeResult:
        """Generate a button for each action defined in parent screen."""

        # get all bindings for current screen
        # bindings = [
        #     binding for (ns, binding) in self.app.namespace_bindings.values()
        #     if ns == self.screen and binding.show
        # ]
        bindings: list[ActionBinding] = []
        for b in self.screen.BINDINGS:
            if is_binding_action(b):
                bindings.append(t.cast(ActionBinding, b))

        action_to_bindings = defaultdict(list)
        for binding in bindings:
            action_to_bindings[binding.action].append(binding)

        for _, bindings in action_to_bindings.items():
            binding = bindings[0]
            if binding.key_display is None:
                key_display = self.app.get_key_display(binding.key)
                if key_display is None:
                    key_display = binding.key.upper()
            else:
                key_display = binding.key_display

            btn_id = binding.btn_id
            if btn_id is None:
                btn_id = binding.description.replace(" ", "-")

            key_text = f"\[{key_display}]{binding.description}"
            btn = Button(key_text, id=btn_id, variant=binding.variant)
            assert btn.id is not None, "Button id is None"
            self._button_actions[btn.id] = binding.action
            self._buttons.append(btn)

        yield from self._buttons

    @on(Button.Pressed)
    async def handle_button_actions(self, event: Button.Pressed) -> None:
        """Handle button actions."""
        if event.button.id in self._button_actions:
            await self.screen.run_action(self._button_actions[event.button.id])

    def compose(self) -> ComposeResult:
        yield from self._build_bar()
