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
"""Agent manager"""

from typing import TYPE_CHECKING, Any, Optional, Sequence

from instrukt.messages.agents import AgentLoaded
from instrukt.messages.log import LogMessage

from ..errors import AgentError
from .loading import AgentLoader

if TYPE_CHECKING:
    from ..context import Context
    from .base import InstruktAgent


class AgentManager:
    """AgentManager handles loading and switching between agents."""

    def __init__(self, ctx: 'Context'):
        self.ctx = ctx
        self._agents: dict[str, Any] = {}
        self.active_agent_name: str | None = None
        self._agent_mods: dict[str, Any] = {}

    @property
    def active_agent(self) -> Optional['InstruktAgent']:
        """List of currently active agents (implies loaded)."""
        if self.active_agent_name is not None:
            return self._agents[self.active_agent_name]
        return None

    @property
    def loaded_agents(self) -> Sequence[str]:
        """List of all loaded agents."""
        return list(self._agents.keys())

    def from_name(self, name: str) -> Optional['InstruktAgent']:
        """Return an agent by name."""
        return self._agents.get(name, None)

    def _load_agent(self, name: str) -> None:
        """slow agent loading function"""
        try:
            agent = AgentLoader.load_agent(name, self.ctx)
        except AgentError as e:
            self.ctx.post_message(LogMessage.error(e))
            return

        if agent is None:
            self.ctx.post_message(
                LogMessage.error(
                    AgentError(f"could not load agent {{{name}}}")))
        else:
            self._agents[agent.name] = agent

            agent_modname = agent.__class__.__module__.split('.')[-2]
            self._agent_mods[agent_modname] = agent
            self.active_agent_name = agent.name
            self.ctx.post_message(AgentLoaded(agent=agent))

    async def load_agent(self, agent_mod: str) -> None:
        """Load an agent or return loaded agent module."""
        if agent_mod in self._agent_mods:
            self.ctx.info("agent already loaded")
            self.active_agent_name = self._agent_mods[agent_mod].name
            #FIXME: should be a differnt message for switching agents
            self.ctx.post_message(AgentLoaded(agent=self.active_agent))
        else:
            self.ctx.app.run_worker(lambda: self._load_agent(agent_mod), thread=True)


    async def switch_agent(self, agent_name: str) -> None:
        """Switch to an already loaded agent by `name`."""
        if agent_name in self._agents:
            self.active_agent_name = agent_name
            self.ctx.post_message(AgentLoaded(agent=self.active_agent))

