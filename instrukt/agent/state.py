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
"""Agents state machine."""

from enum import Enum, auto
from typing import Generic, Protocol, TypeVar


class AgentState(Enum):
    NIL = auto()
    READY = auto()
    LLM_PROCESSING = auto()
    CHAIN_PROCESSING = auto()
    TOOL_USING = auto()
    AGENT_THINKING = auto()
    AGENT_ACTION = auto()

    @classmethod
    def from_str(cls, state: str) -> 'AgentState':
        return EVENT_TO_STATE[state]


EVENT_TO_STATE: dict[str, AgentState] = {
    #DEBUG: these are for debug purposes
    # 'llm_start': AgentState.LLM_PROCESSING,
    # 'llm_new_token': AgentState.LLM_PROCESSING,
    'llm_end': AgentState.READY,
    'llm_error': AgentState.READY,
    #TODO!: separate UI status for AgentAction and Thinking
    'chain_start': AgentState.AGENT_THINKING,
    'chain_end': AgentState.READY,
    'chain_error': AgentState.READY,
    'tool_start': AgentState.TOOL_USING,
    'tool_end': AgentState.AGENT_THINKING,
    'tool_error': AgentState.READY,
    'agent_action': AgentState.AGENT_ACTION,
    'agent_finish': AgentState.READY,
    'agent_cancelled': AgentState.READY,
}


#TODO!: add decorator for implementers of this interface
class StateObserver(Protocol):

    def watch_state(self, state: AgentState) -> None:
        ...


T = TypeVar('T', bound=StateObserver)


class AgentStateSubject(Generic[T]):

    def __init__(self) -> None:
        self.observers: set[T] = set()

    def register_observer(self, observer: T) -> None:
        if observer not in self.observers:
            print(f"registering observer {observer}")
            self.observers.add(observer)

    def notify_observers(self, state: AgentState) -> None:
        for observer in self.observers:
            observer.watch_state(state)


class AgentStateMachine(AgentStateSubject[T]):
    """Agent state machine."""

    def __init__(self) -> None:
        super().__init__()
        self.state = AgentState.NIL

    def set_state(self, state: AgentState) -> None:
        """Set state."""
        if not isinstance(state, AgentState):
            raise ValueError("Invalid state")

        self.state = state
        print(f"notifying observers {self.observers}")
        self.notify_observers(self.state)

    def update_state(self, event: str) -> AgentState:
        """Sets the state based on the event."""
        self.state = EVENT_TO_STATE[event]
        self.notify_observers(self.state)
        return self.state
