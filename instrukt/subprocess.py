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
"""Calling external processes."""
import os
import subprocess
import tempfile
import typing as t

from textual.dom import DOMNode


class ExternalProcessMixin(DOMNode):

    # see https://github.com/Textualize/textual/discussions/165
    def edit(self, content: str) -> str | None:
        """Edit a file in an external editor. Defaults to $EDITOR, falls back to vim.

        Args:
            content: The content to edit.

        Returns the edited content or None if the user aborted the edit.
        """
        assert self.app._driver is not None
        self.app._driver.stop_application_mode()

        initial = content
        result = None
        try:
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as ef:
                ef.write(content)
                ef.flush()
                editor = os.environ.get('EDITOR', 'vim')
                if editor == 'vim':
                    subprocess.call(
                        [editor, '+set backupcopy=yes wrap', ef.name])
                else:
                    subprocess.call([editor, ef.name])
                ef.seek(0)
                # get result
                output = ef.read()
                if output != initial:
                    result = output
        finally:
            self.app.refresh()
            self.app._driver.start_application_mode()
            return result

    def open_path(self, path: str) -> None:
        assert self.app._driver is not None
        self.app._driver.stop_application_mode()
        try:
            editor = os.environ.get('EDITOR', 'vim')
            subprocess.call([editor, path])
        finally:
            self.app.refresh()
            self.app._driver.start_application_mode()

        
    def select(self, items: t.Iterable[str]) -> str:
        """Select an item from a list using an external selector (fzf, dmenu, rofi ...)

        Items are passed to selector through stdin.
        A custom selector can be set using the env variable `SELECTOR`.

        Args:
            items: The list of items to select from.

        Returns:
            str: the selected item.
        """
        assert self.app._driver is not None
        self.app._driver.stop_application_mode()

        selected = ""
        input = "\n".join(items)
        try:
            selector = os.environ.get('SELECTOR', 'fzf')

            output = subprocess.run(selector.split(),
                                    input=input,
                                    text=True,
                                    stdout=subprocess.PIPE)
            selected = output.stdout.strip()
        finally:
            self.app.refresh()
            self.app._driver.start_application_mode()

        return selected

