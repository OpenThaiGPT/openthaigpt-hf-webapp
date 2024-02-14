import asyncio
import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Generic, List, Optional, Type, TypeVar

import aiofiles.os
from pydantic import BaseModel

from ...utils.file import create_file_atomically, safe_write_file
from ..abs import InstanceId

DEFAULT_CHUNK_SIZE = 1024


class WithId(BaseModel, ABC):
    """Seralizable object with an ID"""

    @abstractmethod
    def get_id(self) -> InstanceId: ...


I = TypeVar("I", bound=WithId)

CHUNK_FILENAME_PATTERN = r"chunk_(\d+)\.json"


class Store(Generic[I]):
    def __init__(
        self,
        entry_cls: Type[I],
        chunk_dir: Path,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ):
        self._chunk_dir = chunk_dir
        self._chunk_size = chunk_size
        self._entry_cls = entry_cls
        # mapping from id to the entires being stored
        self._store: Dict[str, I] = {}

        # chunking information
        # mapping from id to chunk index
        self._id2chunk: Dict[str, int] = {}
        # mapping from chunk id to entry id
        self._chunk2id: Dict[int, List[str]] = {}
        # chunks with capacity
        self._chunk_with_capacity: List[int] = []
        # set of chunk idx which require to be save (has pending updates)
        self._chunk_pending_save: List[int] = []
        # set of entries' id which do not have a chunk
        self._unallocated_chunk: List[str] = []
        # index of last chunk
        self._last_chunk_idx = -1
        # lock for chunking information
        self.chunking_lock = asyncio.Lock()

    def __len__(self) -> int:
        return self._chunk_size * self._last_chunk_idx + len(
            self._chunk2id.get(self._last_chunk_idx, [])
        )

    async def get_entries(self, begin: int, end: int) -> List[I]:
        # NOTE: assume mostly packed chunk
        entries: List[I] = []
        chunk_begin = begin // self._chunk_size
        chunk_last = end // self._chunk_size
        chunk_end = chunk_last + 1

        for chunk_idx in range(chunk_begin, chunk_end):
            if chunk_idx == chunk_begin:
                entry_begin = begin % self._chunk_size
            else:
                entry_begin = 0
            if chunk_idx == chunk_last:
                entry_end = end % self._chunk_size
            else:
                entry_end = self._chunk_size

            chunkIds = self._chunk2id[chunk_idx]
            entry_end = min(len(chunkIds), entry_end)
            for entry_idx in range(entry_begin, entry_end):
                entry_id = chunkIds[entry_idx]
                entry = self._store[entry_id]
                entries.append(entry)

        return entries

    async def load_chunks(
        self,
        begin: int = 0,
        end: int = -1,
    ):
        async with self.chunking_lock:
            # get chunk ids from disk
            chunk_idx_s: List[int] = sorted(
                chunk_idx
                for chunk_idx in (
                    Store.get_chunk_idx_from_filename(filename)
                    for filename in await aiofiles.os.listdir(self._chunk_dir)
                )
                if chunk_idx is not None
            )

            if end == -1:
                # compute last and end chunk index
                if len(chunk_idx_s) > 0:
                    end = chunk_idx_s[-1] + 1
                    self._last_chunk_idx = chunk_idx_s[-1]
            else:
                self._last_chunk_idx = end - 1

            # iterate over chunks
            for chunk_idx in range(begin, end):
                if chunk_idx not in chunk_idx_s:
                    print(
                        f"WARNING: chunk {chunk_idx} cannot be loaded, chunk is missing"
                    )
                    continue

                # read chunk file
                async with aiofiles.open(
                    self._chunk_dir / Store.get_chunk_filename(chunk_idx), mode="r"
                ) as file:
                    lines = await file.readlines()

                chunk2id: List[str] = []
                for line in lines:
                    entry = self._entry_cls.model_validate_json(line)
                    entry_id = entry.get_id()

                    # store entry
                    self._store[entry_id] = entry

                    # collect chunk-entry metadata
                    self._id2chunk[entry_id] = chunk_idx
                    chunk2id.append(entry_id)

                self._chunk2id[chunk_idx] = chunk2id

                # if chunk have remaining capacity
                if len(chunk2id) < self._chunk_size:
                    # keep track of chunk with remaining capacity for future insert
                    self._chunk_with_capacity.append(chunk_idx)

    async def unload_chunk(
        self,
        chunk_idx: int,
        save: bool = True,
    ):
        async with self.chunking_lock:
            if save and chunk_idx in self._chunk_pending_save:
                await self.unsafe_save_chunk(chunk_idx)

            for entry_id in self._chunk2id[chunk_idx]:
                del self._store[entry_id]
            del self._chunk2id[chunk_idx]

            if chunk_idx in self._chunk_with_capacity:
                self._chunk_with_capacity.remove(chunk_idx)

    async def set(self, entry: I, replace_if_exist: bool = False):
        """concurrent-safe setting entry"""
        async with self.chunking_lock:
            self.unsafe_set(entry, replace_if_exist)

    def get(self, entry_id: str) -> Optional[I]:
        entry = self._store.get(entry_id)
        if entry is None:
            return None
        return entry.model_copy(deep=True)

    def __contains__(self, key: str):
        return key in self._store

    def unsafe_set(self, entry: I, replace_if_exist: bool = False):
        """Perform unsafe key-value set to Store. Since set touches the chunking information

        Direct calls to this method without `async with self.chunking_lock` is NOT concurrent-safe. Async caller should call `set` instead.

        Args:
            entry (I): entry to be set (add/update) into the
            replace_if_exist (bool, optional): make setting operation an update if already exists. Defaults to False.

        Raises:
            ValueError: entry with the same id already exists
        """
        entry_id = entry.get_id()
        if not replace_if_exist and entry_id in self._store:
            raise ValueError(f"instance with id: {entry_id} already exist")

        self._store[entry_id] = entry
        chunk_idx = self._id2chunk.get(entry_id, -1)

        if chunk_idx == -1:
            # find existing chunk with remaining capacity
            if len(self._chunk_with_capacity) > 0:
                # assign chunk with capacity
                chunk_idx = self._chunk_with_capacity[0]
                chunk2id = self._chunk2id[chunk_idx]
                chunk2id.append(entry_id)
                if len(chunk2id) >= self._chunk_size:
                    self._chunk_with_capacity.remove(chunk_idx)

        if chunk_idx == -1:
            # mark entry as unallocated
            if entry_id not in self._unallocated_chunk:
                self._unallocated_chunk.append(entry_id)
        else:
            if chunk_idx not in self._chunk_pending_save:
                self._chunk_pending_save.append(chunk_idx)

    @staticmethod
    def get_chunk_filename(chunk_idx: int):
        return f"chunk_{chunk_idx:04d}.jsonl"

    @staticmethod
    def get_chunk_idx_from_filename(chunk_filename: str) -> Optional[int]:
        """
        Extracts an integer from a string in the format 'chunk_<number>.json'.

        Args:
            input_string (str): The input string to extract the number from.

        Returns:
            int or None: The extracted integer if a match is found, or None if no match is found.
        """
        match = re.search(CHUNK_FILENAME_PATTERN, chunk_filename)
        if match:
            return int(match.group(1))
        else:
            return None  # Return None if no match is found

    async def save(self):
        async with self.chunking_lock:
            # update existing chunks with pending changes
            chunks_saving = self._chunk_pending_save
            self._chunk_pending_save = []
            for chunk_idx in chunks_saving:
                await self.unsafe_save_chunk(chunk_idx)

            # create new chunks for unallocated data
            while len(self._unallocated_chunk) > 0:
                id_to_save = self._unallocated_chunk[: self._chunk_size]
                self._unallocated_chunk = self._unallocated_chunk[self._chunk_size :]
                # allocate a new chunk on disk
                while True:
                    self._last_chunk_idx = chunk_idx = self._last_chunk_idx + 1
                    chunk_path = self._chunk_dir / self.get_chunk_filename(chunk_idx)
                    if not await aiofiles.os.path.exists(chunk_path):
                        try:
                            await create_file_atomically(chunk_path, "allocation")
                        except FileExistsError:
                            continue
                        break
                self._chunk2id[chunk_idx] = id_to_save
                await self.unsafe_save_chunk(chunk_idx)

    async def unsafe_save_chunk(self, chunk_idx: int):
        lines: List[str] = []
        for entry_id in self._chunk2id[chunk_idx]:
            entry = self._store[entry_id]
            lines.append(
                json.dumps(
                    entry.model_dump(mode="json"),
                    ensure_ascii=False,
                )
            )
        chunk_path = self._chunk_dir / self.get_chunk_filename(chunk_idx)
        await safe_write_file(chunk_path, "\n".join(lines))
