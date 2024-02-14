import typer

from . import store, user

app = typer.Typer()
app.add_typer(user.app, name="user")
app.add_typer(store.app, name="store")

if __name__ == "__main__":
    app()
