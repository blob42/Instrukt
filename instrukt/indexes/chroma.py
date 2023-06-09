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
"""Chroma wrapper and utils."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Sequence, cast

from langchain.vectorstores import Chroma as ChromaVectorStore

from ..config import CHROMA_INSTALLED
from ..utils.asynctools import run_async
from .schema import Collection
from .retrieval import retrieval_tool_from_index

if TYPE_CHECKING:
    from chromadb.api.types import Document, Include, QueryResult  # type: ignore
    from langchain.embeddings.base import Embeddings
    from ..config import ChromaSettings
    from ..tools.base import SomeTool

DEFAULT_COLLECTION_NAME = "instrukt"


class ChromaWrapper(ChromaVectorStore):
    """Wrapper around Chroma DB
    
    When used as an async context manager, it will persist the client on exiting
    the context manager. Otherwise, it persist the DB on each call to `add`.

    Example:
        ```python async with Chroma() as chroma:
            await chroma.add([Document(...), ...])
        ```
    """

    def __init__(
            self,
            settings: "ChromaSettings",
            collection_name: str = DEFAULT_COLLECTION_NAME,
            embedding_function: Optional['Embeddings'] = None,
            persist_directory: Optional[str] = None,
            collection_metadata: Optional[Dict[str, Any]] = None,
            **kwargs):
        if not CHROMA_INSTALLED:
            raise ImportError(
                "Instrukt tried to import chromadb, but it is not installed."
                " chromadb is required for using instrukt knowledge features."
                " Please install it with `pip install instrukt[chromadb]`")

        self._persist_directory = persist_directory or settings.persist_directory

        #TODO!: use the stored embedding_fn name to spawn the embedding_fn
        if embedding_function is None:
            import chromadb.utils.embedding_functions as ef  # type: ignore
            embedding_fn = f"{ef.DefaultEmbeddingFunction.__module__}.{ef.DefaultEmbeddingFunction.__name__}"
        else:
            embedding_fn = f"{type(embedding_function).__module__}.{type(embedding_function).__name__}"

        collection_metadata = collection_metadata or {}
        collection_metadata["embedding_fn"] = embedding_fn

        _kwargs = {
            **kwargs,
            **{
                "client_settings": settings,
                "persist_directory": self._persist_directory,
                "collection_name": collection_name,
                "embedding_function": embedding_function,
                "collection_metadata": collection_metadata,
            }
        }
        super().__init__(**_kwargs)

        self._in_context = False  #context manager

    async def __aenter__(self):
        self._in_context = True
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        self._in_context = False
        await run_async(self._client.persist)

    async def adelete(self,
                      ids: list[str] | None = None,
                      where: dict[Any, Any] | None = None):
        await run_async(self._collection.delete, ids=ids, where=where)

    async def apersist(self):
        await run_async(self._client.persist)

    async def adelete_collection(self):
        await run_async(self._client.delete_collection, self._collection.name)

    async def adelete_named_collection(self, collection_name: str):
        await run_async(self._client.delete_collection, collection_name)

    #TODO: async document adding

    async def acount(self) -> int:
        return await run_async(self._collection.count)

    def count(self) -> int:
        return self._collection.count()

    def list_collections(self) -> Sequence[Collection]:
        """Bypass default chroma listing method that does not rely on
        embeddings function."""

        _cols = cast(Sequence[Any], self._client._db.list_collections())
        return [Collection(*col) for col in _cols]

    @property
    def metadata(self) -> dict[Any, Any] | None:
        """Returns the collection metadata."""
        return self._collection.metadata

    @property
    def description(self) -> str | None:
        """Return the collection's description if it exists."""
        # metadata has to be not None and be a dict with the key description
        if self.metadata is not None and "description" in self.metadata:
            return self.metadata["description"]
        return None


    def get_retrieval_tool(self,
                           description: str | None = None,
                           return_direct: bool = False,
                           **kwargs) -> "SomeTool":
        """Get a retrieval tool for this collection."""
        return retrieval_tool_from_index(self,
                                         description,
                                         return_direct=return_direct,
                                         **kwargs)

