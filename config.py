import json
from dataclasses import dataclass, asdict
from typing import Optional
from utils import config_path, ensure_dirs


@dataclass
class Config:
    last_root: Optional[str] = None
    window: Optional[dict] = None

    def save(self):
        try:
            ensure_dirs()  
            with open(config_path(), "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"設定保存エラー: {e}")

    @staticmethod
    def load():
        try:
            p = config_path()
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return Config(**data)
            except FileNotFoundError:
                return Config()
        except Exception as e:
            print(f"設定読込エラー: {e}")
            return Config()
