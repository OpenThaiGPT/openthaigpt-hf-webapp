from typing import Literal

from .abs import DM_Abs, InstanceId

CompareOp = Literal[">", "="]


class DB_ResponseCmp(DM_Abs[Literal["cmp"]]):
    cls: Literal["cmp"] = "cmp"
    # id: InstanceId is prefix with "r_"
    # "a" is better/prefered over "b"
    a: InstanceId
    b: InstanceId
    cmp: CompareOp
