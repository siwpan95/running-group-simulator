#!/usr/bin/env python3
"""Headless self-check for running-group-simulator / Mirrors of the Lost.

The terminal engine is driven by ``mirror_launcher.py`` / ``mirror_mvp.py``;
this check stays below that layer (Model + services only, no renderer, no
input loop):

* character model: derived values (Dodge / shock threshold), skill lookup and
  ``to_dict`` -> ``from_dict`` round-trip,
* XP system: reward formula, XP spend pricing and the level-up bookkeeping,
* save manager: character snapshot + progress JSON round-trip in a temporary
  directory (the project ``saves/`` folder is not touched).

Run from the project root:

    python selfcheck.py

Prints ``selfcheck ok: ...`` and returns 0 on success, ``FAIL: ...`` and 1
on failure.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from core.character import Character, Skill
from services.save_manager import SaveManager
from services.xp_system import XPSystem

CHECKS: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if not condition:
        raise AssertionError(f"{name}: {detail or 'condition is false'}")
    CHECKS.append(name)


def check_character_model() -> Character:
    c = Character()
    c.character_id = "selfcheck"
    c.name = "Self Check"
    c.skills.append(Skill(name="Stealth", level=12, difficulty="Avg",
                          base_attribute="DX", points_spent=4))

    check("char.id", c.character_id == "selfcheck" and c.name == "Self Check")
    check("char.dodge", c.dodge == 6, c.dodge)                      # (DX 10 + 2) // 2
    check("char.shock", c.shock_threshold == 3, c.shock_threshold)  # 10 // 3
    c.hp_max = 22
    check("char.shock_scales", c.shock_threshold == 7, c.shock_threshold)
    check("char.skill_lookup",
          c.get_skill_level("Stealth") == 12 and c.get_skill_level("IQ") == 10,
          (c.get_skill_level("Stealth"), c.get_skill_level("IQ")))
    check("char.skill_missing", c.get_skill_level("Nope") is None)

    data = c.to_dict()
    clone = Character.from_dict(data)
    check("char.roundtrip",
          clone.character_id == "selfcheck" and clone.name == "Self Check"
          and clone.st == c.st and clone.hp_max == 22
          and clone.total_xp == c.total_xp and clone.dodge == c.dodge,
          {"name": clone.name, "st": clone.st, "hp_max": clone.hp_max})
    check("char.roundtrip_skill",
          clone.get_skill_level("Stealth") == 12, clone.get_skill_level("Stealth"))
    return c


def check_xp_system() -> None:
    xp = XPSystem()

    # scenes + base 3 + flags//3 + psychic mark
    check("xp.formula", xp.calculate_xp(5, 4, 1) == 10, xp.calculate_xp(5, 4, 1))
    check("xp.formula_zero", xp.calculate_xp(0, 0, 0) == 3)

    c = Character()
    c.character_id = "selfcheck"
    c.name = "XP"
    xp.apply_xp(c, 10)
    check("xp.apply", c.total_xp == 10 and len(c.xp_log) == 1,
          (c.total_xp, c.xp_log))

    # ST/HT cost 10, DX/IQ cost 20
    check("xp.spend", xp.spend_xp(c, "attribute", "ST", 1) is True)
    check("xp.spend_state", c.total_xp == 0 and c.st == 11, (c.total_xp, c.st))
    check("xp.spend_reject", xp.spend_xp(c, "attribute", "DX", 1) is False)

    c.total_xp = 10
    options = xp.get_upgrade_options(c)
    targets = {o["target"] for o in options}
    check("xp.options", targets == {"ST", "HT"} and all(o["cost"] == 10 for o in options),
          options)
    check("xp.skill_unimplemented", xp.spend_xp(c, "skill", "Stealth", 1) is False)


def check_save_manager() -> None:
    with tempfile.TemporaryDirectory(prefix="paotuan-selfcheck-") as tmp:
        c = Character()
        c.character_id = "selfcheck"
        c.name = "Save Check"
        c.hp = 7
        c.hp_max = 22
        c.permanent_tags.append("selfcheck-tag")
        progress = {"module": "mirror_house_alley", "scene": 2,
                    "flags": ["a", "b"], "history": [{"node": "start"}]}

        sm = SaveManager(saves_dir=tmp)
        path = sm.save("selfcheck", c, progress)
        check("save.file", Path(path).exists() and Path(path).parent == Path(tmp),
              path)
        check("save.snapshot",
              Path(path).name.startswith("selfcheck_") and Path(path).suffix == ".json",
              Path(path).name)

        data = sm.load(path)
        check("save.load", isinstance(data, dict), type(data))
        check("save.header",
              data.get("character_name") == "Save Check"
              and data.get("save_name") == "selfcheck", data.get("save_name"))
        state = data.get("character_state", {})
        check("save.state", state.get("hp") == 7 and state.get("hp_max") == 22
              and state.get("permanent_tags") == ["selfcheck-tag"], state)
        check("save.progress", data.get("game_progress") == progress,
              data.get("game_progress"))

        check("save.list", len(sm.list_saves()) == 1, sm.list_saves())
        newest = sm.load_newest("selfcheck")
        check("save.newest", isinstance(newest, dict)
              and newest.get("character_name") == "Save Check")
        check("save.delete", sm.delete_save(path) is True and sm.list_saves() == [])


def run() -> None:
    check_character_model()
    check_xp_system()
    check_save_manager()


def main() -> int:
    try:
        run()
    except Exception as exc:  # noqa: BLE001 - self-check must report, not traceback
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1
    print(f"selfcheck ok: paotuan model/services "
          f"({len(CHECKS)} checks: character/xp/save)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
