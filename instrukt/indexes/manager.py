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
"""Manage underlying indexes."""

import typing as t
from pathlib import Path
import chromadb   # type: ignore 

from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field, PrivateAttr

from ..config import ChromaSettings
from ..context import Context
from ..indexes.chroma import DEFAULT_COLLECTION_NAME, ChromaWrapper
from ..indexes.schema import Collection, Index
from ..indexes.loaders import get_loader
from ..errors import IndexError
from ..utils.asynctools import run_async
from .loaders import LOADER_MAPPINGS



class IndexManager(BaseModel):
    """Helper to access chroma indexes."""

    chroma_settings: ChromaSettings
    _index: ChromaWrapper = PrivateAttr()
    _indexes: dict[str, ChromaWrapper] = PrivateAttr()
    chroma_kwargs: dict[str, t.Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._indexes: dict[str, ChromaWrapper] = {}

    def get_index(
            self,
            collection_name: str) -> ChromaWrapper | None:
        """Return the chroma db instance for the given collection name."""
        if collection_name is None:
            raise ValueError("Collection name must be specified")

        if collection_name not in self._indexes:
            self._indexes[collection_name] = ChromaWrapper(
                self.chroma_settings,
                collection_name=collection_name,
                **self.chroma_kwargs)

        return self._indexes[collection_name]

    @property
    def indexes(self) -> t.Sequence[str]:
        """Return the list of loaded indexes."""
        return list(self._indexes.keys())

    async def create(
            self,
            ctx: Context,
            index: Index) -> ChromaWrapper | None:
        """Create a new index from the given file or directory path."""

        ctx.info(f"creating index {index.name} from {index.path}")

        #WIP:
        # if index.type is defined use specified loader
        if index.loader_type is not None:
            _loader = LOADER_MAPPINGS.get(index.loader_type)
            if _loader is not None:
                loader_cls, loader_kwargs = _loader
                loader = loader_cls(index.path, **loader_kwargs)   # type: ignore 
            else:
                loader = None
        else:
            loader = get_loader(index.path)

        if loader is None:
            raise IndexError("No loader found for the given path")

        # naive implementation of doc loading
        #TODO!: cutomize splitting/chunking heuristics per loader/data type
        #TODO!: implement custom parallel directory loader
        docs = await run_async(loader.load_and_split)

        ctx.info(f"loaded {len(docs)} documents")


        #NOTE: the used embedding function used is stored within the collection metadata
        # at the wrapper level.
        new_index = ChromaWrapper(self.chroma_settings,
                              collection_name=index.name,
                              collection_metadata={
                                  'description': index.description, 
                                  },
                              **self.chroma_kwargs)

        ctx.info(f"adding {len(docs)} documents to index")

        # add documents to texts
        await run_async(new_index.add_documents, docs)

        ctx.info(f"index {index.name} created")

        self._indexes[index.name] = new_index
        await run_async(new_index.persist)

        ctx.info(f"index persisted")

        return new_index
    
    async def remove_index(self, name: str) -> None:
        """Remove the given index."""
        if name not in self._indexes:
            raise IndexError(f"Index {name} not found")
        index = self._indexes[name]
        await index.adelete_collection()
        await index.apersist()
        del self._indexes[name]


    def list_collections(self) -> t.Sequence[Collection]:
        """List the available index collections."""
        client = chromadb.Client(self.chroma_settings)

        #NOTE: this is the offcial API. It's slow because it checks embedding fn
        # return  client.list_collections()

        #HACK: bypass chroma and manually list the duckdb collections
        _cols = t.cast(t.Sequence[t.Any], client._db.list_collections())
        return [Collection(*col) for col in _cols]
