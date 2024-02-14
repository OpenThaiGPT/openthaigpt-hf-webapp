from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

SourceName = str


class AbsSource(BaseModel):

    def get_name(self) -> SourceName: ...


class OAnnoSource(AbsSource):
    """Source is from original annotation of the dataset"""

    t: Literal["oanno"] = "oanno"
    name: str

    def get_name(self) -> SourceName:
        return f"{self.t}/{self.name}"


class ModelSource(AbsSource):
    """Source is from model inference"""

    t: Literal["model"] = "model"
    name: str

    def get_name(self) -> SourceName:
        return f"{self.t}/{self.name}"


Uname = str


class UserSource(AbsSource):
    """Source is from user annotation"""

    t: Literal["user"] = "user"
    uname: Uname

    def get_name(self) -> SourceName:
        return f"{self.t}/{self.uname}"


AnySource = Annotated[
    Union[
        OAnnoSource,
        UserSource,
        ModelSource,
    ],
    Field(discriminator="t"),
]
