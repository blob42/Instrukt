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
"""Docker based agents."""

import asyncio
import copy
import logging
import re
import sys
import threading
import uuid
from abc import ABC, abstractmethod
from typing import (
    Any,
    ClassVar,
    Coroutine,
    Iterable,
    Optional,
    Sequence,
    Type,
    Union,
    cast,
)

from langchain.agents import AgentExecutor, initialize_agent
from langchain.agents.agent import (
    BaseMultiActionAgent,
    BaseSingleActionAgent,
)
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models.base import BaseChatModel
from langchain.memory.chat_memory import BaseChatMemory
from langchain.tools import BaseTool

# from langjail import DockerWrapper
from pydantic import BaseModel, Field, PrivateAttr, validator

from ..context import Context
from ..errors import AgentError
from ..llms.openai.token_usage import OpenAICallbackHandler
from ..tools.base import LcToolWrapper, SomeTool
from .memory import make_buffer_mem
from .state import AgentStateMachine

log = logging.getLogger(__name__)

BaseAgentType = Union[BaseSingleActionAgent, BaseMultiActionAgent]


#REFACT: use contextvar
class InstruktAgent(BaseModel, ABC):
    """Instrukt agents need to satisfy this base class.

    .. code-block::
        :caption: defining a custom agent

        class MyAgent(InstruktAgent):
            name = "my_agent"
            description = "my agent description"

    """

    name: ClassVar[str | None] = None
    """Name of the agent. Must not contain spaces."""

    description: ClassVar[str | None] = None

    display_name: ClassVar[str | None] = None
    """Display name of the agent. Can contain spaces."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    llm: BaseChatModel
    toolset: Sequence[SomeTool] = Field(default_factory=list)
    executor: Optional[AgentExecutor] = None
    realm: Optional[Any] = None  # DockerWrapper
    state: AgentStateMachine[Any] = Field(default_factory=AgentStateMachine)
    memory: Optional[BaseChatMemory] = Field(default_factory=make_buffer_mem)
    executor_params: dict[str, Any] = Field(default_factory=dict)
    llm_callback_handlers: list[BaseCallbackHandler] = Field(
        default_factory=lambda: [OpenAICallbackHandler()])
    """OpenAI callback handler for this agent."""

    _attached_tools: list[str] = PrivateAttr(default_factory=list)
    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)
    _task: asyncio.Task[Any] | None = PrivateAttr(default=None)

    class Config:
        arbitrary_types_allowed = True

    def __init_subclass__(cls: Type["InstruktAgent"], **kwargs):
        """Subclass must define a class var name and description"""
        if 'sphinx' in sys.modules:
            return
        if cls.name is None:
            raise NotImplementedError(
                f"{cls.__name__} must define a `name` as class attribute.")

        if not cls.name.isidentifier():
            raise ValueError(
                f"{cls.__name__} name must be a valid python identifier.")

        if cls.description is None:
            raise NotImplementedError(
                f"{cls.__name__} must define a `description` as class attribute."
            )

        if cls.display_name is None:
            cls.display_name = cls.name.capitalize()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._attached_tools = [t.name for t in self.toolset if t.attached]

        if self.executor is None:
            self.executor = self._initialize_agent()

        self.base_agent.llm_chain.llm.callbacks = self.llm_callback_handlers  # type: ignore

    @validator("executor_params", pre=True)
    def validate_executor_params(cls, v: dict[str, Any],
                                 values: dict[str, Any]) -> dict[str, Any]:
        """memory cannot be passed in executor_params as well as attribute."""
        print(values['memory'])
        if "memory" in v and "memory" in values:
            raise ValueError("memory cannot be passed in executor_params "
                             "as well as attribute.")
        return v

    def _build_toolset(self) -> Sequence[Any]:
        """Build a toolset compatible with langchain."""

        def attach_callback(t: BaseTool) -> BaseTool:
            """Attach callback to tool."""
            t.callbacks = self.llm_callback_handlers
            return t

        tools = []  # type: ignore
        if not self.toolset:
            return []

        def attached_tool(t):
            return t.name in self._attached_tools

        for t in filter(attached_tool, self.toolset):
            if isinstance(t, BaseTool):
                tools.append(t)
            elif isinstance(t, LcToolWrapper):
                tools.append(t.base_tool)

        return list(map(attach_callback, tools))

    @property
    def toolset_names(self) -> list[str]:
        """Return the names of the tools in toolset."""
        if self.toolset:
            return []
        return [t.name for t in self.toolset]

    @property
    def openai_cb_handler(self) -> OpenAICallbackHandler | None:
        for cb_handler in self.llm_callback_handlers:
            if isinstance(cb_handler, OpenAICallbackHandler):
                return cb_handler
        return None

    def is_attached_tool(self, tool_name: str) -> bool:
        return tool_name in self._attached_tools

    def _initialize_agent(self) -> AgentExecutor:
        """Initialize the agent executor."""
        if self.memory is not None:
            self.executor_params['memory'] = self.memory

        return initialize_agent(
            self._build_toolset(),
            self.llm,
            **self.executor_params,
        )

    def reload_agent(self) -> None:
        """Reloads the agent. Call this method after you modify the agent's toolset."""
        log.debug("Reloading agent...")
        self.executor = self._initialize_agent()

    @property
    def base_agent(self) -> Optional[BaseAgentType]:
        """Return underlying agent (langchain)."""
        if self.executor is None:
            return None
        return self.executor.agent

    @classmethod
    @abstractmethod
    def load(cls, ctx: 'Context') -> Optional['InstruktAgent']:
        """Agent loading logic goes here."""

    #TODO!: API for async agent loading
    # @classmethod
    # @abstractmethod
    # async def aload(cls, ctx: 'Context') -> Optional['InstruktAgent']:
    #     """Agent loading logic goes here (async)."""

    async def _start_agent_task(
            self, ctx: Context, coro: Coroutine[Any, Any, dict[str,
                                                               Any]]) -> None:
        """Start a the agent query task. Only task can be running."""
        if self._task is not None:
            ctx.info("Agent is already running.")
        else:
            self._task = asyncio.create_task(coro)
            try:
                await self._task
            except Exception as e:
                ctx.error(e)
                # traceback
                # raise e
            finally:
                self._task = None

    async def agent_running(self) -> bool:
        """Check if a task is running for this agent."""
        return self._task is not None and not self._task.done()

    async def stop_agent(self, ctx: Context) -> bool:
        """Stop the agent task."""
        if self._task is not None:
            self._task.cancel()
            self._task = None
            return True
        return False

    async def send_message(self, ctx: Context, msg: str) -> None:
        """Send a message to the agent (async)."""
        assert self.executor is not None, "Agent not initialized."
        from .callback import InstruktCallbackHandler
        instrukt_cb_handler = InstruktCallbackHandler(ctx=ctx)
        callbacks = [instrukt_cb_handler, *self.llm_callback_handlers]
        await self._start_agent_task(
            ctx,
            self.executor.acall(dict(input=msg),
                                return_only_outputs=True,
                                callbacks=callbacks))

    def update_tool_name(self, old: str, new: str) -> None:
        """Change the name of an attached tool."""
        if not self.toolset:
            raise ValueError("no tool to update.")
        if self.executor is None:
            raise AgentError("Agent not initialized.")
        try:
            old_tool = next(filter(lambda t: t.name == old, self.toolset))
            old_tool.name = new
            self.reload_agent()
        except StopIteration:
            raise ValueError(f"Tool {old} not found.")

    def forget_about(self, term: str) -> None:
        """Removes all occurences of `term` from chat memory."""

        def match_term(term: str, text: str) -> bool:
            """Matches term in text with regex case insensitive"""
            return bool(re.search(term, text, re.IGNORECASE))

        if self.memory is None:
            return

        chat_memory = copy.deepcopy(self.memory.chat_memory.messages)
        for (i, msg) in enumerate(chat_memory):
            if match_term(term, msg.content):
                self.memory.chat_memory.messages.remove(msg)

    def add_tool(self, tool: SomeTool) -> None:
        """Add a tool to the agent."""
        if self.executor is None:
            raise AgentError("Agent not initialized.")

        # if tool already in toolset, only try to attach it
        if self.toolset and tool in self.toolset:
            self.attach_tool(tool.name)
        else:
            with self._lock:
                assert tool.name not in self._attached_tools, "tool already attached."
                self.toolset = [*cast(list["SomeTool"], self.toolset), tool]
                self._attached_tools.append(tool.name)
            log.warning(f"forgetting about <{tool.name}>.")
            self.forget_about(tool.name)
            self.reload_agent()

    @property
    def attached_tools(self) -> list[str]:
        """Return the list of attached tools as str."""
        return self._attached_tools

    def attach_tool(self, name: str) -> None:
        """Attach a tool to the agent."""
        if self.executor is None:
            raise AgentError("Agent not initialized.")
        if name not in [t.name for t in self.toolset]:
            raise ValueError(f"Tool <{name}> not in toolset.")
        if name in self._attached_tools:
            log.warning(f"Tool <{name}> already attached.")
            pass
        else:
            self._attached_tools.append(name)
            self.reload_agent()

    def dettach_tool(self, name: str) -> None:
        """Dettach a tool from the agent."""
        log.debug(f"Dettaching tool <{name}>...")
        if not self.toolset:
            raise ValueError("no toolset.")
        if name not in [t.name for t in self.toolset]:
            raise ValueError(f"Tool <{name}> not in toolset.")
        if name in self._attached_tools:
            self._attached_tools.remove(name)
            self.reload_agent()
