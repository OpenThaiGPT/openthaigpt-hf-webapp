import pathlib

import aiofiles
import aiofiles.os


async def safe_write_file(path: pathlib.Path, content: str):
    # Create a temporary file path
    temp_path = path.with_suffix(".tmp")

    try:
        # Write the content to the temporary file asynchronously
        async with aiofiles.open(temp_path, mode="w") as temp_file:
            await temp_file.write(content)

        # Verify the file content by reading it
        async with aiofiles.open(temp_path, mode="r") as temp_file:
            new_content = await temp_file.read()

        if new_content != content:
            raise ValueError("File content verification failed.")

        # Replace the original file with the temporary file asynchronously
        await aiofiles.os.rename(temp_path, path)

    except Exception as e:
        print(f"Error writing file: {e}")
    finally:
        # Clean up the temporary file if it exists asynchronously
        if await aiofiles.os.path.exists(temp_path):
            await aiofiles.os.remove(temp_path)


async def create_file_atomically(path: pathlib.Path, content: str):
    async with aiofiles.open(path, "x") as file:
        await file.write(content)
