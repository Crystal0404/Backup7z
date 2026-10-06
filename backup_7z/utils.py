import re
import subprocess
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from mcdreforged import PluginServerInterface, RTextBase, CommandSource
from py7zr import SevenZipFile

from backup_7z.config import Config

__all__ = [
    "SUFFIX",
    "get_server_path",
    "archive_commandline_7z",
    "archive_7z",
    "archive_zip",
    "save_on",
    "save_off",
    "save_all",
    "si",
    "rtr",
    "show"
]
SUFFIX = {
    "7z": ".7z",
    "7z-commandline": ".7z",
    "zip": ".zip"
}
DATE_PATTERN = re.compile(r".*?(?P<date>\d{4,}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}).*")


def get_server_path() -> Path:
    mcdr_config = si().get_mcdr_config()
    return Path(mcdr_config["working_directory"])


def archive_commandline_7z(target: Path, to: Path):
    args = [
        config().archive.core_7z,
        "a",
        to,
        rf"{target}\*"
    ]
    result = subprocess.run(args, stdout=subprocess.DEVNULL)
    if result.returncode != 0:
        raise RuntimeError(f"failed archive, return code: {result.returncode}")


def archive_7z(target: Path, to: Path):
    with SevenZipFile(to, "w") as szf:
        paths = [i for i in target.rglob("*")]
        for path in paths:
            szf.write(path, arcname=str(path.relative_to(target)))


def archive_zip(target: Path, to: Path):
    with ZipFile(to, "w", ZIP_DEFLATED) as zipf:
        paths = [i for i in target.rglob("*")]
        for path in paths:
            zipf.write(path, arcname=path.relative_to(target))


def save_off():
    si().execute(config().server.auto_save_off)


def save_on():
    si().execute(config().server.auto_save_on)


def save_all():
    si().execute(config().server.save_all_worlds)


def si():
    return PluginServerInterface.get_instance()


def rtr(key: str, *args, **kwargs):
    return si().rtr(key, *args, **kwargs)


def get_list() -> list[str]:
    backup_path = Path(config().backup_path)
    if not backup_path.is_dir():
        return list()

    names = [i.name for i in backup_path.iterdir() if i.is_file() and re.match(DATE_PATTERN, i.name)]
    sort_names = sorted(names, key=parser_time, reverse=True)
    return sort_names


def parser_time(s: str):
    match = re.search(DATE_PATTERN, s)
    time_name = match.groupdict()["date"]
    return datetime.strptime(time_name, "%Y-%m-%d_%H-%M-%S")


def config() -> Config:
    from backup_7z import CONFIG
    return CONFIG


def show(source: CommandSource, max_count: bool = True, count: int = 10):
    backup_list = get_list()
    source.reply(si().rtr("backup_7z.show", count=len(backup_list)))
    backup_path = Path(config().backup_path)
    num = 0
    for backup in backup_list:
        num += 1
        path = backup_path.joinpath(backup)
        size = path.stat().st_size
        text = RTextBase.format(rf"§7{num}. §r§e{backup}§r {size / (1024 ** 3):.2f} GB")
        source.reply(text)
        if max_count and num >= count:
            break
