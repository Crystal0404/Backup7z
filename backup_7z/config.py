from pathlib import Path
from typing import Literal, Self

from mcdreforged import PermissionLevel
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Config(BaseModel):
    model_config = ConfigDict(strict=True)

    class __Commands(BaseModel):
        turn_off_auto_save: bool = True
        save_all_worlds: str = "save-all flush"
        auto_save_off: str = "save-off"
        auto_save_on: str = "save-on"
        timeout: int = Field(default=600, ge=60)
        saved_world_regex: list[str] = Field(
            default_factory=lambda: ["Saved the game", "Saved the world", "System chat: Saved the game"]
        )

    class __Archive(BaseModel):
        mode: Literal["7z", "7z-commandline", "zip"] = "7z"
        core_7z: str = ""

        @model_validator(mode="after")
        def check_core(self) -> Self:
            if self.mode == "7z-commandline" and not Path(self.core_7z).is_file():
                raise ValueError("Can not found core_7z path")
            return self

    permission: int = PermissionLevel.ADMIN
    prefix: str = "!!backup"
    backup_path: str = "./backup"
    archive_format: str = "{time}"
    world_names: list[str] = Field(default_factory=lambda: ["world"])
    ignore_file_patterns: list[str] = Field(default_factory=lambda: ["session.lock"])
    server: __Commands = Field(default_factory=__Commands)
    archive: __Archive = Field(default_factory=__Archive)
