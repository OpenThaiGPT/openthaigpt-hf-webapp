import os
from typing import Annotated

import typer
from anyio import Path
from genericpath import isdir
from pydantic import SecretStr

from otgpt_hft.api.data_bridge import METADATA_FILENAME, StoreMetadata, StoreMetadataBM
from otgpt_hft.data_model.dialogue.error import DataIntegrityError
from otgpt_hft.data_model.dialogue.graph import DialogueGraph
from otgpt_hft.data_model.serial.entry import SerializedEntry
from otgpt_hft.data_model.serial.store import Store
from otgpt_hft.database import Database
from otgpt_hft.global_res import DATA_STORE_PATH
from otgpt_hft.utils.cli import async_to_sync

app = typer.Typer()


# @app.command()
# @async_to_sync
# async def validate():
#     async with Database() as database:
#         users = await database.list_users()
#         print(users)


@app.command(name="list")
def list_stores():
    for dataset_name in os.listdir(DATA_STORE_PATH):
        dataset_dir = DATA_STORE_PATH / dataset_name

        # read dataset metadata
        with open(dataset_dir / METADATA_FILENAME) as file:
            print("Dataset:", dataset_dir.relative_to(DATA_STORE_PATH))
            # print(f"dir: {dataset_dir.absolute()}")
            print(f"metadata: {StoreMetadataBM.model_validate_json(file.read())}")

        # list all splits in the dataset
        for split_name in os.listdir(dataset_dir):
            split_dir = dataset_dir / split_name

            if not os.path.isdir(split_dir):
                continue

            with open(split_dir / METADATA_FILENAME) as file:
                print("  Split:", split_dir.relative_to(DATA_STORE_PATH))
                # print(f"  dir: {split_dir.absolute()}")
                print(f"  metadata: {StoreMetadataBM.model_validate_json(file.read())}")

        print()


@app.command(name="validate")
@async_to_sync
async def validate_stores():
    for dataset_name in os.listdir(DATA_STORE_PATH):
        dataset_dir = DATA_STORE_PATH / dataset_name

        # list all splits in the dataset
        for split_name in os.listdir(dataset_dir):
            split_dir = dataset_dir / split_name

            if not os.path.isdir(split_dir):
                continue

            # load split data
            store = Store(
                SerializedEntry,
                split_dir,
            )

            await store.load_chunks()

            entires = await store.get_entries(0, len(store))

            found_issue = False
            for entry in entires:
                try:
                    DialogueGraph(entry, inspect=True)
                    # if graph.find_issues(inspect=True):
                    #     found_issue = True
                except DataIntegrityError as e:
                    print("dataset_name", dataset_name)
                    print("split_name", split_name)
                    print("entry_id", entry.get_id())
                    print("DataIntegrityError", e.info)
                    print()
                    found_issue = True

            if found_issue:
                print(split_dir, "FOUND ISSUE")
            else:
                print(split_dir, "ok")


@app.command(name="inspect")
@async_to_sync
async def inspect_store(dataset_name: str, split_name: str, entry_id: str):
    dataset_dir = DATA_STORE_PATH / dataset_name
    split_dir = dataset_dir / split_name

    # load split data
    store = Store(
        SerializedEntry,
        split_dir,
    )

    await store.load_chunks()

    entry = store.get(entry_id)

    if entry is None:
        print("entry not found")
        return

    found_issue = False
    try:
        DialogueGraph(entry, inspect=True)
        # if graph.find_issues(inspect=True):
        #     found_issue = True
    except DataIntegrityError as e:
        print("dataset_name", dataset_name)
        print("split_name", split_name)
        print("entry_id", entry.get_id())
        print("DataIntegrityError", e.info)
        print()
        found_issue = True

    if found_issue:
        print(split_dir, "FOUND ISSUE")
    else:
        print(split_dir, "ok")
