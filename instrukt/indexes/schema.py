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
"""Indexes Schemas"""

import os
import typing as t
from typing import Any, NamedTuple, Optional

from langchain.embeddings.base import Embeddings
from pydantic import BaseModel, Field, validator

from ..config import APP_SETTINGS
from .embeddings import EMBEDDINGS
from .loaders import LOADER_MAPPINGS


class Collection(NamedTuple):
    """An index collection"""
    id: str
    name: str
    metadata: dict[Any, Any]

class EmbeddingDetails(NamedTuple):
    """Details about an embedding"""
    embedding_fn_cls: str
    model_name: str | None = None
    extra: dict[str, t.Any] = {}
    """extra information about this embedding"""

    @property
    def fn_short(self) -> str:
        """Shortened functipn name."""
        return self.embedding_fn_cls.split(".")[-1]


def v_non_empty_field(fname: str, v: t.Sequence[t.Any]) -> Any:
    """Generic non empty field validator."""
    if len(tuple(v)) == 0:
        raise ValueError(f"{fname} cannot be empty")
    return v


class Index(BaseModel):
    """Base Instrukt Index class.

    Indexes are the the document storing and retrieval backend for agents."""
    name: str

    #TODO: make this a list of paths with its corresponding loader
    path: str
    description: str
    embedding: str = "default"
    loader_type: str | None = None  # auto detected or selected
    metadata: Optional[dict[Any, Any]] = Field(default_factory=dict)
    glob: str | None = None
    """custom glob for matching files"""



    @validator("path")
    def validate_path(cls, v: str) -> str:
        """Ensure path is absolute"""
        if len(v) == 0:
            raise ValueError("Path cannot be empty")

        v = os.path.expanduser(v)
        v = os.path.abspath(v)

        if not os.path.exists(v):
            # shorten home path
            v = "~/" + os.path.relpath(v, os.path.expanduser("~"))
            raise ValueError(f"wrong path: {v}")

        return v


    @validator("name")
    def validate_non_empty(cls, v: str) -> str:
        """Ensure name is not empty"""
        return v_non_empty_field("name", v)

    @validator("description")
    def validate_description(cls, v: str) -> str:
        return v_non_empty_field("description", v)
        

    @validator("loader_type")
    def validate_loader_type(cls, v: str) -> str:
        """Ensure loader type is valid"""
        if v not in LOADER_MAPPINGS and v is not None:
            raise ValueError(
                f"Invalid loader type: {v}\n  "
                f"Should be one of {list(LOADER_MAPPINGS.keys())}\n")

        return v

    # validator for embedding
    # if embedding is the "openai" key of EMBEDDINGS raise error
    @validator("embedding")
    def validate_embedding(cls, v: str) -> str:
        """Ensure embedding is valid"""
        # if v is the one under the EMBEDDINGS["openai"] key
        if v not in EMBEDDINGS and v is not None:
            raise ValueError(
                    f"Invalid Embedding type: {v}\n "
                    f" Should be one of {list(EMBEDDINGS.keys())}\n"
                    )
        if v == "openai" and not APP_SETTINGS.has_openai:
            raise ValueError("OpenAI API key not set")
        return v

    @property
    def embedding_fn(self) -> Embeddings:
        """Get the embedding function"""
        embedding = EMBEDDINGS[self.embedding]
        return embedding.fn(**embedding.kwargs)
