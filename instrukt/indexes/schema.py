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
from typing import Any, NamedTuple, Optional

from pydantic import BaseModel, Field, validator

from .loaders import LOADER_MAPPINGS
from .embeddings import Embedding, EMBEDDINGS


class Collection(NamedTuple):
    """An index collection"""
    id: str
    name: str
    metadata: dict[Any, Any]

class EmbeddingDetails(NamedTuple):
    """Details about an embedding"""
    embedding_fn_cls: str
    model_name: str | None


class Index(BaseModel):
    """Base Instrukt Index class.

    Indexes are the the document storing and retrieval backend for agents."""
    name: str

    #TODO: make this a list of paths with its corresponding loader
    path: str
    embedding: str = "default"
    description: str | None = None
    loader_type: str | None = None  # auto detected or selected
    metadata: Optional[dict[Any, Any]] = Field(default_factory=dict)

    @validator("path")
    def validate_path(cls, v: str) -> str:
        """Ensure path is absolute"""
        if len(v) == 0:
            raise ValueError("Path cannot be empty")

        v = os.path.expanduser(v)
        v = os.path.abspath(v)

        if not os.path.exists(v):
            raise ValueError(f"Path does not exist: {v}")

        return v

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
        if v == "openai":
            raise ValueError("requires OpenAI API key")
        return v

