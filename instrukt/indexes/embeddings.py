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
"""Embeddings used in indexes."""
#TODO: CUDA
import typing as t
from typing import NamedTuple

from langchain.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
    OpenAIEmbeddings,
)

if t.TYPE_CHECKING:
    from langchain.embeddings.base import Embeddings


class Embedding(NamedTuple):
    """Wrappers and helpers for an embedding function/model used in an index."""
    name: str
    fn: t.Type["Embeddings"]
    kwargs: t.Dict[str, t.Any]


EMBEDDINGS: dict[str, Embedding] = {
    "default":
    Embedding("Sentence Transormers (xs)", HuggingFaceEmbeddings,
              dict(model_name="sentence-transformers/all-MiniLM-L6-v2", )),
    "bge-base-en":
    Embedding("BGE Base EN", HuggingFaceEmbeddings,
              dict(model_name="BAAI/bge-base-en",
                    # set True to compute cosine similarity)
                   encode_kwargs = {'normalize_embeddings': True}
                   )), 
    "mpnet-base-v2":
    Embedding("Sentence Transormers", HuggingFaceEmbeddings,
              dict(model_name="sentence-transformers/all-mpnet-base-v2", )),
    "instructor":
    Embedding("Instructor (base)", HuggingFaceInstructEmbeddings,
              dict(
                  #TODO: use instructor-large
                  model_name="hkunlp/instructor-base", 
                  embed_instruction='Represent the document for retrieval: ',
                  query_instruction='Represent the question for retrieving supporting documents: ',
                  encode_kwargs = dict(show_progress_bar=True)
                  )),
    "openai":
    Embedding("OpenAI", OpenAIEmbeddings, dict()),
              }

