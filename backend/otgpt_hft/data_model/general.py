from typing import Literal

from .abs import DM_AbsPrompt, DM_AbsUtterance

GENERAL_TASK_T = Literal["general"]
GENERAL_TASK: GENERAL_TASK_T = "general"


class DM_GeneralPrompt(DM_AbsPrompt[GENERAL_TASK_T]):
    task: GENERAL_TASK_T = GENERAL_TASK
    utt: str

    def get_utt(self) -> str:
        return self.utt


class DM_GeneralUtterance(DM_AbsUtterance[GENERAL_TASK_T]):
    task: GENERAL_TASK_T = GENERAL_TASK
    utt: str

    def get_utt(self) -> str:
        return self.utt
