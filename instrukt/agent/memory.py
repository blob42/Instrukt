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
"""Agent short and long term memory."""

import typing as t
from langchain.memory import ConversationBufferMemory as LcConversationBufferMemory
from langchain.memory import ConversationBufferWindowMemory as LcConversationBufferWindowMemory
from langchain.memory.chat_memory import BaseChatMemory
from pydantic import BaseModel


class BaseRetrievalMemoryMixin(BaseChatMemory):
    """Custom class to accomodate Retrieval QA chains."""

    ret_output_key: str = "ret_output"
    """Key to use to retrieve the output from the retriever."""

    def _get_input_output(
        self, inputs: dict[str, t.Any], outputs: dict[str, t.Any]
    ) -> tuple[str, str]:

        # if outputs is a dict try to
        if self.output_key is None and len(outputs) == 1:
            output_key = list(outputs.keys())[0]
            # if this is coming from a retriever
            if isinstance(outputs[output_key],
                          dict) and self.ret_output_key in outputs[output_key]:
                # return only the ret_output in a new dict
                return super()._get_input_output(
                    inputs, {output_key: outputs[output_key][self.ret_output_key]})

        return super()._get_input_output(inputs, outputs)

    def save_context(self, inputs: dict[str, t.Any], outputs: dict[str, str]) -> None:
        """Save context from this conversation to buffer."""
        input_str, output_str = self._get_input_output(inputs, outputs)
        self.chat_memory.add_user_message(input_str)
        self.chat_memory.add_ai_message(output_str)

class ConversationBufferMemory(BaseRetrievalMemoryMixin, LcConversationBufferMemory):
    pass

class ConversationBufferWindowMemory(BaseRetrievalMemoryMixin,
                                     LcConversationBufferWindowMemory):
    pass

def make_buffer_mem() -> BaseChatMemory:
    return ConversationBufferMemory(memory_key="chat_history",
                                    return_messages=True)

def make_buffer_window_mem(k: int = 5) -> BaseChatMemory:
    return ConversationBufferWindowMemory(memory_key="chat_history",
                                    k=k,
                                    return_messages=True)
