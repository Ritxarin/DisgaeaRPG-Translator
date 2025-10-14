import re

weapon_map = {
'剣': 'Sword',
'杖': 'Staff',
'拳': 'Fist',
'銃': 'Gun',
'斧': 'Axe',
'弓': 'Bow',
'槍': 'Spear',
'魔物魔法': 'Mon Magic',
'魔物物理': 'Mon.Phys'
}


damage_type_map = {
'必殺技で与えるダメージ': 'Skill Damage',
'与える全てのダメージ': 'Damage',
'属性攻撃で与えるダメージ': 'Elemental Damage'
}


element_map = {
'炎': 'Fire',
'水': 'Water',
'風': 'Wind',
'星': 'Star'
}

patterns = [

    # --- Pattern 1: Highest-HP enemy follow-ups ---
    (
    re.compile(
        r'(、さらに)?ターン(?P<timing>開始|終了)時、残りHPが高い敵キャラ(?:単体)?に'
        r'(?P<element>[炎水風星])属性攻撃\((?P<hits>\d+)回[,，]威力(?P<power>[A-E]\+?)\)',
        flags=re.UNICODE,
    ),
    lambda m: f"{', ' if m.group(1) else ''}"
              f"Highest-HP Foe: At the "
              f"{'start' if m.group('timing') == '開始' else 'end'} of turn, "
              f"{element_map[m.group('element')]} Follow-up "
              f"({m.group('hits')} {'Time' if m.group('hits') == '1' else 'Times'}, Power {m.group('power')})",
    ),

    # --- Pattern 2: Lowest-HP enemy follow-ups ---
    (
    re.compile(
        r'(、さらに)?ターン(?P<timing>開始|終了)時、残りHP(?:が|の)低い敵キャラ(?:単体)?に'
        r'(?P<element>[炎水風星])属性攻撃\((?P<hits>\d+)回[,，]威力(?P<power>[A-E]\+?)\)',
        flags=re.UNICODE,
    ),
    lambda m: f"{', ' if m.group(1) else ''}"
              f"Lowest-HP Foe: At the "
              f"{'start' if m.group('timing') == '開始' else 'end'} of turn, "
              f"{element_map[m.group('element')]} Follow-up "
              f"({m.group('hits')} {'Time' if m.group('hits') == '1' else 'Times'}, Power {m.group('power')})",
    )



    # # 1️⃣ Party uses [Element] skill -> Party Damage Up
    # (
    #     re.compile(
    #         r"パーティが(?P<element>[炎水風星])属性の技を使用した時、パーティに与える全てのダメージ\+#PER#%(?:\((?P<turns>\d+)T\))?付与"
    #     ),
    #     lambda m: f"All Allies: When a {element_map[m.group('element')]} Skill is used, "
    #               f"Damage +#PER#%({m.group('turns')}T)" if m.group('turns')
    #               else f"All Allies: When a {element_map[m.group('element')]} Skill is used, Damage +#PER#%"
    # ),

    # # 2️⃣ Party uses [Element] skill -> Buff stats or SP etc.
    # (
    #     re.compile(
    #         r"パーティが(?P<element>[炎水風星])属性の技を使用した時、パーティの(?P<buffs>[A-Z・]+|HP以外の基礎パラメータ|SP)\+#PER#%(?:\((?P<turns>\d+)T\))?"
    #     ),
    #     lambda m: (
    #         f"All Allies: When a {element_map[m.group('element')]} Skill is used, "
    #         f"{('Non-HP Basic Stats' if m.group('buffs') == 'HP以外の基礎パラメータ' else m.group('buffs').replace('・', '/'))} "
    #         f"+#PER#%({m.group('turns')}T)"
    #         if m.group('turns')
    #         else
    #         f"All Allies: When a {element_map[m.group('element')]} Skill is used, "
    #         f"{('Non-HP Basic Stats' if m.group('buffs') == 'HP以外の基礎パラメータ' else m.group('buffs').replace('・', '/'))} +#PER#%"
    #     )
    # ),

    # 1️⃣ Weapon-equipped self: element damage
    # (
    # re.compile(r'自分が(?P<weapon>[^武]+)武器装備時、(?:(?P<element>[炎水風星属性])属性)?攻撃で与える(?P<type>全てのダメージ|必殺技で与えるダメージ|ダメージ)\+#PER#%'),
    # lambda m: f"{weapon_map.get(m.group('weapon'), m.group('weapon'))}-Equipped Self: " +
    # f"{element_map.get(m.group('element'), 'Elemental') if m.group('element') else ''} " +
    # f"{ 'Damage' if m.group('type')=='全てのダメージ' else 'Skill Damage' if '必殺技' in m.group('type') else 'Damage'} +#PER#%"
    # ),

    # 2️⃣ Weapon-equipped self: damage
    # (
    #     re.compile(
    #         r'自分が(?P<weapon>剣|杖|魔物魔法|魔物物理|拳|銃|斧|弓|槍)武器装備時、'
    #         r'(?:(?P<element>[炎水風星])属性)?'
    #         r'(?:攻撃で)?'
    #         r'(?P<damage_type>与える全てのダメージ|必殺技で与えるダメージ|属性攻撃で与えるダメージ)'
    #         r'\+#PER#%'
    #     ),
    #     lambda m: f"{weapon_map[m.group('weapon')]}-Equipped Self: "
    #               f"{element_map.get(m.group('element'), damage_type_map[m.group('damage_type')])} +#PER#%"
    # ),

    # # Highest AG-Ally - HP heal
    # (
    # re.compile(r"ターン(?P<timing>開始|終了)時、行動ゲージが先頭の味方キャラのHPを、自身の最大HPの#PER#(?:%|％)回復"),
    # lambda m: f"Highest-AG Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, Heal #PER#% of max HP"
    # ),


    # # Highest AG-Ally -SP
    # (
    # re.compile(r"ターン(?P<timing>開始|終了)時、行動ゲージが先頭の味方キャラのSP\+#PER#"),
    # lambda m: f"Highest-AG Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, SP+#PER#"
    # ),


    # # Highest AG-Ally - Standard buffs (ATK, INT, DEF, CRD, etc.) with optional turns and %
    # (
    #     re.compile(
    #     r"ターン(?P<timing>開始|終了)時、行動ゲージが先頭の味方キャラの"
    #     r"(?P<buffs>[A-Z0-9・]+)"
    #     r"(?:\+#PER#(?:%|％))?"
    #     r"(?:\((?P<turns>\d+)(?:T|ターン)\))?"
    #     ),
    #     lambda m: f"Highest-AG Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, "
    #     f"{m.group('buffs').replace('・','/')}{' +#PER#%(' + m.group('turns') + 'T)' if m.group('turns') else ' +#PER#%'}"
    # ),

    # # High Stat + buffs
    # (re.compile(r"ターン(?P<timing>開始|終了)時、最も(?P<target>[A-Z]+)が高い味方キャラの(?P<buffs>[A-Z・]+)\+#PER#%\((?P<turns>\d+)T\)"),
    # lambda m: f"Highest-{m.group('target')} Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, {m.group('buffs').replace('・', '/')} +#PER#%({m.group('turns')}T)"),

    # # High Stat + Skill Damage
    # (
    # re.compile(
    # r"ターン(?P<timing>開始|終了)時、最も(?P<target>[A-Z]+)の高い味方キャラに必殺技で与えるダメージ\+#PER#%\((?P<turns>\d+)T\)付与"
    # ),
    # lambda m: f"Highest-{m.group('target')} Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, Skill Damage +#PER#%({m.group('turns')}T)"
    # ),

    # # High Stat + Damage
    # (
    # re.compile(
    # r"ターン(?P<timing>開始|終了)時、パーティの最も(?P<target>[A-Z]+)が高いキャラに与える全てのダメージ\+#PER#%\((?P<turns>\d+)T\)付与"
    # ),
    # lambda m: f"Highest-{m.group('target')} Ally: At the {'start' if m.group('timing')=='開始' else 'end'} of turn, Damage +#PER#%({m.group('turns')}T)"
    # ),

]