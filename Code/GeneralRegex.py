import re


patterns = [
    
    # --- Dedicated Mana Potion description (name) ---
    (
        re.compile(r"使用すると(.+?)のマナが獲得できる不思議なお薬"),
        lambda m, ctx: (
            f"A wondrous potion that grants "
            f"{ctx.characters.get(m.group(1), m.group(1))} mana when used"
        )
    ),

    # --- Nether Star (name) ---
    (
        re.compile(r"(.+?)の魔星$"),
        lambda m, ctx: (
            f"{ctx.characters.get(m.group(1), m.group(1))} Nether Star"
        )
    ),

    # --- Nether Star (description) ---
    (
        re.compile(r"(.+?)を★(\d+)の覚醒状態にできる魔星"),
        lambda m, ctx: (
            f"Nether Star for Awakening {m.group(2)}★ "
            f"{ctx.characters.get(m.group(1), m.group(1))}."
        )
    ),

    # --- Crystal (name) ---
    (
        re.compile(r"(.+?)の結晶$"),
        lambda m, ctx: (
            f"{ctx.characters.get(m.group(1), m.group(1))} Crystal"
        )
    ),

    # --- Crystal (description) ---
    (
        re.compile(r"(.+?)を魔改造できる結晶"),
        lambda m, ctx: (
            f"A crystal used for "
            f"{ctx.characters.get(m.group(1), m.group(1))}'s Nether Enhancement."
        )
    ),

    # --- Raise character to level ---
    (
        re.compile(r"(.+?)をLv(\d+)にしよう"),
        lambda m, ctx: (
            f"Level up {ctx.characters.get(m.group(1), m.group(1))} "
            f"to Lv {m.group(2)}"
        )
    ),

    # --- Recruit character ---
    (
        re.compile(r"(.+?)を仲間にしよう"),
        lambda m, ctx: (
            f"Recruit {ctx.characters.get(m.group(1), m.group(1))}"
        )
    ),

    # --- Nether Enhance character N times ---
    (
        re.compile(r"(.+?)を(\d+)回魔改造させよう"),
        lambda m, ctx: (
            f"Nether Enhance "
            f"{ctx.characters.get(m.group(1), m.group(1))} "
            f"{m.group(2)} times"
        )
    ),

    # --- Nether Enhance character ---
    (
        re.compile(r"(.+?)を魔改造させよう"),
        lambda m, ctx: (
            f"Nether Enhance "
            f"{ctx.characters.get(m.group(1), m.group(1))}"
        )
    ),

    # --- Clear stages N times with character in party (no support) ---
    (
        re.compile(
            r"(.+?)を編成して(\d+)回ステージをクリアしよう"
            r"\(同行者不可\)"
        ),
        lambda m, ctx: (
            f"Clear {int(m.group(2)):,} stages with "
            f"{ctx.characters.get(m.group(1), m.group(1))} in your party "
            f"(not companion)"
        )
    ),

    # --- Character Reminiscence area --- #
    (
        re.compile(r"(.+?)追想エリア"),
        lambda m, ctx: (
            f"{ctx.characters.get(m.group(1), m.group(1))} Reminiscence Area"
        )
    ),

    # --- Trial --- #
    (
        re.compile(r"試闘の間\s*(.+)"),
        lambda m, ctx: (
            f"Trial Room {ctx.characters.get(m.group(1), m.group(1))}"
        )
    ),

]