from __future__ import annotations

import asyncio
import logging
import math
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import uuid4

import aiofiles
import aiofiles.os
from pydantic import BaseModel, Field

from otgpt_hft.auth import is_session_logged_in
from otgpt_hft.data_model.abs import InstanceId
from otgpt_hft.data_model.cmp import DB_ResponseCmp
from otgpt_hft.data_model.dialogue.error import DataIntegrityError
from otgpt_hft.data_model.dialogue.graph import DialogueGraph
from otgpt_hft.data_model.source import UserSource
from otgpt_hft.tooling.pub_sub.channel import Channel
from otgpt_hft.utils.bm.channel import wrap_channel_type
from otgpt_hft.utils.min_bg_task import MinBGTasks

from ..data_model.serial.entry import SerializedEntry
from ..data_model.serial.store import Store
from ..tooling.pub_sub.base import ChannelName, SubscriptionAReq, SubscriptionARes
from ..tooling.pub_sub.pub_sub_ex import ExtensiblePubSub, PChannel
from ..tooling.ws.connection import (
    AbsTypedWebSocket,
    FPayloadBM,
    PSession,
    SessionError,
    TypedWebSocketHandler,
    combine_fa_req,
)

logger = logging.getLogger(__name__)


class AnnoRefBM(BaseModel):
    dataset: str
    split: str
    entry: str
    idx: int
    cmpId: Optional[str]


class WhoAmIReq(FPayloadBM[Literal["whoami"]]):
    type: Literal["whoami"] = "whoami"


class WhoAmIRes(FPayloadBM[Literal["whoami"]]):
    type: Literal["whoami"] = "whoami"
    uname: str


class AssignedAnnoReq(FPayloadBM[Literal["assigned-anno"]]):
    """Assigned Annotation Request"""

    type: Literal["assigned-anno"] = "assigned-anno"
    ref: Optional[AnnoRefBM]


class AssignedAnnoRes(FPayloadBM[Literal["assigned-anno"]]):
    """Assigned Annotation Response"""

    type: Literal["assigned-anno"] = "assigned-anno"
    ref: AnnoRefBM
    count: int
    total: int
    a: str
    b: str


class AnnoCmpReq(FPayloadBM[Literal["anno-cmp"]]):
    """Assigned Annotation Request"""

    type: Literal["anno-cmp"] = "anno-cmp"
    ref: AnnoRefBM
    cmp: DB_ResponseCmp


class AnnoCmpRes(FPayloadBM[Literal["anno-cmp"]]):
    """Assigned Annotation Request"""

    type: Literal["anno-cmp"] = "anno-cmp"
    ok: bool


# entry
EntryChannelName = Tuple[
    Literal["entry"], str, str, str
]  # dataset_name, split_name, entry_id

IndexChannelName = Union[
    # list of all datasets
    Tuple[Literal["index"]],
    # list of data splits in the dataset
    # dataset_name
    Tuple[Literal["index"], str],
    # list of data entries in the split
    # dataset_name, split_name
    Tuple[Literal["index"], str, str],
    # dataset_name, split_name, page_idx
    Tuple[Literal["index"], str, str, int],
    # page metadata
    # dataset_name, split_name
    Tuple[Literal["index"], str, str, Literal["meta"]],
]

DBChannelName = Union[
    IndexChannelName,
    EntryChannelName,
]
WDBChannelName = wrap_channel_type(DBChannelName)


class DBDatasetSubReq(SubscriptionAReq[WDBChannelName]):
    """DataBridge Dataset Subscription Request"""


class DBDatasetSubRes(SubscriptionARes[WDBChannelName]):
    """DataBridge Dataset Subscription Response"""


FetchReq = Annotated[
    Union[WhoAmIReq, AssignedAnnoReq, AnnoCmpReq],
    Field(discriminator="type"),
]
FetchRes = Annotated[
    Union[WhoAmIRes, AssignedAnnoRes, AnnoCmpRes],
    Field(discriminator="type"),
]
AsyncReq = DBDatasetSubReq
AsyncRes = DBDatasetSubRes


METADATA_FILENAME = "metadata.json"
PAGE_SIZE = 10


class StoreMetadataBM(BaseModel):
    """Store metadata in 'metadata.json'"""

    title: str
    caption: str
    description: str


class StoreMetadata:
    def __init__(self, id: str, channel: str, bm: StoreMetadataBM):
        self.id = id
        self.bm = bm
        self.pending = True
        self.channel = channel

    def get_item(self) -> Item:
        return Item(
            id=self.id,
            pending=True,
            labels=[],
            channel=self.channel,
            **self.bm.model_dump(),
        )


