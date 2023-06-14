"""Test index module"""
import pytest

from instrukt.indexes.loaders import DIRECTORY_LOADER, LOADER_MAPPINGS, get_loader

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


class TestLoader:

    def test_get_directory_loader(self, tmp_path):
        """directory paths should use a directory loader"""
        path = str(tmp_path)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, DIRECTORY_LOADER[0])


    @pytest.mark.requires("pdfminer")
    @pytest.mark.parametrize(
        "ext, loader_mapping",
        [
            (".txt", LOADER_MAPPINGS[".txt"][0]),
            (".pdf", LOADER_MAPPINGS[".pdf"][0]),
        ]
    )
    def test_get_loader(self, tmp_path, ext, loader_mapping):
        """file paths should use the correct loader"""
        path = str(tmp_path / f"test{ext}")
        with open(path, "w") as f:
            f.write(TEST_TEXT)
        loader = get_loader(path)
        assert loader is not None
        assert isinstance(loader, loader_mapping)
