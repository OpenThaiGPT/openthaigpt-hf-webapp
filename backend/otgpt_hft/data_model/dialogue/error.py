from typing import Any, Dict


class DataIntegrityError(Exception):

    def __init__(self, info: Dict[str, Any]):
        super().__init__()
        self.info = info
