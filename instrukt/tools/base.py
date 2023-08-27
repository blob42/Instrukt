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
"""Instrukt agent tools."""

#TODO: check if tools offer async or provide async wrappers

import importlib.util
import inspect
import logging
import typing as t
from abc import ABC, abstractmethod
from typing import TypeVar

from langchain.agents.load_tools import load_tools
from langchain.tools import BaseTool
from langchain.tools import Tool as LangchainTool
from pydantic import BaseModel

from ..utils.asynctools import run_async

if t.TYPE_CHECKING:
    from langchain.base_language import BaseLanguageModel

log = logging.getLogger(__name__)

#TEST: used for testing, default list not yet finalized
DEFAULT_LC_TOOLS = ["requests_all"]
"""Default langchain tools to load"""

#FIXME: cleaner way to test installed tool dependencies and add them

if importlib.util.find_spec("wikipedia"):
    try:
        import wikipedia  # type: ignore
        DEFAULT_LC_TOOLS.append("wikipedia")
    except ImportError:
        pass


class SomeTool(ABC):
    """Interface that all instrukt tools must implement."""

    name: str
    """The unique name of the tool that clearly communicates its purpose."""
    description: str
    """Used to tell the model how/when/why to use the tool.
    
    You can provide few-shot examples as a part of the description.
    """
    is_retrieval: bool = False
    """If this is a retrieval based tool."""

    retrieval_runner: t.Any | None = None

    attached: bool = True
    """Whether the tool is attached to the agent at startup or not."""

    @abstractmethod
    def run(self, *args, **kwargs) -> t.Any:
        pass

    @abstractmethod
    async def arun(self, *args, **kwargs) -> t.Any:
        pass

    async def _arun(self, *args, **kwargs) -> t.Any:
        pass




T = TypeVar("T", bound=t.Union[SomeTool, "BaseTool"])


#HACK: probably a bad idea
def enforce_async_tool(tool: T) -> T:
    """Fallback async for langchain tools.
   
   Take an instance of the `BaseTool` class from langchain and creates an
   asynchronous fallback if it is not implemented.
    """
    if not callable(inspect.getattr_static(tool, '_arun', None)):
        raise TypeError("Tool does not have a callable _arun method.")

    source = inspect.getsource(tool._arun)
    if 'NotImplementedError' in source:

        async def async_fallback(*args, **kwargs):
            return await run_async(tool.run, *args, **kwargs)

        tool.__dict__['_arun'] = async_fallback
        log.info(f"Created async fallback for {tool.name}")

        return tool

    return tool


#WIP: this cannot be used directly as langchain tool, we actually pass the base_tool
# to langchain when we build the agent, the defined methods here are not used.
#TODO: create decorator
class LcToolWrapper(t.Generic[T], SomeTool):
    """A wrapper around langchain tools that adds custom logic."""

    def __init__(self, basetool: T, **kwargs):
        self.base_tool: T = enforce_async_tool(basetool)
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"LcToolWrapper({self.base_tool})"

    def run(self, *args, **kwargs) -> t.Any:
        return self.base_tool.run(*args, **kwargs)

    async def arun(self, *args, **kwargs) -> t.Any:
        """Try builtin coroutine and use fallback otherwise."""
        try:
            return await self.base_tool.arun(*args, **kwargs)
        except NotImplementedError:
            return await run_async(self.base_tool.run, *args, **kwargs)

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.base_tool, name)


class ToolRegistry:
    """ToolFactory keeps track of all registered tools."""

    _instance = None
    _tools: dict[str, SomeTool] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._tools: dict[str, SomeTool] = {}

        return cls._instance

    def __init__(self, preload_tool_names: list[str] | None = None):
        if preload_tool_names is None:
            preload_tool_names = DEFAULT_LC_TOOLS
        self.load_from_lc_tool_names(preload_tool_names)

    @property
    def tools(self) -> dict[str, SomeTool]:
        """Returns all registered tools."""
        return self._tools

    @property
    def names(self) -> list[str]:
        """Returns registered tools by name"""
        return [t for t in self._tools.keys()]

    def register_tool(self, tool: SomeTool, name: str | None = None) -> None:
        """Register a tool."""
        _name = name or tool.name
        if _name in self._tools:
            raise ValueError(f"A tool with name {_name} is already registered")
        self._tools[_name] = tool

    def register_tools(self, *tools: t.Tuple[str, SomeTool]) -> None:
        """Register many tools."""
        for tool_name, tool in tools:
            try:
                self.register_tool(tool, tool_name)
            except ValueError:
                log.warning(f"{tool.name} already registered, skipping.")
                continue

    def get_tool(self, tool_name: str) -> SomeTool:
        """Get a tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"No tool with name {tool_name} is registered")
        return self._tools[tool_name]

    def get_tools(self, *tool_names: str) -> list[SomeTool]:
        """Get many tools by name."""
        tools = []
        for tool_name in tool_names:
            try:
                tools.append(self.get_tool(tool_name))
            except ValueError:
                log.warning(f"No tool with name {tool_name} is registered")
                continue
        return tools

    #TODO: pass tool kwargs
    def load_from_lc_tool_names(
            self,
            tool_names: list[str],
            llm: t.Optional["BaseLanguageModel[t.Any]"] = None) -> None:
        """Load tools from langchain tool names into the registry"""
        tools = self.from_lc_tool_names(tool_names, llm=llm)
        self.register_tools(*zip([t.name for t in tools], tools))

    @staticmethod
    def from_lc_tool_names(
        tool_names: list[str],
        llm: t.Optional["BaseLanguageModel[t.Any]"] = None,
    ) -> list[SomeTool]:
        """Retu rn wrapped Langchain tools from names."""
        tools = load_tools(tool_names, llm=llm)
        return [LcToolWrapper(tool) for tool in tools]


class Tool(LangchainTool, SomeTool):
    """ A wrapper class for langchain.tools.Tool that implements SomeTool."""

    coroutine: t.Callable[..., t.Awaitable[str]]
    is_retrieval: bool = False
    """If this is a retrieval tool"""
    retrieval_runner: t.Any | None = None

    def wrapped(self) -> LcToolWrapper["BaseTool"]:
        return LcToolWrapper(self)



TOOL_REGISTRY = ToolRegistry()
