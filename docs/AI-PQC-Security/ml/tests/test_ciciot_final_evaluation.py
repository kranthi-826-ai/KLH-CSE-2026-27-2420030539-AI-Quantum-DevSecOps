from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "training"))
from evaluate_frozen_ciciot2023 import evaluate


@pytest.mark.parametrize("marker", ("test-started.json", "result.json"))
def test_final_evaluation_refuses_repeat_before_loading_any_data(tmp_path, marker):
    (tmp_path / marker).write_text("{}")
    with pytest.raises(FileExistsError):
        evaluate(tmp_path)
