## Backup 7z

一个用于创建7z格式永久备份的插件

---

### 配置

```json5
{
    "permission": 3,  // 运行命令权限的最低等级
    "prefix": "!!backup",  // 命令前缀
    "backup_path": "./backup",  // 输出备份文件的目录
    "archive_format": "{time}",  // 备份文件名格式
    "world_names": [  // 备份存档目录名称
        "world"
    ],
    "ignore_file_patterns": [
        "session.lock"  // 需要忽略文件的表达式
    ],
    "server": {
        "turn_off_auto_save": true,  // 备份时是否需要关闭自动保存以确保备份期间存档不会变化, 推荐开启
        "save_all_worlds": "save-all flush",  // 保存世界的命令
        "auto_save_off": "save-off",  // 关闭自动保存命令
        "auto_save_on": "save-on",  // 启动自动保存命令
        "timeout": 600,  // 等待保存完成最长时间, 超过此时间会取消备份任务
        "saved_world_regex": [  // 保存完成输出文本表达式
            "Saved the game",
            "Saved the world",
            "System chat: Saved the game"
        ]
    },
    "archive": {
        "mode": "zip",  // 备份模式. 可选zip, 7z-commandline, zip-commandline
        "core_7z": "" // 7z-commandline模式下7-zip核心路径
    }
}
```

---

### 备份模式

此插件可以选择不同的备份模式, 以达成不同备份效果

### `zip`

最经典的压缩算法, 压缩速度快, 兼容性强, 但文件体积往往比7z大

此模式使用python标准库进行压缩, 开箱即用, 不需要额外配置

### `7z-commandline` `zip-commandline`

希望获得更高的压缩性能? 此模式下可以通过命令行调用`7-zip`进行压缩, 以达到最佳压缩性能

`7z-commandline`将文件打包为7z格式, `zip-commandline`将文件打包为zip格式

你需要指定`core_7z`为7-zip可执行文件, 通常为`7z.exe`的文件路径

你可以在这里下载到官方7-zip [https://7-zip.org](https://7-zip.org)