class Item(BaseModel):
    id: str
    title: str | None
    caption: str | None
    description: str
    pending: bool
    labels: List[str]
    channel: str


class Session(PSession):
    def __init__(
        self,
        db: DataBridge,
        t_ws: AbsTypedWebSocket[Any, Any, Any, Any],
        session_name: str,
        user: str,
    ):
        self.db = db
        self.t_ws = t_ws
        self.user = user

        self.logger = logging.LoggerAdapter(logger, {"session": session_name})

        self.sub_channels: List[ChannelName] = []

    def on_close(self):
        for ch in self.sub_channels:
            self.db.pub_sub.unsubscribe(ch, self.t_ws.send)


DatasetName = str
SplitName = str
SplitAddress = Tuple[DatasetName, SplitName]


class DataBridge(
    TypedWebSocketHandler[Session, FetchReq, FetchRes, AsyncReq, AsyncRes]
):
    ReqType = combine_fa_req(FetchReq, AsyncReq)

    def __init__(self) -> None:
        super().__init__(logging.LoggerAdapter(logger, {"handler": "data-bridge"}))

        self.pub_sub = ExtensiblePubSub()
        self.dataset_to_split: Dict[DatasetName, List[SplitName]] = {}
        self.dataset_meta: Dict[DatasetName, StoreMetadata] = {}
        self.split_meta: Dict[SplitAddress, StoreMetadata] = {}
        self.stores: Dict[SplitAddress, Store[SerializedEntry]] = {}
        self.bg_tasks = MinBGTasks()

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self.bg_tasks.set_loop(loop)

    async def load_data(self, store_path: Path):
        """load and initialize DataBridge data"""
        start_time = time.perf_counter()

        # iterate over directory to load data
        for dataset_name in await aiofiles.os.listdir(store_path):
            dataset_dir = store_path / dataset_name

            # read dataset metadata
            with open(dataset_dir / METADATA_FILENAME) as file:
                self.dataset_meta[dataset_name] = StoreMetadata(
                    id=dataset_name,
                    channel=f"index/{dataset_name}",
                    bm=StoreMetadataBM.model_validate_json(file.read()),
                )

            # list all splits in the dataset
            split_names = await aiofiles.os.listdir(dataset_dir)
            dataset_to_split: List[SplitName] = []

            # load each splits
            for split_name in split_names:
                split_dir = dataset_dir / split_name
                if not await aiofiles.os.path.isdir(split_dir):
                    continue

                dataset_to_split.append(split_name)
                logger.info({"msg": "loading split", "split": split_dir})

                # read split metadata
                with open(split_dir / METADATA_FILENAME) as file:
                    self.split_meta[dataset_name, split_name] = StoreMetadata(
                        id=split_name,
                        channel=f"index/{dataset_name}/{split_name}",
                        bm=StoreMetadataBM.model_validate_json(file.read()),
                    )

                # load split data
                store = Store(
                    SerializedEntry,
                    split_dir,
                )
                self.stores[dataset_name, split_name] = store
                await store.load_chunks()

            self.dataset_to_split[dataset_name] = dataset_to_split

        # NOTE: there is no good way to make typing work for channel prefix
        self.pub_sub.register_hook(("index",), self._index_hook)  # type: ignore
        self.pub_sub.register_hook(("entry",), self._entry_hook)  # type: ignore

        # TODO lazily create DialogueGraph
        DATA_TO_ANNO: List[SplitAddress] = [
            ("Thaweewat-oasst1_th", "dev"),
        ]

        self.dialogue_graphs: Dict[SplitAddress, Dict[InstanceId, DialogueGraph]] = {}

        for dataset_name, split_name in DATA_TO_ANNO:
            store = self.stores[dataset_name, split_name]
            entries = await store.get_entries(0, len(store))

            dialogue_graphs: Dict[InstanceId, DialogueGraph] = {}
            for entry in entries:
                dialogue_graphs[entry.get_id()] = DialogueGraph(entry)

            self.dialogue_graphs[dataset_name, split_name] = dialogue_graphs

        logger.info(
            {
                "msg": "done loading data",
                "duration_s": round(time.perf_counter() - start_time, 3),
            }
        )

    # data bridge methods for preparing data
    def _index_hook(self, ch: IndexChannelName) -> Channel[DBDatasetSubRes]:
        def _on_destroy_index_channel(channel: PChannel) -> None:
            # do nothing
            pass

        channel = Channel(
            ch,
            SARType=DBDatasetSubRes,
            on_empty=_on_destroy_index_channel,
        )

        async def _publish_index_init_msg(
            ch: IndexChannelName, channel: Channel[DBDatasetSubRes]
        ):
            msg = await self._get_index(ch)
            await channel.publish(msg)

        self.bg_tasks.run(_publish_index_init_msg(ch, channel))
        return channel

    async def _get_index(self, ch: IndexChannelName) -> Any:
        if len(ch) == 3:
            ch = *ch, 1
        match (ch):
            case ("index",):
                datasets = sorted(self.dataset_to_split.keys())
                items: List[Item] = []
                for dataset_name in datasets:
                    items.append(self.dataset_meta[dataset_name].get_item())
                return items
            case ("index", dataset_name):
                assert isinstance(
                    dataset_name, str
                ), f"dataset_name must be string, but got {type(dataset_name)}"
                splits = sorted(self.dataset_to_split[dataset_name])
                items: List[Item] = []
                for split_name in splits:
                    items.append(self.split_meta[dataset_name, split_name].get_item())
                return items
            case ("index", dataset_name, split_name, "meta"):
                # TODO handle non-existing `dataset_name`, `split_name`
                total_entries = len(self.stores[dataset_name, split_name])

                return {
                    "totalPage": math.ceil(total_entries / PAGE_SIZE),
                    "totalEntries": total_entries,
                }
            case ("index", dataset_name, split_name, page):
                entry_start = (page - 1) * PAGE_SIZE
                entry_end = page * PAGE_SIZE
                entries = await self.stores[dataset_name, split_name].get_entries(
                    entry_start, entry_end
                )
                items: List[Item] = []
                for entry, idx in zip(entries, range(entry_start + 1, entry_end + 1)):
                    id = entry.get_id()
                    items.append(
                        Item(
                            id=id,
                            title=None,
                            caption=f"{idx}: {id}",
                            description=entry.prompt.get_utt(),
                            pending=True,
                            labels=[],
                            channel=f"entry/{dataset_name}/{split_name}/{id}",
                        )
                    )
                return items
            case _:  # type: ignore
                raise ValueError(
                    "bad index channel, index channel must be `DBChannelName`"
                )

    def _entry_hook(self, ch: EntryChannelName) -> Channel[DBDatasetSubRes]:
        def _on_destroy_entry_channel(channel: PChannel) -> None:
            # do nothing
            pass

        channel = Channel(
            ch,
            SARType=DBDatasetSubRes,
            on_empty=_on_destroy_entry_channel,
        )

        async def _publish_entry_init_msg(
            ch: EntryChannelName, channel: Channel[DBDatasetSubRes]
        ):
            msg = await self._get_entry(ch)
            await channel.publish(msg)

        self.bg_tasks.run(_publish_entry_init_msg(ch, channel))
        return channel

    async def _get_entry(self, ch: EntryChannelName) -> SerializedEntry:
        _, dataset_name, split_name, entry_id = ch
        entry = self.stores[dataset_name, split_name].get(entry_id)
        if entry is None:
            raise ValueError(
                f"entry id '{entry_id}' does not exist in dataset '{dataset_name}' split '{split_name}'"
            )
        # NOTE: cmps store data for all annotators, which is a lot
        #       so remove them for now, until we have a better solution
        # remove cmps data
        entry.cmps = []
        return entry

    # data bridge core methods, for interfacing with TypedWebSocketHandler
    async def create_session(
        self, t_ws: AbsTypedWebSocket[FetchReq, FetchRes, AsyncReq, AsyncRes]
    ) -> Session:
        session_id = str(uuid4())
        if not is_session_logged_in(t_ws.req_session):
            raise SessionError(code=4000, reason="not logged in")
        return Session(self, t_ws, session_id, t_ws.req_session["uname"])

    async def handle_fetch_request(
        self,
        t_ws: AbsTypedWebSocket[FetchReq, FetchRes, AsyncReq, AsyncRes],
        session: Session,
        request: FetchReq,
    ) -> FetchRes:
        # DataBridge do no have any fetch operations ATM
        uname = t_ws.req_session["uname"]
        src_name = UserSource(uname=uname).get_name()

        if isinstance(request, AssignedAnnoReq):
            # resolve SplitAddress
            if request.ref is None:
                # NOTE: the tool only annotated from one data split
                # TODO: remove hard coding
                split_address = "Thaweewat-oasst1_th", "dev"
                dialogue_graphs = self.dialogue_graphs[split_address]

                for entry_id, dialogue_graph in dialogue_graphs.items():
                    cmp = dialogue_graph.root.get_cmp(src_name)
                    pairs_w_rel_count, total_pairs, pairs_wo_rel = (
                        cmp.compute_coverage()
                    )
                    if pairs_w_rel_count == total_pairs:
                        continue

                    assert pairs_wo_rel is not None
                    entry = entry_id
                    idx = len(cmp.raw_cmp_data)
                    a, b = pairs_wo_rel

                    return AssignedAnnoRes(
                        id=request.id,
                        ref=AnnoRefBM(
                            dataset=split_address[0],
                            split=split_address[1],
                            entry=entry,
                            idx=idx,
                            cmpId=str(uuid4()),
                        ),
                        count=pairs_w_rel_count,
                        total=total_pairs,
                        a=a,
                        b=b,
                    )

                # fallback for end of annotation
                entry_id = list(dialogue_graphs.keys())[-1]
                dialogue_graph = dialogue_graphs[entry_id]

                cmp = dialogue_graph.root.get_cmp(src_name)
                pairs_w_rel_count, total_pairs, _ = cmp.compute_coverage()
                assert pairs_w_rel_count == total_pairs

                idx = len(cmp.raw_cmp_data) - 1
                raw_cmp_data = cmp.raw_cmp_data[idx]
                a = raw_cmp_data.a
                b = raw_cmp_data.b

                return AssignedAnnoRes(
                    id=request.id,
                    ref=AnnoRefBM(
                        dataset=split_address[0],
                        split=split_address[1],
                        entry=entry_id,
                        idx=idx,
                        cmpId=str(uuid4()),
                    ),
                    count=pairs_w_rel_count,
                    total=total_pairs,
                    a=a,
                    b=b,
                )
            else:
                split_address = request.ref.dataset, request.ref.split
                dialogue_graph = self.dialogue_graphs[split_address][request.ref.entry]
                # TODO add support for non-root anno
                cmp = dialogue_graph.root.get_cmp(src_name)
                pairs_w_rel_count, total_pairs, pairs_wo_rel = cmp.compute_coverage()

                if request.ref.idx >= len(cmp.raw_cmp_data):
                    if pairs_wo_rel is not None:
                        request.ref.idx = len(cmp.raw_cmp_data)
                    else:
                        request.ref.idx = len(cmp.raw_cmp_data) - 1

                if request.ref.idx < len(cmp.raw_cmp_data):
                    raw_cmp_data = cmp.raw_cmp_data[request.ref.idx]
                    a = raw_cmp_data.a
                    b = raw_cmp_data.b
                else:
                    assert pairs_wo_rel is not None
                    a, b = pairs_wo_rel

                return AssignedAnnoRes(
                    id=request.id,
                    ref=request.ref,
                    count=pairs_w_rel_count,
                    total=total_pairs,
                    a=a,
                    b=b,
                )
        elif isinstance(request, AnnoCmpReq):
            split_address = request.ref.dataset, request.ref.split
            dialogue_graph = self.dialogue_graphs[split_address][request.ref.entry]
            # TODO add support for non-root anno
            cmp = dialogue_graph.root.get_cmp(src_name)
            cmp.add_cmp_data(request.cmp)

            # analyze every time we make annotations to data
            try:
                dialogue_graph.find_issues(inspect=True)
            except DataIntegrityError as e:
                print(e.info)
                return AnnoCmpRes(id=request.id, ok=False)

            store = self.stores[split_address]
            serial = store.get(request.ref.entry)
            assert serial is not None
            # TODO handle replacement
            serial.cmps.append(request.cmp)
            await store.set(serial, replace_if_exist=True)
            await store.save()
            return AnnoCmpRes(id=request.id, ok=True)
        else:
            assert isinstance(request, WhoAmIReq)
            return WhoAmIRes(
                id=request.id,
                uname=uname,
            )

    async def handle_async_request(
        self,
        t_ws: AbsTypedWebSocket[FetchReq, FetchRes, AsyncReq, AsyncRes],
        session: Session,
        request: AsyncReq,
    ) -> bool:
        # DataBridge only have two async requests, sub and unsub
        assert isinstance(request, DBDatasetSubReq)
        if request.type == "sub":
            assert request.channel not in session.sub_channels
            session.sub_channels.append(request.channel)
            await self.pub_sub.subscribe(
                request.channel,
                t_ws.send,  # type: ignore
            )
        else:
            assert request.type == "unsub"
            assert request.channel in session.sub_channels
            self.pub_sub.unsubscribe(
                request.channel,
                t_ws.send,  # type: ignore
            )
            session.sub_channels.remove(request.channel)
        return True
