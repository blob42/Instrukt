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
"""langchain callback handler """
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union, Sequence
from uuid import UUID
import logging

from langchain.callbacks.base import AsyncCallbackHandler, RetrieverManagerMixin
from pydantic import BaseModel

from ..context import Context
from ..messages.agents import AgentMessage
from ..utils.debug import notify
from .events import AgentEvents

log = logging.getLogger(__name__)


if TYPE_CHECKING:
    from langchain.schema import AgentAction, AgentFinish, LLMResult, Document

#REFACT:
#TODO!: use contextvar
class InstruktCallbackHandler(AsyncCallbackHandler, RetrieverManagerMixin,  BaseModel):

    ctx: Context

    class Config:
        arbitrary_types_allowed = True

    def _set_agent_state(self, state: str) -> None:
        assert self.ctx.app is not None, "app context error"
        if self.ctx.app.active_agent is None:
            raise ValueError("Agent is not loaded")
        self.ctx.app.active_agent.state.update_state(state)
    
    async def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """Run when LLM starts running."""
        notify("llm_start")
        self._set_agent_state("llm_start")
        # msg = AgentMessage(event=AgentEvents.LLMStart)

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """Run on new LLM token. Only available when streaming is enabled."""
        notify("llm new token")
        self._set_agent_state("llm_new_token")

    async def on_llm_end(self, response: 'LLMResult', **kwargs: Any) -> Any:
        """Run when LLM ends running."""
        notify("llm end instrukt")
        self._set_agent_state("llm_end")

    async def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when LLM errors."""
        self._set_agent_state("llm_error")
        notify("llm error")

    async def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> Any:
        """Run when chain starts running."""
        self._set_agent_state("chain_start")
        notify("chain start")
        # notify(f"entering {class_name}")
        msg = AgentMessage(event=AgentEvents.ChainStart, data=serialized)
        assert self.ctx.app is not None
        self.ctx.app.post_message(msg)

    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> Any:
        """Run when chain ends running."""
        self._set_agent_state("chain_end")
        notify("chain end")
        msg = AgentMessage(event=AgentEvents.ChainEnd, data=outputs)
        self.ctx.app.post_message(msg)

    async def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when chain errors."""
        self._set_agent_state("chain_error")
        notify("chain error")
        msg = AgentMessage(event=AgentEvents.ChainError, data=error)
        self.ctx.app.post_message(msg)

    async def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Run when tool starts running."""
        self._set_agent_state("tool_start")
        data = {**serialized, "input": input_str}
        msg = AgentMessage(event=AgentEvents.ToolStart, data=data)
        self.ctx.app.post_message(msg)

    #NOTE: logs the output of the tool without the actual tool name
    async def on_tool_end(self, output: str,
                    observation_prefix: Optional[str] = None,
                    llm_prefix: Optional[str] = None, # the next token of LLM
                    name: str = "",
                    **kwargs: Any) -> Any:
        """Run when tool ends running."""
        self._set_agent_state("tool_end")
        notify("tool end")
        data = {'output': output, 'name': name}
        msg = AgentMessage(event=AgentEvents.ToolEnd, data=data)
        self.ctx.app.post_message(msg)

    async def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> Any:
        """Run when tool errors."""
        self._set_agent_state("tool_error")
        notify("tool error")

    async def on_text(self, text: str, **kwargs: Any) -> Any:
        """Run on arbitrary text."""
        notify("lc_ontext")
        msg = AgentMessage(event=AgentEvents.Text, data=text)
        self.ctx.app.post_message(msg)

    async def on_agent_action(self, action: 'AgentAction', **kwargs: Any) -> Any:
        """Run on agent action."""
        self._set_agent_state("agent_action")
        notify(f"agent action: {action.tool}")
        msg = AgentMessage(event=AgentEvents.AgentAction, data=action)
        self.ctx.app.post_message(msg)

    async def on_agent_finish(self, finish: 'AgentFinish', **kwargs: Any) -> Any:
        """Run on agent end."""
        self._set_agent_state("agent_finish")
        notify("agent finish")
        msg = AgentMessage(event=AgentEvents.AgentFinish, data=finish)
        self.ctx.app.post_message(msg)


    #TODO:
    async def on_retriever_end(
            self,
            documents: Sequence["Document"],
            *,
            run_id: UUID,
            parent_run_id: UUID | None = None,
            **kwargs: Any
            ) -> Any:
        # log.debug("on_retriever_end")
        pass
