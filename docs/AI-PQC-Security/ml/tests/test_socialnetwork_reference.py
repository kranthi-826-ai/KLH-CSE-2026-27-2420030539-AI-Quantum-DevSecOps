from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from train_socialnetwork_reference import check_metadata, matrix


def fixtures():
    train = {"training_metadata": [{"small_text": [{"name": "commands_test.txt", "text": "100;110\ncontainer"}]}]}
    validation = {"validation_metadata": [{"archive": f"/{s}.tar.gz", "small_text": [
        {"name": "test/collection-1/30min_NO_attack_experiment.txt",
         "text": "Attack: NONE\nStart date: sex jun 23 18:27:32 WEST 2023\n"}]} for s in ("scenario5", "scenario3")]}
    return train, validation


def test_normal_intervals_have_timezone_and_explicit_duration():
    exclusions, intervals = check_metadata(*fixtures())
    assert exclusions == [(99, 111)]
    assert intervals["scenario5"] == (1687541252, 1687543052)


def test_attack_word_is_not_normal_label():
    train, validation = fixtures()
    validation["validation_metadata"][0]["small_text"][0]["text"] = "task attack_socialnetwork_mixed"
    with pytest.raises(ValueError, match="annotation missing"):
        check_metadata(train, validation)


def test_too_few_windows_cannot_train():
    with pytest.raises(ValueError):
        matrix([])
