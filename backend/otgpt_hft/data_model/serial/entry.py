"""Representation for serialized data"""

from typing import List

from ..any import AnyPrompt, AnyUtterance
from ..cmp import DB_ResponseCmp
from .store import WithId


class SerializedEntry(WithId):
    prompt: AnyPrompt
    utterance: List[AnyUtterance]
    cmps: List[DB_ResponseCmp]

    def get_id(self) -> str:
        # entry is the prompt id
        return self.prompt.id
