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

if TYPE_CHECKING:

    from .app import InstruktApp
    from .config import ConfigManager
    from .indexes.manager import IndexManager
    from .messages.log import MsgType
    from .types import AnyMessage

context: ContextVar['Context'] = ContextVar('context')

#WARN: make sure context is concurrency/thread safe
class Context():
    """Stores a reference to textual App context"""

    # app: 'InstruktApp'
    # config_manager: 'ConfigManager'
    # index_manager: 'IndexManager'

    def __init__(self,
                 app: t.Optional['InstruktApp'] = None) -> None:
        from .config import ConfigManager
        from .indexes.manager import IndexManager
        self.app = app
        self.config_manager = ConfigManager(self)

        # if openai key is not available use default embedding function
        chroma_kwargs: dict [str, t.Any] = {}

        # if user exported openai api key, use openai embeddings by default

        #REVIEW: the user always chooses the default embedding function, 
        # automatic assignment should be used as absolute last resort
        #
        # if self.config_manager.C.openai_api_key is not None and len(
        #         self.config_manager.C.openai_api_key) != 0:
        #     try:
        #         from langchain.embeddings.openai import OpenAIEmbeddings
        #         chroma_kwargs['embedding_function'] = OpenAIEmbeddings() # type: ignore
        #     except ImportError:
        #         self.error(
        #             "OpenAIEmbeddings not available, using default embedding function"
        #         )
        self.index_manager = IndexManager(
            chroma_settings=self.config_manager.config.chroma,
            ctx=self,
            chroma_kwargs=chroma_kwargs)

    class Config:
        arbitrary_types_allowed = True

    def __repr__(self):
        return f"Context(app={self.app})"

    #FIXME: messages called through here come after `self.info()` !
    def post_message(self, message: 'AnyMessage') -> None:
        """Post a message to the app."""
        self.app.post_message(message)

    async def write_chat_buffer(self, message: 'AnyMessage') -> None:
        """Write a message to the chat buffer."""
        self.app.notify_chat_buffer(message)

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
