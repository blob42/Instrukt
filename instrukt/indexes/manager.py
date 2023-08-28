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

import contextvars
import importlib
import logging
import typing as t
import uuid

import chromadb  # type: ignore
from chromadb.db.impl.sqlite import SqliteDB  # type: ignore
from langchain.embeddings import (
    HuggingFaceEmbeddings,
    HuggingFaceInstructEmbeddings,
    HuggingFaceBgeEmbeddings,
    OpenAIEmbeddings,
)
from langchain.embeddings.base import Embeddings as LcEmbeddings
from pydantic import BaseModel, Field, PrivateAttr

from ..config import APP_SETTINGS, ChromaSettings
from ..context import context_var
from ..errors import IndexError
from ..indexes.chroma import ChromaWrapper
from ..indexes.loaders import get_loader
from ..indexes.schema import Collection, EmbeddingDetails, Index
from .loaders import LOADER_MAPPINGS, AutoDirLoader

if t.TYPE_CHECKING:
    from ..indexes.chroma import TEmbeddings
    from ..views.index.main import IndexConsole

log = logging.getLogger(__name__)


class IndexManager(BaseModel):
    """Helper to access chroma indexes."""

    chroma_settings: ChromaSettings
    chroma_kwargs: dict[str, t.Any] = Field(default_factory=dict)
    _client: chromadb.Client = PrivateAttr()
    _index: ChromaWrapper = PrivateAttr()
    _indexes: dict[str, ChromaWrapper] = PrivateAttr()

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._indexes: dict[str, ChromaWrapper] = {}
        self._client = chromadb.Client(settings=self.chroma_settings)

    def get_index(self, collection_name: str) -> ChromaWrapper | None:
        """Return the chroma db instance for the given collection name."""

        if collection_name is None or collection_name == "":
            # raise ValueError("Collection name must be specified")
            return None

        if collection_name not in self._indexes:

            # if collection is already stored, restore its embedding_fn
            embedding_inst: TEmbeddings | None = None
            if collection_name in [c.name for c in self.list_collections()]:
                embedding = self.get_embedding_fn(collection_name)
                embedding_fn_cls = self.get_embedding_fn_cls(
                    embedding.embedding_fn_cls)
                if issubclass(
                        embedding_fn_cls,
                    (
                        HuggingFaceEmbeddings,
                        HuggingFaceInstructEmbeddings,
                        HuggingFaceBgeEmbeddings
                    )):
                    embedding_inst = embedding_fn_cls(
                        model_name=embedding.model_name)
                # use default embedding's model name (ie OpenAI ..)

                # handle openai
                elif issubclass(embedding_fn_cls, OpenAIEmbeddings):
                    #ensure openai api key is available
                    if APP_SETTINGS.openai_api_key is None or len(
                            APP_SETTINGS.openai_api_key) == 0:
                        log.warning(
                            "This index was created with OpenAIEmbeddings, "
                            "OpenAI API key required.")
                        return None
                    else:
                        embedding_inst = embedding_fn_cls()  # type: ignore

                else:
                    raise ValueError(
                        "Unknown embedding function used with locally "
                        f"stored index {collection_name}.")

                self.chroma_kwargs['embedding_function'] = embedding_inst

            log.debug(f"loading index <{collection_name}>")
            self._indexes[collection_name] = ChromaWrapper(
                self._client,
                collection_name=collection_name,
                **self.chroma_kwargs)

        return self._indexes[collection_name]

    async def aget_index(self, collection_name: str) -> ChromaWrapper | None:
        """Async version of get_index."""
        from ..utils.asynctools import run_async
        return await run_async(self.get_index, collection_name)

    @property
    def indexes(self) -> t.Sequence[str]:
        """Return the list of loaded indexes."""
        return list(self._indexes.keys())

    def get_loader(self, path: str, loader_type: str | None = None):
        if loader_type is not None:
            _loader = LOADER_MAPPINGS.get(loader_type)
            if _loader is not None:
                loader_cls, loader_kwargs, _ = _loader
                loader = loader_cls(path, **loader_kwargs)  # type: ignore
            else:
                loader = None
        else:
            loader = get_loader(path)

        if loader is None:
            raise IndexError("No loader found for the given path")
        return loader

    def create(self, _ctx: contextvars.Context,
                     index: Index) -> ChromaWrapper | None:
        """Create a new index from the given file or directory path."""

        ctx = _ctx.get(context_var)
        assert ctx is not None

        #WIP:
        # if index.type is defined use specified loader
        loader = self.get_loader(index.path, index.loader_type)

        assert ctx.app is not None, "missing App in Context"
        console = t.cast("IndexConsole", ctx.app.query_one("IndexConsole"))
        assert console is not None
        if isinstance(loader, AutoDirLoader):
            loader.pbar = console.pbar

            if index.glob is not None:
                loader.glob = [index.glob]

        docs = loader.load_and_split()

        if len(docs) == 0:
            return None

        ctx.app.call_from_thread(ctx.app.refresh)

        #NOTE: the used embedding function used is stored within the collection metadata
        # in the chroma wrapper module.

        self.chroma_kwargs['embedding_function'] = index.embedding_fn

        log.debug(f"chroma kwargs: {self.chroma_kwargs})")

        new_index = ChromaWrapper(self._client,
                                  collection_name=index.name,
                                  loading=False,
                                  collection_metadata={
                                      'description': index.description,
                                  },
                                  **self.chroma_kwargs)

        # add documents to index
        console.pbar.update_pbar(total=None, progress=0)
        console.pbar.update_msg("creating embeddings ...")
        with console.pbar.patch_tqdm_update():
            ids = iter(str(uuid.uuid4())[:4] for _ in range(len(docs)))
            for d in docs:
                d.metadata["id"] = next(ids)
            new_index.add_documents(docs)

        self._indexes[index.name] = new_index

        return new_index

    async def adelete_index(self, name: str) -> None:
        """Remove the given index."""
        if name not in self._indexes:
            raise IndexError(f"Index {name} not found")
        index = self._indexes[name]
        await index.adelete_collection()
        del self._indexes[name]

    def list_collections(self) -> t.Sequence[Collection]:
        """List the available index collections."""
        client = chromadb.Client(self.chroma_settings)

        #NOTE: this is the offcial API. It's slow because it checks embedding fn
        return client.list_collections()

    def get_embedding_fn(self, col_name: str) -> EmbeddingDetails:
        """Get embedding function as fully qualified class name for the collection.

        The embedding function is stored in the collection metadata.

        Returns:
            (embedding_fn_cls, Optional[model_name])
        """
        db = SqliteDB(chromadb.System(self.chroma_settings))

        #NOTE: using raw sql
        # with db.tx() as cur:
        #     res = cur.execute("""
        #             SELECT collection_metadata.collection_id,
        #                       collections.name AS collection_name,
        #                       collection_metadata.str_value AS embedding_fn
        #                       FROM collection_metadata
        #                       INNER JOIN collections
        #                       ON collection_metadata.collection_id = collections.id
        #                       WHERE collection_metadata.key = 'embedding_fn'
        #             """).fetchall()

        cols = db.get_collections(name=col_name)
        if len(cols) == 0:
            raise ValueError(
                f"No embedding function found for collection {col_name}")

        if len(cols) > 1:
            raise ValueError(f"Multiple collections named {col_name}")

        try:
            metadata = cols[0]["metadata"]
            embedding_fn = metadata.get("embedding_fn")

            extra_info = {}
            # handle openai missing api key
            if embedding_fn.find("OpenAIEmbeddings") != -1:
                if APP_SETTINGS.openai_api_key is None or \
                        len(APP_SETTINGS.openai_api_key) == 0:
                    extra_info = dict(
                        error="[b yellow]missing openai api key ![/]")

            model_name = metadata.get("model_name")
            return EmbeddingDetails(embedding_fn, model_name, extra_info)
        except IndexError:
            raise IndexError(f"No metadata found for collection {col_name}")

    def get_embedding_fn_cls(self,
                             embedding_fqn: str) -> t.Type["TEmbeddings"]:
        """Get embedding function class for the collection."""
        embedding_cls = get_class(embedding_fqn)
        assert issubclass(embedding_cls, LcEmbeddings)
        return embedding_cls


def get_class(fqn: str) -> t.Type:
    """Given fully qualified class name, return the class."""

    mod_name, cls_name = fqn.rsplit('.', 1)

    try:
        module = importlib.import_module(mod_name)
        return getattr(module, cls_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Failed to import class {fqn}: {e}")


def get_fqn(cls: t.Type[object]) -> str:
    """ Get the fully qualified class name of a given class."""
    return f"{cls.__module__}.{cls.__name__}"
