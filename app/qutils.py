from __future__ import annotations
import json
from typing import Tuple

MCQ_TYPES = {"mcq_single","mcq_multi","true_false","image_mcq_single","video_cued_mcq_single"}

def is_approvable(qtype: str, options_json: str | None, answer_json: str | None) -> Tuple[bool,str]:
    if qtype in MCQ_TYPES:
        if not options_json:
            return False, "Options are required for this question type."
        try:
            opts = json.loads(options_json)
        except Exception:
            return False, "Options JSON invalid."
        if not isinstance(opts, list) or len(opts) < 2:
            return False, "At least 2 options are required."
        if not answer_json:
            return False, "Answer is required."
        # basic parse
        try:
            ans = json.loads(answer_json)
        except Exception:
            return False, "Answer JSON invalid."
        if qtype == "mcq_multi":
            if not isinstance(ans, list) or len(ans) == 0:
                return False, "Answer must be a non-empty list of indices."
        else:
            if not isinstance(ans, int):
                return False, "Answer must be an integer index."
    elif qtype == "short_text":
        if not answer_json:
            return False, "Answer is required for short_text."
    return True, ""
