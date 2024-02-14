"""Representation for data events (modification, delete, creation)"""


from pydantic import BaseModel

from .address import WAddress

# class CreationEvent(BaseModel):
#     pass


class ModifyEvent(BaseModel):
    # address
    add: WAddress
