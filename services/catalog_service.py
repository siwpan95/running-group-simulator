# -*- coding: utf-8 -*-
"""
迷失之镜 — 内容目录服务（v3.6 内容目录工程化）

统一加载/检索各系统的策展目录（data/<system>/catalog.json）：
  CatalogService.load("coc7") → {"creatures": [...]}
  CatalogService.find_creature("深潜者") / find_spell / find_item
目录本身由 tools/make_*_catalog.py 从资源库策展生成，
tools/validate_catalogs.py 校验 schema（测试套件钉住两者）。
"""
import json
import os
from typing import Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")

# 支持的系统 → 目录文件相对路径
CATALOG_PATHS = {
    "coc7": os.path.join("coc7", "catalog.json"),
    "dnd5e": os.path.join("dnd5e", "catalog.json"),
    "wod": os.path.join("wod", "catalog.json"),
    "gurps": os.path.join("gurps", "catalog.json"),
}


class CatalogService:
    """内容目录统一入口（纯数据服务，无状态）。"""

    def __init__(self, data_root: str = DATA):
        self.data_root = data_root
        self._cache: Dict[str, Dict] = {}

    def available(self) -> List[str]:
        return [k for k in CATALOG_PATHS if os.path.exists(self._path(k))]

    def _path(self, system: str) -> str:
        rel = CATALOG_PATHS.get(system)
        if not rel:
            raise KeyError("未知系统目录: %s（支持 %s）"
                           % (system, sorted(CATALOG_PATHS)))
        return os.path.join(self.data_root, rel)

    def load(self, system: str) -> Dict:
        if system not in self._cache:
            with open(self._path(system), encoding="utf-8") as f:
                self._cache[system] = json.load(f)
        return self._cache[system]

    def list_creatures(self, system: str) -> List[Dict]:
        c = self.load(system)
        return c.get("creatures") or c.get("monsters") or []

    def find_creature(self, name: str, system: Optional[str] = None) -> Optional[Dict]:
        """按中文名/英文名模糊查找生物（不指定系统时全局找）。"""
        systems = [system] if system else self.available()
        for s in systems:
            for e in self.list_creatures(s):
                if name in (e.get("name"), e.get("name_en")):
                    return dict(e, _system=s)
        return None

    def find_spell(self, name: str, system: Optional[str] = None) -> Optional[Dict]:
        systems = [system] if system else self.available()
        for s in systems:
            for e in self.load(s).get("spells") or []:
                if e.get("name", "").lower() == name.lower():
                    return dict(e, _system=s)
        return None

    def find_item(self, name: str, system: Optional[str] = None) -> Optional[Dict]:
        systems = [system] if system else self.available()
        for s in systems:
            for e in self.load(s).get("items") or []:
                if e.get("name", "").lower() == name.lower():
                    return dict(e, _system=s)
        return None
