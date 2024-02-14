from typing import Annotated

import typer
from pydantic import SecretStr

from otgpt_hft.database import Database
from otgpt_hft.utils.cli import async_to_sync

app = typer.Typer()


@app.command(name="list")
@async_to_sync
async def list_user():
    async with Database() as database:
        users = await database.list_users()
        print(users)


@app.command(name="register")
@async_to_sync
async def register_user(
    name: str,
    password: Annotated[
        str,
        typer.Option(
            default=None, prompt=True, confirmation_prompt=True, hide_input=True
        ),
    ],
):
    s_password = SecretStr(password)
    async with Database() as database:
        await database.register_user(name, s_password)


@app.command(name="reset-password")
@async_to_sync
async def reset_password(
    name: str,
    password: Annotated[
        str,
        typer.Option(
            default=None, prompt=True, confirmation_prompt=True, hide_input=True
        ),
    ],
):
    s_password = SecretStr(password)
    async with Database() as database:
        await database.reset_password(name, s_password)


@app.command(name="delete")
@async_to_sync
async def delete_user(name: str):
    typer.confirm(f'Are you sure you want to delete user "{name}"?', abort=True)

    async with Database() as database:
        deleted = await database.delete_user(name)

    if deleted:
        print(f'Deleted user: "{name}"')
    else:
        print(f'No user to be deleted with name: "{name}"')


if __name__ == "__main__":
    app()
