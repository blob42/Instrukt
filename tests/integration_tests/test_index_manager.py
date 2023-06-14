from pathlib import Path

import pytest

from instrukt.config import CHROMA_INSTALLED, ChromaSettings
from instrukt.context import Context
from instrukt.indexes.manager import IndexManager
from instrukt.indexes.schema import Index
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter


@pytest.fixture(name="ctx")
def context(mocker):
    mocked_ctx = mocker.Mock(spec=Context)
    mocker.patch.object(mocked_ctx, "info", return_value=None)
    return mocked_ctx



@pytest.fixture
def index_manager(ctx, tmp_path):
    chroma_settings = ChromaSettings(persist_directory=str(tmp_path))
    return IndexManager(chroma_settings=chroma_settings,
                        chroma_kwargs=dict(embedding_function=None))

class TestIndexManager:

    #WIP: indexing a simple text document
    @pytest.mark.skipif(not CHROMA_INSTALLED, reason="chromadb not installed")
    @pytest.mark.asyncio
    async def test_create_base(self, ctx, index_manager):
        # test document is ./examples/document.txt
        test_file = Path(__file__).parent / "examples" / "bitcoin.txt"

        newindex=Index(name="test_collection", path=str(test_file))
        index = await index_manager.create(ctx, newindex)

        test_file2 = Path(__file__).parent / "examples" / "attention.txt"
        docs = TextLoader(file_path=str(test_file2)).load()
        text_splitter = CharacterTextSplitter()
        texts = text_splitter.split_documents(docs)
        index.add_documents(texts)


        assert index._collection.name == "test_collection"
        assert index._collection.count() > 0


        doc1, score1 = index.similarity_search_with_score("p2p payment system", k=1)[0]
        assert doc1.metadata['source'].find("bitcoin") != -1
        doc2, score2 = index.similarity_search_with_score("deep neural network", k=1)[0]
        assert doc2.metadata['source'].find("attention") != -1

        close = index.similarity_search_with_score("p2p payment system")[0][1]
        far = index.similarity_search_with_score("natural language processing")[0][1]
        assert far > close

    @pytest.mark.asyncio
    async def test_create_non_existing_file(self, index_manager, ctx):
        path = Path(__file__).parent / "examples" / "non_existing.txt"
        
        # should raise some error
        with pytest.raises(Exception):
            await index_manager.create(ctx, Index(name="test", path=str(path)))

    @pytest.mark.asyncio
    async def test_create_text_file(self, index_manager, ctx):
        path = Path(__file__).parent / "examples" / "bitcoin.txt"
        assert await index_manager.create(ctx, Index(name="test", path=str(path)))
        assert ctx.info.called
        index = index_manager.get_index("test")
        assert index is not None
        assert index._collection.name == "test"

