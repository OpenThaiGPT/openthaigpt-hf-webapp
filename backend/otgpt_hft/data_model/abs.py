from abc import abstractmethod
from typing import Generic, List, Literal, TypeVar

from pydantic import BaseModel

from .source import AnySource

T = TypeVar("T", bound=str)
T2 = TypeVar("T2", bound=str)

InstanceId = str


class DM_Abs(BaseModel, Generic[T]):
    id: InstanceId
    cls: T
    source: AnySource


class DM_AbsTask(DM_Abs[T], Generic[T, T2]):
    task: T2
    author: Literal["user", "agent"]

    @abstractmethod
    def get_utt(self) -> str:
        ...


class DM_AbsPrompt(DM_AbsTask[Literal["pmpt"], T2]):
    cls: Literal["pmpt"] = "pmpt"
    # id: InstanceId is prefix with "p_"
    tags: List[str]  # tags of prompt entry `split_type`(train/dev/test), `dataset_name`


def id_is_prompt(id: InstanceId) -> bool:
    return id.startswith("p_")


class DM_AbsUtterance(DM_AbsTask[Literal["utt"], T2]):
    cls: Literal["utt"] = "utt"
    # id: InstanceId is prefix with "r_"
    prev_id: InstanceId

    # TODO: check if we need root_id
    # root_id: Optional[InstanceId] = None

    # def resolve_root(self):
    #     if self.root_id is None:
    #         if prev_id
    #     return self.root_id
