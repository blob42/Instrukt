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
"""Index retrieval utils."""

import typing as t

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from ..errors import ToolError
from ..tools.base import Tool
from ..config import APP_SETTINGS

if t.TYPE_CHECKING:
    from langchain.chat_models.base import BaseChatModel

    from .chroma import ChromaWrapper

TOOL_DESC_FULL = """Useful to lookup information about {{{{{name}}}}}. {tool_desc}."""
TOOL_DESC_SIMPLE = """Useful to lookup information about {{{{{name}}}}}."""

_system_message = """You are Dr. Vivian Quill. Your style is conversational, and you
always aim to get straight to the point. Use the following pieces of context to answer
the users question. If you don't know the answer, just say that you don't know, don't
try to make up an answer.

Format the answers in a structured way using markdown. Always answer from the
perspective of being Dr. Vivian.
----------------
{context}"""

_messages = [
    SystemMessagePromptTemplate.from_template(_system_message),
    HumanMessagePromptTemplate.from_template("{question}"),
]
CHAT_PROMPT = ChatPromptTemplate.from_messages(_messages)


def retrieval_tool_from_index(index: "ChromaWrapper",
                              description: str | None = None,
                              return_direct: bool = False,
                              llm: t.Optional["BaseChatModel"] = None,
                              **kwargs) -> Tool:
    """Return a tool from the given index name.

    The name is used as a key to retrieve the collection from the index manager.

    Args:
        name: The name of the index to retrieve.
        manager: The index manager.
        description: The tool description. Defaults to None.
        llm: The language model. Defaults to ChatOpenAI().
        **kwargs: Additional Tool kwargs.
    """

    if llm is None:
        llm = ChatOpenAI(**APP_SETTINGS.openai.dict(exclude={"temperature", "model"}),
                         model="gpt-3.5-turbo-0613",
                         temperature=0.6)

    if index.count() == 0:
        raise ToolError("index is empty")
    name = index._collection.name

    #TEST:
    if description is None:
        if index.metadata is not None:
            desc = index.metadata.get("description")
            if desc is not None:
                description = TOOL_DESC_FULL.format(name=name, tool_desc=desc)
            else:
                description = TOOL_DESC_SIMPLE.format(name=name)
        else:
            description = TOOL_DESC_SIMPLE.format(name=name)

    retriever = index.as_retriever(search_kwargs={"k": 4})

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={
            "prompt": CHAT_PROMPT,
        }

        #TODO!: catch source documents
        # return_source_documents=True
    )

    return Tool(is_retrieval=True,
                name=name,
                description=description,
                func=qa.run,
                coroutine=qa.arun,
                return_direct=return_direct,
                **kwargs)
