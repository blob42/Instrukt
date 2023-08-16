"""Test index module"""
import enum
from random import choice
from string import ascii_lowercase
from pathlib import Path
import instrukt

import pytest
from langchain.text_splitter import Language, RecursiveCharacterTextSplitter

from instrukt.indexes.loaders import (DIRECTORY_LOADER, LOADER_MAPPINGS,
                                      get_loader, splitter_for_file,
                                      AutoDirLoader)
"""
Creating an index should:
    - Use the Index model to represent the new index
    - Decide which loader to use based on the file type 
    - Use directory loader for directories
    - Load document(s) into a loader
    - create split text from the document(s)
    - prepare the vectorstore 
    - load the split text into the vectorstore as embeddings
"""

TEST_TEXT = "This is a test text"


def random_string(length=5):
    return ''.join(choice(ascii_lowercase) for _ in range(length))


def random_file_name(length=10, ext=""):
    file_name = random_string(length)
    if bool(ext):
        return file_name + ext
    else:
        return file_name + random_string()


class TestLoader:

    def test_get_directory_loader(self, tmp_path):
        """directory paths should use a directory loader"""
        path = str(tmp_path)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, DIRECTORY_LOADER[0])

    @pytest.mark.requires("pdfminer")
    @pytest.mark.parametrize("ext, loader_mapping", [
        (".txt", LOADER_MAPPINGS[".txt"][0]),
        (".pdf", LOADER_MAPPINGS[".pdf"][0]),
    ])
    def test_get_loader(self, tmp_path, ext, loader_mapping):
        """file paths should use the correct loader"""
        path = str(tmp_path / f"test{ext}")
        with open(path, "w") as f:
            f.write(TEST_TEXT)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, loader_mapping)

    @pytest.mark.parametrize("ext",
                             [f".{language.value}" for language in Language] +
                             [f".{random_string()}" for _ in range(5)])
    def test_source_code_splitter(self, ext):
        file_name = random_file_name(ext=ext)
        if ext in Language.__members__.values():
            assert isinstance(
                RecursiveCharacterTextSplitter.from_language(ext),
                RecursiveCharacterTextSplitter)

            lang, spl = splitter_for_file(file_name)
            assert spl == RecursiveCharacterTextSplitter.from_language(lang)

        # non handled
        else:
            with pytest.raises(ValueError):
                RecursiveCharacterTextSplitter.from_language(ext)


#FIX:
class TestAutoDirLoader:
    """Test AutoDirLoader"""

    def test_load_directory(self):
        # get the absolute path to the package `instrukt`
        test_dir = Path(instrukt.__file__).parent.parent / 'instrukt'
        loader = AutoDirLoader(test_dir, **DIRECTORY_LOADER[1])
        docs = loader.load()
        print(docs)
