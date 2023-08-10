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
import typing as t
from typing import TYPE_CHECKING
from contextvars import ContextVar
import logging

if TYPE_CHECKING:

    from .app import InstruktApp
    from .config import ConfigManager
    from .indexes.manager import IndexManager
    from .messages.log import MsgType
    from .types import AnyMessage

context: ContextVar['Context'] = ContextVar('context')
index_manager_var: ContextVar['IndexManager | None'] = ContextVar(
    "index_manager", default=None)
config_manager_var: ContextVar['ConfigManager | None'] = ContextVar(
    "config_manager", default=None)

context_var: ContextVar['Context | None'] = ContextVar("context", default=None)

log = logging.getLogger(__name__)


#WARN: make sure context is concurrency/thread safe
class Context():
    """Stores a reference to textual App context"""

    def __init__(self) -> None:
        from .config import ConfigManager
        from .indexes.manager import IndexManager

        self.config_manager = ConfigManager()
        self.index_manager = IndexManager(
            chroma_settings=self.config_manager.config.chroma, )

    def __repr__(self):
        return f"Context(app={self.app})"

    @property
    def app(self) -> t.Optional['InstruktApp']:
        """The app property."""
        if hasattr(self, "_app"):
            return self._app
        return None

    @app.setter
    def app(self, value):
        self._app = value

    @property
    def index_manager(self) -> 'IndexManager':
        """The index_manager property."""
        im = index_manager_var.get()
        assert im is not None, "index_manager is None"
        return im

    @index_manager.setter
    def index_manager(self, value):
        index_manager_var.set(value)

    @property
    def im(self) -> 'IndexManager':
        """The index_manager property."""
        return self.index_manager

    @property
    def config_manager(self) -> 'ConfigManager':
        """The config_manager property."""
        cm = config_manager_var.get()
        assert cm is not None, "config_manager is None"
        return cm

    @config_manager.setter
    def config_manager(self, value):
        config_manager_var.set(value)

    @property
    def cm(self) -> 'ConfigManager':
        """The config_manager property."""
        return self.config_manager

    def post_message(self, message: 'AnyMessage') -> None:
        """Post a message to the app."""
        self.app.post_message(message)

    async def write_console_window(self, message: 'AnyMessage') -> None:
        """Write a message to the chat buffer."""
        self.app.notify_console_window(message)

    def notify(self, message: 'AnyMessage') -> None:
        """Send a notification to the UI."""
        self.app.post_message(message)

    def error(self, message: 'MsgType') -> None:
        """Send and error notification to the UI."""
        from .messages.log import LogMessage
        self.app.post_message(LogMessage.error(message))

    def info(self, message: 'MsgType') -> None:
        """Send an info notification to the UI."""
        from .messages.log import LogMessage
        self.app.post_message(LogMessage.info(message))


context_var.set(Context())
