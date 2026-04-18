import os
import sys
from pathlib import Path


_tag_home = os.environ.get("TAG_HOME", "")
_candidate_paths = []

if _tag_home:
    candidate = Path(_tag_home)
    if candidate.is_dir():
        _candidate_paths.append(candidate)

_source_root = Path(__file__).resolve().parents[2]
_candidate_paths.append(_source_root)

for _path in _candidate_paths:
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)
