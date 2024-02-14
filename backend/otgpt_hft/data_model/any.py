from typing import Annotated, Union

from pydantic import Field

from .exam import DM_ExamPrompt, DM_ExamUtterance
from .general import DM_GeneralPrompt, DM_GeneralUtterance

AnyPrompt = Annotated[
    Union[
        DM_GeneralPrompt,
        DM_ExamPrompt,
    ],
    Field(discriminator="task"),
]

AnyUtterance = Annotated[
    Union[
        DM_GeneralUtterance,
        DM_ExamUtterance,
    ],
    Field(discriminator="task"),
]

AnyDialogueUnit = Annotated[
    Union[
        AnyPrompt,
        AnyUtterance,
    ],
    Field(discriminator="task"),
]
