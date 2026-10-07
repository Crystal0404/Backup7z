import re
import shutil
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock, Thread, Event

from mcdreforged import PluginServerInterface, Requirements, CommandSource, CommandContext, Literal, QuotableText, \
    Info, RText, RColor, RClickSuggestCommand, RClickRunCommand

from backup_7z.config import Config
from backup_7z.utils import *

CONFIG: Config
EVENT: Event = Event()
LOCK: Lock = Lock()
LOAD: bool = False


def on_load(server: PluginServerInterface, _):
    global CONFIG, LOAD
    CONFIG = server.load_config_simple(target_class=Config)
    LOAD = True
    register_command(server)


def on_unload(_: PluginServerInterface):
    global LOAD
    LOAD = False
    EVENT.set()


def on_info(_: PluginServerInterface, info: Info):
    if not LOAD or info.is_user or EVENT.is_set():
        return

    if any(re.fullmatch(i, info.content) for i in CONFIG.server.saved_world_regex):
        EVENT.set()


def register_command(server: PluginServerInterface):
    prefix = CONFIG.prefix
    text_make = (
        RText(f"{prefix} make [<comment>]", color=RColor.gray).
        set_click_event(RClickSuggestCommand(f"{prefix} make")).
        set_hover_text(rtr("backup_7z.hover.make"))
    )
    text_list = (
        RText(f"{prefix} list", color=RColor.gray).
        set_click_event(RClickRunCommand(f"{prefix} list")).
        set_hover_text(rtr("backup_7z.hover.list"))
    )
    text_listall = (
        RText(f"{prefix} listall", color=RColor.gray).
        set_click_event(RClickRunCommand(f"{prefix} listall")).
        set_hover_text(rtr("backup_7z.hover.listall"))
    )
    command = (
        Literal(prefix).
        requires(
            Requirements.has_permission(CONFIG.permission),
            lambda: server.rtr("mcdreforged.mcdr_command.permission_denied")
        ).
        runs(
            lambda s: s.reply(
                rtr(
                    "backup_7z.root",
                    prefix=prefix,
                    prefix_make=text_make,
                    prefix_list=text_list,
                    prefix_listall=text_listall
                )
            )
        ).
        then(
            Literal("make").
            runs(make).
            then(QuotableText("comment").runs(make))
        ).
        then(Literal("list").runs(lambda s: show(s))).
        then(Literal("listall").runs(lambda s: show(s, False)))
    )
    server.register_command(command)
    server.register_help_message(prefix, rtr("backup_7z.help"))


def wrap_lock(func):
    @wraps(func)
    def wrap(*args, **kwargs):
        if not LOCK.locked():
            raise RuntimeError("Lock must acquire!")
        try:
            result = func(*args, **kwargs)
        finally:
            LOCK.release()
        return result

    return wrap


def make(_: CommandSource, context: CommandContext):
    if LOCK.acquire(blocking=False):
        comment = context.get("comment", None)
        Thread(target=make_in_thread, args=(comment,), name="backup_7z").start()
    else:
        si().broadcast(rtr("backup_7z.running"))


@wrap_lock
def make_in_thread(comment: str | None):
    start = time.time()
    si().broadcast(rtr("backup_7z.start"))
    EVENT.clear()
    backup_path = Path(CONFIG.backup_path)
    backup_path.mkdir(exist_ok=True, parents=True)
    with TemporaryDirectory(dir=backup_path) as temp:
        target_path = Path(temp)
        try:
            if CONFIG.server.turn_off_auto_save:
                save_off()
            save_all()
            EVENT.wait(timeout=CONFIG.server.timeout)
            if not (EVENT.is_set() and LOAD):
                si().broadcast(rtr("backup_7z.exit"))
                return
            copy_world(target_path)
        finally:
            save_on()
        si().broadcast(rtr("backup_7z.archive"))
        archive_mode = CONFIG.archive.mode
        archive_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_name = (
                CONFIG.archive_format.format(time=archive_time)
                + ("" if comment is None else f"_{comment}")
                + SUFFIX[archive_mode]
        )
        try:
            archive_world(target_path, backup_path, archive_mode, archive_name)
        except Exception:
            si().broadcast(rtr("backup_7z.archiva_failed"))
            raise
    end = time.time()
    si().broadcast(rtr("backup_7z.done", name=archive_name))
    archive_path = backup_path.joinpath(archive_name)
    if archive_path.exists() and archive_path.is_file():
        size = archive_path.stat().st_size
        si().broadcast(rtr("backup_7z.time_size", size=f"{size / (1024 ** 3):.2f}", s=f"{end - start:.2f}"))


def copy_world(target_path: Path):
    for world_name in CONFIG.world_names:
        from_path = Path(get_server_path()).joinpath(world_name)
        to_path = target_path.joinpath(world_name)
        if from_path.exists():
            shutil.copytree(from_path, to_path, ignore=shutil.ignore_patterns(*CONFIG.ignore_file_patterns))


def archive_world(target_path: Path, backup_path: Path, archive_mode: str, archive_name: str):
    archive_path = backup_path.joinpath(archive_name)
    if archive_path.resolve().parent != backup_path.resolve():
        raise ValueError
    match archive_mode:
        case "7z-commandline" | "zip-commandline":
            archive_commandline(target_path, archive_path)
        case "zip":
            archive_zip(target_path, archive_path)
