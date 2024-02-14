from typing import Literal

from .abs import DM_AbsPrompt, DM_AbsUtterance

EXAM_TASK_T = Literal["exam"]
EXAM_TASK: EXAM_TASK_T = "exam"


class DM_ExamPrompt(DM_AbsPrompt[EXAM_TASK_T]):
    task: EXAM_TASK_T = EXAM_TASK
    question: str

    def get_utt(self) -> str:
        return self.question


class DM_ExamUtterance(DM_AbsUtterance[EXAM_TASK_T]):
    task: EXAM_TASK_T = EXAM_TASK
    cot: str
    answer: str

    def get_utt(self) -> str:
        return f"{self.cot} ({self.answer})"
