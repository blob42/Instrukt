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
"""Retrieval from an index with RetrievalQA."""

import logging
import typing as t

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from ...config import APP_SETTINGS
from ...errors import ToolError
from ...tools.base import Tool
from .utils import make_description

log = logging.getLogger(__name__)

if t.TYPE_CHECKING:
    from langchain.chat_models.base import BaseChatModel

    from .chroma import ChromaWrapper


_system_message = """You are Pr. Vivian. Your style is conversational, and you
always aim to get straight to the point. Use the following pieces of context to answer
the users question. If you don't know the answer, just say that you don't know, don't
try to make up an answer. Format the answers in a structured way using markdown. Include snippets from the
context to illustrate your points. Always answer from the perspective of being Pr. Vivian.
----------------
{context}"""

#WIP:
# _with_src_system_message = """You are Pr. Vivian. Your style is conversational, and you
# always aim to get straight to the point. Use the following pieces of context to answer
# the users question. If you don't know the answer, just say that you don't know, don't
# try to make up an answer.
#
# Format the answers in a structured way using markdown. Always answer from the
# perspective of being Pr. Vivian.
# ----------------
# context: {context}"""
# _src_messages =[
#     SystemMessagePromptTemplate.from_template(_with_src_system_message),
#     HumanMessagePromptTemplate.from_template("{question}"),
#         ]
#SRC_CHAT_PROMPT=

_messages = [
    SystemMessagePromptTemplate.from_template(_system_message),
    HumanMessagePromptTemplate.from_template("{question}"),
]
CHAT_PROMPT = ChatPromptTemplate.from_messages(_messages)


def retrieval_tool_from_index(index: "ChromaWrapper",
                              description: str | None = None,
                              return_direct: bool = False,
                              with_sources: bool = False,
                              with_citation: bool = False,
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
        llm = ChatOpenAI(**APP_SETTINGS.openai.dict())
        #TODO!: document changing retrieval param using input `r:gptx` with auto complete
        # llm.model_name="gpt-4"
        llm.temperature=0.3


    if index.count == 0:
        raise ToolError("index is empty")
    name: str = index._collection.name

    description = make_description(description, index, name)


    #TEST: k, mmr ...
    retriever = index.as_retriever(search_type="mmr",
                                   search_kwargs={"k": 8,
                                                  "lambda_mult": 0.8,
                                                  "fetch_k": 30})


    #WIP: add citation support
    if with_citation:
        raise NotImplementedError("citation support not yet implemented")
        #TODO:
        # qa = RetrievalQAWithSourcesChain.from_chain_type(
        #     llm=llm,
        #     retriever=retriever,
        #     reduce_k_below_max_tokens = True,
        #     max_tokens_limit = 2000, #TODO: calc limit from model + prompt
        #     # chain_type_kwargs={
        #     #     "prompt": CHAT_PROMPT,
        #     #     # return_source_documents=True
        #     # },
        # )
        # async def aqa(query, **ret_kwargs):
        #     res = await qa.acall(dict(question=query),
        #                          return_only_outputs=True,
        #                          **ret_kwargs)
        #     log.debug(f"sources: {res['sources']}")
        #     return res["answer"]
        #
        # return Tool(is_retrieval=True,
        #             name=name,
        #             description=description,
        #             func=lambda _: None,
        #             coroutine=aqa,
        #             return_direct=return_direct,
        #             **kwargs)
    else:
        qachain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": CHAT_PROMPT,
            },
        )
        if with_sources:
            qachain.return_source_documents=True
            qachain.output_key="ret_output"
        async def aqa(query, **ret_kwargs):
            return await qachain.acall(dict(query=query),
                                 return_only_outputs=True,
                                 **ret_kwargs)
        return Tool(name=name,
                    description=description,
                    is_retrieval=True,
                    retrieval_runner=qachain,
                    func=lambda _: None,
                    coroutine=aqa,
                    return_direct=return_direct,
                    **kwargs)
