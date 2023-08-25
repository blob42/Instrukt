import typing as t
from pathlib import Path

import pytest

from instrukt.output_parsers.multi_strategy import ConvMultiStrategyParser
from instrukt.output_parsers.strategies import (
    json_react_strategies,
    fix_json_with_embedded_code_block,
    json_recover_final_answer
)

# @pytest.fixture
# def parser():
#     return TestOutputParser()
#
#EXAMPLE:
# @pytest.mark.golden_test("golden/output_parser/*.yml")
# def test_react_action_inputs(self, golden):
#     assert get_action_and_input(golden["input"])== (golden.out["action"],
#                                                     golden.out["action_input"])

# @pytest.mark.golden_test("golden/output_parser/*code_block.yml")
# def test_parse_code_block(golden, parser):
#     assert parser.parse(golden["input"]) == (golden.out["action"],
#                                              golden.out["action_input"],
#                                              golden.out["input"]
#                                              )

# This will test the ConvoMultiStrategyParser
# the files under ./data/llm_outputs/* represent test outputs from the llm
# every file will be loaded and passed through the differnt parsers in the following
# tests.
# A helper fixture will be used to load the files and return the text


def gather_llm_outputs() -> t.List[t.Tuple[str, str]]:
    """Return a list of strings, each string is a test output from the llm."""
    outputs = []
    for path in (Path(__file__).parent / "data/llm_outputs/").glob("*"):
        with open(str(path), "r") as f:
            outputs.append((f.read(), path.name))
    return outputs

llm_outputs = gather_llm_outputs()


@pytest.mark.parametrize("output, name", llm_outputs, ids=[x[1] for x in llm_outputs])
def test_json_react_strategies(output, name, parser):
    _test_json_react_strategy(output, name, parser)

def _test_json_react_strategy(output, name, parser):
        try:
            res = parser.parse(output)
        except Exception as e:
            pytest.fail(f"Error parsing output entry: {name}.")

def test_fix_json_with_embedded_code_block():
    path =  (Path(__file__).parent / "data/llm_outputs/bare_json_embed_code_block")
    with open(str(path), "r") as f:
        output = f.read()
    res = fix_json_with_embedded_code_block(output)
    assert type(res) == dict
    with pytest.raises(Exception):
        res = fix_json_with_embedded_code_block(output, max_loop=1)

def test_fix_broken_final_answer():
    path =  (Path(__file__).parent / "data/llm_outputs/broken_final_answer")
    with open(str(path), "r") as f:
        output = f.read()
    res = json_recover_final_answer(output)
    assert type(res) == dict
    assert output.find(res["action_input"]) != -1



@pytest.fixture(name="parser")
def conv_multi_strategy_parser():
    return ConvMultiStrategyParser(json_react_strategies)




