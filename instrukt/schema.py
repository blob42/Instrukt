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
"""Common schema classes."""
from typing import NamedTuple, Any

from langchain.schema import AIMessage
from langchain.schema import HumanMessage as LHumanMessage


class ChatMessage(NamedTuple):
    """Base class for chat messages."""
    content: str | dict[str, Any]

class AgentManifest(NamedTuple):
    """A manifest for an agent."""
    name: str
    """Name must be the same as the name of the agent module name."""

    description: str
    version: str

class HumanChatMessage(ChatMessage):
    """A message from the human."""

class AgentChatMessage(ChatMessage):
    """A message from the agent."""

LC_TO_INSTRUKT_MESSAGES = {
        LHumanMessage: HumanChatMessage,
        AIMessage: AgentChatMessage,
        }



