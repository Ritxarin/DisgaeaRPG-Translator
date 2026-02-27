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
'魔物物理': 'Mon Phys'
}
weapon_keys = sorted(weapon_map.keys(), key=len, reverse=True)
weapon_pattern = '|'.join(map(re.escape, weapon_keys))

stat_map = {
    'SP': 'SP',
    'ゲージ': 'AG',  # Action Gauge
    'HP以外の基礎パラメータ': 'Non-HP Basic Stats',
    '基礎パラメータ': 'Basic Stats',
    'HP': 'HP',
    'ATK': 'ATK',
    'INT': 'INT',
    'DEF': 'DEF',
    'RES': 'RES',
    'SPD': 'SPD',
    'CRD': 'CRD',
    'CRT': 'CRT',
    # Add more if needed
}

# Build stat group from the stat_map keys
# Escape any that contain non-ASCII characters or regex symbols
stats_pattern = (
    r'(?:HP以外の基礎パラメータ|基礎パラメータ|ゲージ|'
    r'SPD|SP(?!D)|RES|INT|DEF|CRD|CRT|ATK|HP)'
)

damage_type_map = {
'必殺技で与えるダメージ': 'Skill Damage',
'与えるすべてのダメージ': 'Damage',
'与える全てのダメージ': 'Damage',
'属性攻撃で与えるダメージ': 'Elemental Damage',
'単体攻撃': 'Single-Target Damage',
'全体攻撃': 'AoE Damage',
'必殺技': 'Skill Damage',
'通常攻撃': 'Normal Attack',
'無属性攻撃': 'Non-Elemental Damage',
'属性攻撃': 'Elemental Damage',
'受ける全てのダメージ': 'Damage Taken',
}
damage_keys = sorted(damage_type_map.keys(), key=len, reverse=True)
damage_pattern = '|'.join(map(re.escape, damage_keys))


element_map = {
'炎': 'Fire',
'水': 'Water',
'風': 'Wind',
'星': 'Star',
'無': 'Non-Elemental'
}
element_keys = sorted(element_map.keys(), key=len, reverse=True)
element_pattern = '|'.join(map(re.escape, element_keys))

race_map = {
    '魔物型': 'Monster',
    '人型': 'Humanoid',
}

timing_map = {
    'ターン開始時': 'At the start of the turn',
    'ターン終了時': 'At the end of the turn',
    '戦闘開始時': 'At the start of battle',
}

target_map = {
    '自分の': 'Self',
    'パーティの': 'All Allies',
    '敵全体の': 'All Enemies',
    '残りHPが高い敵キャラ': 'Highest-HP Foe',
    '残りHPの高い敵キャラ': 'Highest-HP Foe',
    '残りHPが低い敵キャラ': 'Lowest-HP Foe',
    '残りHPの低い敵キャラ': 'Lowest-HP Foe',
}

latent_type_map = {
    'キング': 'King',
    'クイーン': 'Queen',
    'ルーク': 'Rook',
    'ビショップ': 'Bishop',
    'ナイト': 'Knight',
    'ポーン': 'Pawn',
}

hp_cond = (
    r'(?:(?:自身の)?HPが)'
    r'(?P<threshold>\d+)%'
    r'(?P<comparator>以上|以下|未満)の場合、'
)

lead_timing = (
    r'(?P<lead>(?:、さらに|[、,])?)\s*'
    r'(?P<timing>ターン開始時、|ターン終了時、)?'
)


hp_cmp_map = {
    '以上': '>=',
    '以下': '<=',
    '未満': '<',
}

patterns = [

    # --- 1️⃣ End of Turn Defeat Foe Stat Buffs ✅ ---
    (
        re.compile(
            r'^(、さらに)?(ターン終了時)、敵キャラを倒していたら(?P<target>自分の|敵全体の)?'
            r'(?P<stats>(?:[A-Z]+(?:・[A-Z]+)*|HP以外の基礎パラメータ))\+#PER#(?:%|％)'  # Match single/multiple stats or "Non-HP Basic Stats"
            r'(?:\((?P<turns>\d+)(T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)$',  # Handle both T and ターン in duration
            flags=re.UNICODE
        ),
        lambda m: (
            f"{'Self' if m.group('target') == '自分の' else 'All Allies'}"  # Determine Target
            + ": At the "
            + "end of the turn, if unit has defeated a foe, "
            + (
                "Non-HP Basic Stats "  # Default to Non-HP Basic Stats
                if m.group('stats') == 'HP以外の基礎パラメータ' else  # If "HP以外の基礎パラメータ"
                f"{', '.join(m.group('stats').replace('・', '/').split('・'))} "  # Otherwise, show specific stats
            )
            + "+#PER#%"  # Stats or Non-HP Basic Stats
            + (
                f"({m.group('turns') or m.group('turns_alt')}T)" if (m.group('turns') or m.group('turns_alt')) else ''
            )  # Optional turns, either T or ターン
        )
    ),

    # --- 2️⃣ Static buffs/debuffs with no duration ✅ ---
    (
        re.compile(
            rf'^(?P<target>自分の|パーティの|敵全体の)?'
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'(?P<sign>[+-])#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            target_map.get(m.group('target'), '')
            + (": " if m.group('target') else "")
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + f" {m.group('sign')}#PER#%"
        )
    ),

    # --- 3️⃣ Simple Stat Buffs (No Timing) with Mandatory Leading Comma ✅ ---
    (
        re.compile(
            rf'^[、,]'  # match Japanese comma OR normal comma
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'(?P<sign>[+-])#PER#(?:%|％)'
            r'(?:\((?P<turns>\d+)T\)|（(?P<turns_alt>\d+)ターン）)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            ", "  # always include leading comma
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + f" {m.group('sign')}#PER#%"
            + (f"({m.group('turns') or m.group('turns_alt')}T)" 
            if (m.group('turns') or m.group('turns_alt')) else "")
        )
    ),

    # --- 4️⃣ Synchonization ✅ ---
    (
        re.compile(
            r'^(、さらに)?自身にシンクロ\(#PER#回\)付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(1) else ''}"  # Optional leading comma
            + "Self: Synchronization (#PER# times)"
        )
    ),

    # --- 5️⃣ Party Debuff Conversion at Start of Battle ✅ ---
    (
        re.compile(
            r'戦闘開始時、パーティに(?P<stats>(?:\w+・?)+)デバフ転換状態を付与\((?P<times>\d+)回\)',
            flags=re.UNICODE
        ),
        lambda m: f"All Allies: At start of battle, {m.group('stats').replace('・', '/')} Debuff Conversion ({m.group('times')} times)"
    ),

    # --- 6️⃣ Stat Buffs with Timing, Target, and optional Leading Comma ✅ ---
    (
        re.compile(
            r'^(、さらに)?(戦闘開始時|ターン(?P<timing>開始|終了)時)、'
            r'(?P<target>自分の|パーティの)?'
            r'(?P<stats>[A-Z]+(?:・[A-Z]+)*)\++#PER#(?:%|％)'  # Match both % and ％
            r'(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)$',  # End at turn duration
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(1) else ''}"  # Leading comma if there is one
            + (
                'Self' if m.group('target') == '自分の' else 'All Allies'
            )  # Determine target
            + ": At the "
            + (
                'start of battle' if m.group(2) == '戦闘開始時' else  # Handle "start of battle"
                ('start' if m.group('timing') == '開始' else 'end')
            )  # Handling start of battle vs start/end of turn
            + ("" if m.group(2) == '戦闘開始時' else " of the turn")  # Only add "of the turn" for turn-based cases
            + ", "
            + f"{m.group('stats').replace('・', '/')} +#PER#%"  # Stats, replace '・' with '/'
            + (
                f"({m.group('turns') or m.group('turns_alt')}T)" if (m.group('turns') or m.group('turns_alt')) else ''
            )  # Optional turns, either T or ターン
        )
    ),

    # --- 7️⃣ Standalone Stat Buffs (no timing clause, optional leading comma) ---
    (
        re.compile(
            r'^(?:、さらに|[、,])?\s*'                           # allow:  、さらに  OR  、  OR  , 
            r'(?P<stats>[A-Z]+(?:・[A-Z]+)*)'
            r'\+#PER#%'
            r'(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            ", "                               # always output with English comma
            + m.group('stats').replace('・', '/')
            + " +#PER#%"
            + (
                f"({m.group('turns') or m.group('turns_alt')}T)"
                if (m.group('turns') or m.group('turns_alt')) else ""
            )
        )
    ),
  
    # --- 8️⃣ Additional stat buffs for self/party  ✅ ---
    (
        re.compile(
            r'^(、さらに)(?P<target>自分の|パーティの|敵全体の)?(?P<stats>[A-Z]+(?:・[A-Z]+)*)\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)\))?'
        ),
        lambda m: (
            f", {target_map[m.group('target')]}: " if m.group('target') else ", "
        )
        + f"{m.group('stats').replace('・', '/')} +#PER#%"
        + (f"({m.group('turns')}T)" if m.group('turns') else "")
    ),

    # --- 9️⃣ Follow-up Attacks based on remaining HP ✅ ---    
    (
        re.compile(
            r'(、さらに)?'
            r'(?P<timing>ターン開始時|ターン終了時|戦闘開始時)、'
            r'(?P<hp_phrase>残りHPが高い敵キャラ|残りHPが低い敵キャラ|残りHPの低い敵キャラ)(?:単体)?'
            r'に(?P<element>[炎水風星])属性攻撃\((?P<hits>\d+)回[,，]威力(?P<power>[A-E]\+?)\)',
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(1) else ''}"
            f"{target_map[m.group('hp_phrase')]}: "
            f"{timing_map[m.group('timing')]}, "
            f"{element_map[m.group('element')]} Follow-up "
            f"({m.group('hits')} {'Time' if m.group('hits') == '1' else 'Times'}, Power {m.group('power')})"
        )
    ),

    # --- 1️⃣0️⃣ Party uses [Element] skill -> Buffs (Damage, stats, SP...) ✅ --- #
    (
        re.compile(
            rf'(?:[、,]\s*)?(?:さらに)?'
            rf'パーティが(?P<element>[炎水風星])属性の技を使用した(?:時|とき|際)、'
            rf'パーティ'
            rf'(?:'
                rf'に(?P<damage_type>与える全てのダメージ)'
                rf'|'
                rf'の(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
                rf'|'
                rf'の(?P<sp>SP)'
            rf')'
            rf'\+#PER#(?:%|％)?'          # ✅ % is OPTIONAL
            rf'(?:\((?P<turns>\d+)T\))?',
            flags=re.UNICODE
        ),
        lambda m: (
            (
                f"{', ' if m.group(0).startswith(('、', ',')) else ''}"
                f"All Allies: When a {element_map[m.group('element')]} skill is used, "
            )
            + (
                # 🟥 Damage (always %)
                f"{damage_type_map[m.group('damage_type')]} +#PER#%"
                if m.group('damage_type')

                # 🟩 SP (flat amount, no %)
                else (
                    "SP +#PER#"
                    if m.group('stats') == 'SP'

                    # 🟦 Stats (always %)
                    else f"{'/'.join(stat_map[s] for s in m.group('stats').split('・'))} +#PER#%"
                )
            )
            + (
                f" ({m.group('turns')}T)"
                if m.group('turns')
                else ""
            )
        )
    ),


    # --- 1️⃣1️⃣ Party Crits -> Multi-Stat Buffs ✅ ---
    (
        re.compile(
            rf'^パーティがクリティカル時、'
            rf'パーティの(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#(?:%|％)'
            r'(?:\((?P<turns>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            "All Allies: When any ally crits, "
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
            + (f" ({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    # --- 1️⃣2️⃣ Weapon-equipped self: damage and stat buffs ✅ --- #
    (
        re.compile(
            r"(?:[、,]\s*)?(?:さらに)?自分が"
            r"(?P<weapon>剣|杖|魔物魔法|魔物物理|拳|銃|斧|弓|槍)武器装備時、"
            r"(?:(?:(?P<element>[炎水風星])属性)?(?:攻撃で)?(?P<damage_type>与える全てのダメージ|必殺技で与えるダメージ|属性攻撃で与えるダメージ)"
            r"|\s*(?P<stats>[A-Z・]+))"
            r"\+#PER#%",
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(0).startswith(('、', ',')) else ''}"
            f"{weapon_map[m.group('weapon')]}-Equipped Self: "
            + (
                # 🟥 Damage case
                (
                    f"{element_map[m.group('element')]} " if m.group('element') else ""
                )
                + f"{damage_type_map[m.group('damage_type')]} +#PER#%"
                if m.group('damage_type')
                # 🟦 Stat buff case
                else f"{m.group('stats').replace('・', '/')} +#PER#%"
            )
        )
    ),

    # --- 1️⃣2️⃣ Alternative: Weapon-equipped self: elemental party damage buff ✅ --- #
    (
        re.compile(
            r'^(?P<lead>[、,])?(?:さらに)?'
            r'自分が(?P<weapon>剣|杖|魔物魔法|魔物物理|拳|銃|斧|弓|槍)武器装備時、'
            r'パーティが(?P<damage_type>'
            r'属性攻撃で与えるダメージ|'
            r'与える全てのダメージ|与えるすべてのダメージ|'
            r'必殺技で与えるダメージ'
            r')'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{weapon_map[m.group('weapon')]}-Equipped Self: "
            + "All Allies: "
            + f"{damage_type_map.get(m.group('damage_type'), m.group('damage_type'))} +#PER#%"
        )
    ),

    # --- 1️⃣3️⃣ Gender-based dame dealt/taken ✅ ---
    (
        re.compile(
            r"(?:[、,]\s*)?(?:さらに)?"
            r"(?P<target>自分が|パーティの)"
            r"(?P<gender>男性|女性)キャラ"
            r"(?:(?P<direction>から|に)|が)?"
            r"(?P<type>与える|受ける)?(?:全ての)?ダメージ"
            r"(?P<value>(?:[+-]#PER#|[+-]?\d+)[%％])",
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(0).startswith(('、', ',')) else ''}"
            +
            (
                "Self" if m.group('target') == '自分が'
                else "All Allies"
            )
            + ": "
            +
            (
                # Determine the English phrasing based on available cues
                "Damage dealt to " if m.group('type') == '与える' or m.group('direction') == 'に'
                else "Damage taken from " if m.group('direction') == 'から'
                else "Damage taken by "
            )
            + ("male" if m.group('gender') == '男性' else "female")
            + " units "
            + m.group('value').replace('％', '%')
        )
    ),

    # --- 1️⃣4️⃣ When Attacked Stat Buffs ✅ ---
    (
        re.compile(
            r"(?:[、,]\s*)?(?:さらに)?"
            r"(?:(?P<trigger_party>パーティが)?攻撃を受けた時、)"  # trigger: "when (party) is attacked"
            r"(?:(?P<buff_target>自分|パーティ)の)?"               # buff target: self or party
            r"(?P<stats>HP以外の基礎パラメータ|基礎パラメータ|[A-Z・]+|ゲージ|SP)"
            r"\+(?P<value>#PER#％|#PER#%|[0-9]+％|[0-9]+%)"
            r"(?:[\(（](?P<duration>\d+T|\d+ターン)[\)）])?",
            flags=re.UNICODE
        ),
        lambda m: (
            f"{', ' if m.group(0).startswith(('、', ',')) else ''}"
            f"{'All Allies' if m.group('buff_target') == 'パーティ' else 'Self'}: "
            f"When the {'party' if m.group('trigger_party') else 'unit'} is attacked, "
            f"{'/'.join(stat_map.get(s, s) for s in m.group('stats').split('・'))} "
            f"+{m.group('value').replace('％', '%')}"
            + (f" ({m.group('duration').replace('ターン', 'T')})" if m.group('duration') else "")
        )
    ),

    # --- 1️⃣5️⃣ Weapon-Wielding Party Damage Dealt/Taken ✅ ---
    (
        re.compile(
        r"(?P<lead>[、,])?(?:さらに)?パーティの(?P<weapon>.+?)武器装備キャラが"
        r"(?:(?P<condition>.+?)で)?"
        r"(?P<direction>与える|受ける)"
        r"(?P<scope>全ての)?ダメージ(?P<sign>\+|\-)#PER#[%％]",
        flags=re.UNICODE
    ),
        lambda m: (
            # optional leading comma
            (", " if m.group('lead') else "")
            # weapon info
            + f"{'/'.join(weapon_map.get(w, w) for w in m.group('weapon').split('・'))}-Wielding Allies: "
            # direction branch
            + (
                # Damage dealt
                f"{damage_type_map.get(m.group('condition'), 'Damage')} {m.group('sign')}#PER#%"
                if m.group('direction') == '与える'
                # Damage taken
                else f"Damage taken"
                + (f" from {damage_type_map.get(m.group('condition'), '')}" if m.group('condition') else "")
                + f" {m.group('sign')}#PER#%"
            )
        )
    ),

    # --- 1️⃣6️⃣ Multi-Stat Buffed Allies/Self at Turn Start/End ✅ ---
    (
        re.compile(
            rf'^(?P<prefix>(?:、さらに|[、,])?)\s*'                            # optional leading comma or "、さらに"
            rf'(?P<timing>ターン開始時|ターン終了時|戦闘開始時)、'             # timing
            rf'パーティの(?P<cond_stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'  # condition stats
            rf'バフ効果を受けている(?P<who>キャラ|味方)の'                     # who = キャラ | 味方
            rf'(?P<apply_stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)' # applied stats
            r'\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?$',
            flags=re.UNICODE
        ),
                lambda m: (
            f"{m.group('cond_stats').replace('・', '/')}-Buffed "
            f"{'Self' if m.group('who') in ('自身','自分') else 'Allies'}: "
            f"At the "
            f"{'start' if m.group('timing') == 'ターン開始時' else 'end' if m.group('timing') == 'ターン終了時' else 'start of battle'}"
            f"{'' if m.group('timing') == '戦闘開始時' else ' of the turn'}, "
            f"{m.group('apply_stats').replace('・', '/')} +#PER#%"
            f"{'(' + (m.group('turns') or m.group('turns_alt')) + 'T)' if (m.group('turns') or m.group('turns_alt')) else ''}"
        )
    ),

    # --- 1️⃣7️⃣ I -Multi-Stat Buffed Self at Turn Start/End ✅ ---
    (
    re.compile(
        rf'^(?P<timing>ターン開始時|ターン終了時)、'
        rf'(?P<cond_stats>{stats_pattern})バフ効果を受けている場合、'
        rf'(?P<apply_stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
        r'\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?$',
        flags=re.UNICODE
    ),
    lambda m: (
        f"{m.group('cond_stats')}-Buffed Self: "
        f"At the {'start' if m.group('timing')=='ターン開始時' else 'end'} of the turn, "
        f"{m.group('apply_stats').replace('・','/')} +#PER#%"
        f"{'(' + (m.group('turns') or m.group('turns_alt')) + 'T)' if (m.group('turns') or m.group('turns_alt')) else ''}"
    )),

    # --- 1️⃣7️⃣ II - Buffed Self → SP Gain at Turn Start/End ---
    (
        re.compile(
            rf'^(?P<timing>ターン開始時|ターン終了時)、'
            rf'(?P<cond_stat>{stats_pattern})バフ効果を受けている場合、'
            rf'自分のSP\+#PER#(?:%|％)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            f"{stat_map.get(m.group('cond_stat'), m.group('cond_stat'))}-Buffed Self: "
            f"At the {'start' if m.group('timing') == 'ターン開始時' else 'end'} of the turn, "
            f"SP +#PER#%"
        )
    ),

    # --- 1️⃣7️⃣ -  III Buffed Self → Party buffs ✅ ---
    (
        re.compile(
            rf'^(?P<timing>ターン開始時|ターン終了時)、'
            rf'(?P<cond_stat>{stats_pattern})バフ効果を受けている場合、'
            rf'パーティの(?P<apply_stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            f"{stat_map.get(m.group('cond_stat'), m.group('cond_stat'))}-Buffed Self: "
            f"All Allies, At the {'start' if m.group('timing') == 'ターン開始時' else 'end'} of the turn, "
            + "/".join(stat_map.get(s, s) for s in m.group('apply_stats').split('・'))
            + " +#PER#%"
            + (
                f"({m.group('turns') or m.group('turns_alt')}T)"
                if (m.group('turns') or m.group('turns_alt')) else ""
            )
        )
    ),

    # --- 1️⃣7️⃣ IV - Buffed Self → Damage Buffs ✅ ---
    (
        re.compile(
            rf'^(?P<lead>[、,])(?:さらに)?'
            rf'自身が(?P<cond_stat>{stats_pattern})バフ効果を受けている場合、'
            rf'(?P<damage_type>'
            rf'与える全てのダメージ|与えるすべてのダメージ|'
            rf'必殺技で与えるダメージ|'
            rf'属性攻撃で与えるダメージ'
            rf')'
            r'\+#PER#(?:%|％)'
            r'(?:\((?P<turns>\d+)(?:T|ターン)\))?'
            r'付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            ", "
            + f"{stat_map.get(m.group('cond_stat'), m.group('cond_stat'))}-Buffed Self: "
            + f"{damage_type_map.get(m.group('damage_type'), m.group('damage_type'))} "
            + "+#PER#%"
            + (f"({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),


    #--- 1️⃣8️⃣ Highest/Lowest Stat Ally Buffs at Turn Start/End ✅ ---
    (
        re.compile(
            rf'\s*'  # allow whitespace
            r'(?P<timing>ターン開始時|ターン終了時)、'
            rf'最も(?P<compare_stat>{stats_pattern})が(?P<order>高い|低い)味方キャラの'
            rf'(?P<stat_block>HP以外の基礎パラメータ|{stats_pattern}(?:・{stats_pattern})*)'
            r'\+#PER#[%％]'
            r'(?:\((?P<duration>\d+)(?:T|ターン)?\))?'
            r'\s*$',  # allow trailing whitespace
            flags=re.UNICODE
        ),
        lambda m: (
            f"{'Lowest' if m.group('order') == '低い' else 'Highest'}-{m.group('compare_stat')} Ally: "
            + ("At the start of the turn, " if m.group('timing') == "ターン開始時" else "At the end of the turn, ")
            + (
                "All Stats except HP"
                if m.group('stat_block') == "HP以外の基礎パラメータ"
                else "/".join(m.group('stat_block').split('・'))
            )
            + " +#PER#%"
            + (f" ({m.group('duration')}T)" if m.group('duration') else "")
        )
    ),

   # --- 1️⃣9️⃣ Highest Stat Ally Damage Buffs at Turn Start/End ✅ ---
    (
        re.compile(
            rf'^ターン(?P<timing>開始|終了)時、'                              # timing
            rf'(?:パーティの)?'                                             # optional "パーティの" (second form)
            rf'最も(?P<compare_stat>{stats_pattern})(?:が|の)高い'            # compare stat + が|の
            rf'(?:味方(?:キャラ)?|キャラ)に'                                # "味方キャラに" or "キャラに"
            rf'(?P<dtype>必殺技で与えるダメージ|与える全てのダメージ|与えるダメージ)'
            r'\+#PER#%'                                                     # percent token
            r'(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?'  # duration (optional)
            r'付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            # compare_stat -> prefer mapped (e.g. 'SPD' -> 'SPD' or Japanese->English if present)
            f"Highest-{stat_map.get(m.group('compare_stat'), m.group('compare_stat'))} Ally: "
            f"At the {'start' if m.group('timing') == '開始' else 'end'} of the turn, "
            f"{damage_type_map.get(m.group('dtype'), m.group('dtype'))} +#PER#%"
            f"{'(' + (m.group('turns') or m.group('turns_alt')) + 'T)' if (m.group('turns') or m.group('turns_alt')) else ''}"
        )
    ),

    # --- 2️⃣0️⃣ Highest/Lowest AG Ally Effects at Turn Start/End (AG, SP, Heal) ✅ ---
    (
        re.compile(
            r"ターン(?P<timing>開始|終了)時、"
            r"行動ゲージが(?P<position>先頭|最後尾)の味方キャラの"
            r"(?:(?P<hp>HPを、自身の最大HPの#PER#(?:%|％)回復)"
            r"|(?P<stat>SP|ゲージ)\+#PER#)",
            flags=re.UNICODE
        ),
        lambda m: (
            f"{'Highest' if m.group('position')=='先頭' else 'Lowest'}-AG Ally: "
            f"At the {'start' if m.group('timing')=='開始' else 'end'} of turn, "
            +
            (
                # HP heal block
                "Heal #PER#% of max HP"
                if m.group('hp')
                else
                # SP / Gauge block
                f"{stat_map.get(m.group('stat'), m.group('stat'))} +#PER#"
            )
        )
    ),

    # --- 2️⃣1️⃣ Highest/Lowest AG Ally Multi-Stat Buffs at Turn Start/End ✅ ---
    (
        re.compile(
            rf"ターン(?P<timing>開始|終了)時、"
            rf"行動ゲージが(?P<position>先頭|最後尾)の味方キャラの"
            rf"(?P<buffs>(?:(?!(?<![A-Z・])SP(?![A-Z・])|ゲージ){stats_pattern})(?:・(?:(?!(?<![A-Z・])SP(?![A-Z・])|ゲージ){stats_pattern}))*)"
            rf"\+#PER#(?P<percent>%|％)?"
            rf"(?:\((?P<turns>\d+)(?:T|ターン)\))?",
            flags=re.UNICODE
        ),
        lambda m: (
            f"{'Highest' if m.group('position')=='先頭' else 'Lowest'}-AG Ally: "
            f"At the {'start' if m.group('timing')=='開始' else 'end'} of turn, "
            f"{'/'.join(m.group('buffs').split('・'))} "
            f"+#PER#%"
            + (f" ({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    # --- 2️⃣2️⃣ All Enemy Multi-Stat Debuffs. Optional leading comma ✅ ---
    (
        re.compile(
            rf'^(?P<prefix>(?:、さらに|[、,])?)\s*'
            r'敵全体の'
            rf'(?P<stats>(?:HP以外の基礎パラメータ|{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'-#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group("prefix") else "")   # << normalized comma+space ALWAYS
            + "All Enemies: "
            + (
                "Non-HP Basic Stats"
                if m.group("stats") == "HP以外の基礎パラメータ"
                else "/".join(stat_map.get(s, s) for s in m.group("stats").split("・"))
            )
            + " -#PER#%"
        )
    ),

    # --- 2️⃣3️⃣ Auto-Revive for Self/Party. Optional leading comma ✅ ---
    (
        re.compile(
            r'^(?P<prefix>(?:、さらに|[、,])?)\s*'
            r'(?P<who>パーティ|自分)に自動蘇生付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group("prefix") else "")
            + ("All Allies" if m.group("who") == "パーティ" else "Self")
            + ": Auto-Revive"
        )
    ),

    # --- 2️⃣4️⃣ Single stat Buffed Allies, buffs with optional timing ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'(?:(?P<timing>ターン開始時|ターン終了時)、)?'   # 🔹 timing OPTIONAL
            r'パーティの(?P<buff>ATK|DEF|INT|RES|SPD|CRD|CRT)'
            r'バフ効果を受けている(?P<who>キャラ|味方)の'
            r'(?P<stats>[A-Z・]+)'
            r'\+#PER#(?:%|％)?'
            r'(?:\((?P<duration>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            # leading comma
            (", " if m.group('lead') else "")
            # buff source
            + f"{stat_map.get(m.group('buff'), m.group('buff'))}-Buffed "
            # who
            + ("Allies: " if m.group('who') == '味方' else "Allies: ")
            # timing (ONLY if present)
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            # applied stats
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
            # duration
            + (f"({m.group('duration')}T)" if m.group('duration') else "")
        )
    ),

    # --- 2️⃣5️⃣ Multi-stat Buffed Allies, buffs with optional timing ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'(?:(?P<timing>ターン開始時|ターン終了時)、)?'   # 🔹 timing OPTIONAL
            r'(?P<buffs>(?:ATK|DEF|INT|RES|SPD|CRD|CRT)'
            r'(?:・(?:ATK|DEF|INT|RES|SPD|CRD|CRT))+?)'
            r'バフ効果のいずれかを受けている場合、'
            r'パーティの(?P<stats>[A-Z・]+)'
            r'\+#PER#(?:%|％)'
            r'(?:\((?P<duration>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            # leading comma
            (", " if m.group('lead') else "")
            # condition buffs
            + f"{'/'.join(stat_map.get(b, b) for b in m.group('buffs').split('・'))}-Buffed Allies: "
            # timing (ONLY if present)
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            # applied stats
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
            # duration
            + (f"({m.group('duration')}T)" if m.group('duration') else "")
        )
    ),

    # --- 2️⃣6️⃣ Highest/Lowest AG Enemy Multi-Stat Debuffs (optional leading comma, optional timing) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'(?P<timing>ターン(?P<when>開始|終了)時、)?'
            rf'行動ゲージが(?P<position>先頭|最後尾)の敵キャラの'
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            rf'-(?P<value>#PER#)(?:%|％)'
            rf'(?:\((?P<turns>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{'Highest' if m.group('position') == '先頭' else 'Lowest'}-AG Enemy: "
            + (
                f"At the {'start' if m.group('when') == '開始' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " -#PER#%"
            + (f" ({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    # --- 2️⃣7️⃣ Highest/Lowest Stat Enemy Multi-Stat Debuffs at Turn Start/End ✅ ---
    (
        re.compile(
            rf'^ターン(?P<timing>開始|終了)時、'
            rf'最も(?P<compare_stat>{stats_pattern})が(?P<order>高い|低い)敵キャラの'
            rf'(?P<stat_block>HP以外の基礎パラメータ|'
            rf'(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            rf'-(?P<value>#PER#)(?:%|％)'
            rf'(?:\((?P<duration>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            f"{'Highest' if m.group('order') == '高い' else 'Lowest'}-"
            f"{stat_map.get(m.group('compare_stat'), m.group('compare_stat'))} Enemy: "
            f"At the {'start' if m.group('timing') == '開始' else 'end'} of the turn, "
            + (
                "Non-HP Basic Stats"
                if m.group('stat_block') == "HP以外の基礎パラメータ"
                else "/".join(stat_map.get(s, s) for s in m.group('stat_block').split('・'))
            )
            + " -#PER#%"
            + (f"({m.group('duration')}T)" if m.group('duration') else "")
        )
    ),

    # --- 2️⃣8️⃣ Party Stat Buffs if X+ Latent-Type Units Are Present (optional leading comma, timing, multi-types) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'(?P<timing>ターン開始時、|ターン終了時、)?'
            rf'(?:パーティに)?'   # ✅ FIX
            rf'潜在タイプ\[(?P<latent>[^\]]+)\]のキャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'パーティの(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: "
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If {m.group('count')}+ ["
            + "/".join(latent_type_map.get(t, t) for t in m.group('latent').split('・'))
            + "] Type units are present, "
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
        )
    ),

    ## --- 2️⃣9️⃣ Party Damage Buff if X+ Latent-Type Units Are Present (optional leading comma, timing, multi-types) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'               # optional leading comma
            rf'(?P<timing>ターン開始時、|ターン終了時、)?'        # optional timing
            rf'(?:パーティに)?'                                # 🔥 OPTIONAL パーティに
            rf'潜在タイプ\[(?P<latent>[^\]]+)\]のキャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'パーティが(?P<damage_type>'
            rf'必殺技で与えるダメージ|'
            rf'与える全てのダメージ|与えるすべてのダメージ|'
            rf'属性攻撃で与えるダメージ'
            rf')'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: "
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If {m.group('count')}+ ["
            + "/".join(latent_type_map.get(t, t) for t in m.group('latent').split('・'))
            + "] Type units are present, "
            + f"{damage_type_map.get(m.group('damage_type'), m.group('damage_type'))} +#PER#%"
        )
    ),

    # --- 3️⃣0️⃣ Party Damage Buff if Latent-Type Units Are Present (optional leading comma, multi-types) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'(?:パーティの)?'  # optional
            rf'潜在タイプ\[(?P<latent>[^\]]+)\]のキャラが'
            rf'(?P<damage>'
            rf'必殺技で与えるダメージ|'
            rf'与える全てのダメージ|'
            rf'与えるすべてのダメージ'
            rf')'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{'/'.join(latent_type_map.get(t, t) for t in m.group('latent').split('・'))} Allies: "
            + f"{damage_type_map.get(m.group('damage'), m.group('damage'))} +#PER#%"
        )
    ),

    # --- 3️⃣1️⃣ Party Stat Buff if Latent-Type Units Are Present (optional leading comma, multi-types) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'(?:パーティの)?'
            rf'潜在タイプ\[(?P<latent>[^\]]+)\]のキャラの'
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{'/'.join(latent_type_map.get(t, t) for t in m.group('latent').split('・'))} Allies: "
            + f"{'/'.join(stat_map.get(s, s) for s in m.group('stats').split('・'))} +#PER#%"
        )
    ),

    # --- 3️⃣2️⃣ Initial SP Buff at Start of Battle for Self/Party ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'戦闘開始時、'
            r'(?P<target>自分の|パーティの)'
            r'初期SP'
            r'\+#PER#(?:%|％)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                "Self" if m.group('target') == '自分の'
                else "All Allies"
            )
            + ": At the start of battle, Initial SP +#PER#%"
        )
    ),

    # --- 3️⃣3️⃣ Party Stat Buff if X+ Weapon-Wielding Units Are Present (optional leading comma, multi-types) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'パーティに得意武器種が\[(?P<weapons>[^\]]+)\]のキャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'(?P<target>自分の|パーティの)'
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#(?:%|％)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                "Self" if m.group('target') == '自分の'
                else "All Allies"
            )
            + ": "
            + f"If {m.group('count')}+ ["
            + "/".join(weapon_map.get(w, w) for w in m.group('weapons').split('・'))
            + "] Allies, "
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
        )
    ),

    # --- 3️⃣4️⃣ Party Buff Effects Buff ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'パーティが使用するバフの効果'
            r'(?P<sign>\+|-)'
            r'(?P<value>\d+|#PER#)'
            r'(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: Buff Effects "
            + f"{m.group('sign')}{m.group('value')}%"
        )
    ),

    # --- 3️⃣5️⃣ Party SP Cost Reduction Buff ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'パーティの消費SP-'
            r'(?P<value>#PER#|\d+)'
            r'(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: SP Cost -"
            + f"{m.group('value')}%"
        )
    ),

    # --- 3️⃣6️⃣ Self Stat Buff if X+ Race Units Are Present (optional leading comma) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'パーティに(?P<race>{"|".join(map(re.escape, race_map.keys()))})キャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'自分の(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            rf'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "Self: "
            + f"If {m.group('count')}+ "
            + f"{race_map.get(m.group('race'), m.group('race'))} units are present, "
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
        )
    ),

    # --- 3️⃣7️⃣ Party Damage Buff if X+ Race Units Are Present (optional leading comma, timing) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'               # optional leading comma
            rf'(?P<timing>ターン開始時、|ターン終了時、)?'        # optional timing
            rf'(?:パーティに)?'                                # optional パーティに
            rf'(?P<race>魔物型|人型)キャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'パーティが(?P<damage_type>'
            rf'必殺技で与えるダメージ|'
            rf'与える全てのダメージ|与えるすべてのダメージ|'
            rf'属性攻撃で与えるダメージ'
            rf')'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: "
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If {m.group('count')}+ "
            + f"{race_map.get(m.group('race'), m.group('race'))} units are present, "
            + f"{damage_type_map.get(m.group('damage_type'), m.group('damage_type'))} +#PER#%"
        )
    ),

    # --- 3️⃣8️⃣ Party Stat Buff if X+ Race Units Are Present (optional leading comma, timing) ✅ ---
    (
        re.compile(
            rf'^(?P<lead>(?:、さらに|[、,])?)\s*'
            rf'(?P<timing>ターン開始時、|ターン終了時、)?'
            rf'(?:パーティに)?'
            rf'(?P<race>魔物型|人型)キャラが'
            rf'(?P<count>\d+)体以上いる場合、'
            rf'パーティの(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            r'\+#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "All Allies: "
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If {m.group('count')}+ "
            + f"{race_map.get(m.group('race'), m.group('race'))} units are present, "
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + " +#PER#%"
        )
    ),

    # --- 3️⃣9️⃣ Self Invincibility (optional leading comma, timing) ✅ ---
    (
        re.compile(
            r'^(?P<lead>(?:、さらに|[、,])?)\s*'
            r'(?P<timing>戦闘開始時、|ターン開始時、|ターン終了時、)?'
            r'自分に無敵\(#PER#回\)付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + "Self: "
            + (
                f"At {('the start of the battle' if m.group('timing') == '戦闘開始時、' else 'the start of the turn' if m.group('timing') == 'ターン開始時、' else 'the end of the turn')}, "
                if m.group('timing') else ""
            )
            + "grant Invincibility (#PER# Times)"
        )
    ),

    # --- 4️⃣0️⃣ - 🅰️ HP Conditional Buffs: SP Buffs  ✅ ---
    (
        re.compile(
            rf'^{lead_timing}'
            rf'{hp_cond}'
            rf'(?P<target>パーティ|自分)のSP'
            rf'(?P<sign>[+-])#PER#(?:%|％)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If HP {hp_cmp_map[m.group('comparator')]} {m.group('threshold')}%, "
            + ("All Allies: " if m.group('target') == 'パーティ' else "Self: ")
            + f"SP {m.group('sign')}#PER#%"
        )
    ),

    #  --- 4️⃣0️⃣ - 🅱️ HP Conditional Buffs: Multi-Stat Buffs  ✅ ---
    (
        re.compile(
            rf'^{lead_timing}'
            rf'{hp_cond}'
            rf'(?P<target>パーティ|自分)の'
            rf'(?P<stats>(?:{stats_pattern})(?:・(?:{stats_pattern}))*)'
            rf'(?P<sign>[+-])#PER#(?:%|％)?'
            rf'(?:\((?P<turns>\d+)(?:T|ターン)\))?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If HP {hp_cmp_map[m.group('comparator')]} {m.group('threshold')}%, "
            + ("All Allies: " if m.group('target') == 'パーティ' else "Self: ")
            + "/".join(stat_map.get(s, s) for s in m.group('stats').split('・'))
            + f" {m.group('sign')}#PER#%"
            + (f"({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    #  --- 4️⃣0️⃣ - 🅲️ HP Conditional Buffs: Damage Buffs  ✅ ---
    (
        re.compile(
            rf'^{lead_timing}'
            rf'{hp_cond}'
            rf'(?P<target>パーティ|自分)に?'
            rf'(?P<damage>'
                rf'必殺技で与えるダメージ|'
                rf'与える全てのダメージ|'
                rf'与えるすべてのダメージ|'
                rf'受ける全てのダメージ'
            rf')'
            rf'(?P<sign>[+-])#PER#(?:%|％)?'
            rf'(?:\((?P<turns>\d+)(?:T|ターン)\))?'
            rf'(?:付与)?$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If HP {hp_cmp_map[m.group('comparator')]} {m.group('threshold')}%, "
            + ("All Allies: " if m.group('target') == 'パーティ' else "Self: ")
            + f"{damage_type_map.get(m.group('damage'), m.group('damage'))} "
            + f"{m.group('sign')}#PER#%"
            + (f"({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    #  --- 4️⃣0️⃣ - 🅳️ HP Conditional Buffs: Invincibility Buffs  ✅ ---
    (
        re.compile(
            rf'^{lead_timing}'
            rf'{hp_cond}'
            rf'(?P<target>パーティ|自分)に無敵'
            rf'\(#PER#回\)付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (
                f"At the {'start' if m.group('timing') == 'ターン開始時、' else 'end'} of the turn, "
                if m.group('timing') else ""
            )
            + f"If HP {hp_cmp_map[m.group('comparator')]} {m.group('threshold')}%, "
            + ("All Allies: " if m.group('target') == 'パーティ' else "Self: ")
            + "Invincibility (#PER# Times)"
        )
    ),

    # --- 4️⃣1️⃣ - I: Chained Elemental Damage Buffs ✅ ---
    (
        re.compile(
            rf'^(?P<lead>[、,])'
            rf'(?:(?P<element>[炎水風星])属性)?'
            rf'攻撃で与えるダメージ'
            r'\+#PER#(?:%|％)'
            r'(?:\((?P<turns>\d+)(?:T|ターン)\))?'
            r'付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            ", "
            + (f"{element_map[m.group('element')]} " if m.group('element') else "")
            + "Damage +#PER#%"
            + (f"({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    # --- 4️⃣1️⃣ - II: Chained Damage Type Buffs ✅ ---
    (
        re.compile(
            rf'^(?P<lead>[、,])'
            rf'(?P<damage_type>'
            rf'与える全てのダメージ|与えるすべてのダメージ|'
            rf'必殺技で与えるダメージ|'
            rf'属性攻撃で与えるダメージ|'
            rf'無属性攻撃で与えるダメージ'
            rf')'
            r'\+#PER#(?:%|％)'
            r'(?:\((?P<turns>\d+)(?:T|ターン)\))?'
            r'付与$',
            flags=re.UNICODE
        ),
        lambda m: (
            ", "
            + f"{damage_type_map.get(m.group('damage_type'), m.group('damage_type'))} "
            + "+#PER#%"
            + (f"({m.group('turns')}T)" if m.group('turns') else "")
        )
    ),

    # 4️⃣2️⃣ Race-based stat buffs without timing , optional duration ✅ ---
    (
        re.compile(
            r'^(?P<lead>、さらに|、|,)?'
            r'パーティの(?P<race>魔物型|人型)キャラの'
            r'(?P<stats>[A-Z・]+)\+#PER#%'
            r'(?:[（(]?(?P<duration>\d+T|\d+ターン)[）)]?)?'
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{race_map[m.group('race')]} Allies: "
            + f"{m.group('stats').replace('・', '/')} +#PER#%"
            + (f"({m.group('duration').replace('ターン', 'T')})" if m.group('duration') else "")
        )
    ),

    # 4️⃣3️⃣  Race-based stat buffs with timing (start of battle or turn), optional duration ✅ --
    (
        re.compile(
            r'^(?P<lead>、さらに|、|,)?'
            r'(?P<timing>戦闘開始時|ターン開始時|ターン終了時)、'
            r'パーティの(?P<race>魔物型|人型)キャラの'
            r'(?P<stats>[A-Z・]+)\+#PER#%'
            r'(?:[（(]?(?P<duration>\d+T|\d+ターン)[）)]?)?',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{timing_map[m.group('timing')]}, "
            + f"{race_map[m.group('race')]} Allies: "
            + f"{m.group('stats').replace('・', '/')} +#PER#%"
            + (f"({m.group('duration').replace('ターン', 'T')})" if m.group('duration') else "")
        )
    ),


    #FALLBACK. Matches unconditional party-wide damage buffs ONLY.
    # Must appear after all conditional damage rules.
    # ---  ✅ --- #
    (
        re.compile(
            rf'^(?P<lead>、さらに|、|,)?(?:さらに)?'
            rf'(?:自分が(?P<weapon>{weapon_pattern})武器装備時、)?'
            rf'パーティが'
            rf'(?:(?P<element>{element_pattern})属性)?'
            rf'(?P<damage>{damage_pattern})'
            r'[+-]?#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + (f"{weapon_map[m.group('weapon')]}-Equipped Self: " if m.group('weapon') else "")
            + "All Allies: "
            + (
                f"{element_map[m.group('element')]} "
                if m.group('element') else ""
            )
            + f"{damage_type_map.get(m.group('damage'), m.group('damage'))} +#PER#%"
        )
    ),


    # Buffed Self + SP buffs
    (
        re.compile(
            r'(?P<lead>[、,])?(?:さらに)?(?P<timing>ターン開始時|ターン終了時)、'
            r'(?P<buff>[A-Z]+)バフ効果を受けている場合、'
            r'(?P<target>パーティ|自分)の(?P<stat>[A-Z]+)\+#PER#(?!%)'
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{m.group('buff')}-buffed Self: "
            + ("At the start of the turn" if m.group('timing') == "ターン開始時" else "At the end of the turn")
            + ", "
            + ("All Allies " if m.group('target') == "パーティ" else "")
            + f"{m.group('stat')} +#PER#"
        )
    ),

    # Buffed Self + Stat buffs
    (
        re.compile(
            r'(?P<lead>[、,])?(?:さらに)?'
            r'(?:(?P<timing>ターン開始時|ターン終了時)、)?'
            r'(?P<buffs>[A-Z・]+)バフ効果を受けている場合、'
            r'(?P<target>自分|パーティ)の'
            r'(?P<stats>[A-Z・]+)'
            r'\+?#PER#%?'
            r'(?:\((?P<duration>\d+T|\d+ターン)\))?'
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{'/'.join(m.group('buffs').split('・'))}-buffed Self: "
            + (
                "At the start of the turn, " if m.group('timing') == "ターン開始時"
                else "At the end of the turn, " if m.group('timing') == "ターン終了時"
                else ""
            )
            + (
                "All Allies " if m.group('target') == "パーティ" else ""
            )
            + f"{'/'.join(m.group('stats').split('・'))} +#PER#%"
            + (f" ({m.group('duration').replace('ターン', 'T')})" if m.group('duration') else "")
        )
    ),

    # Conditional Buffs Based on Enemy Debuff Status, Party
    (
        re.compile(
            r'ターン(?P<timing>開始|終了)時、(?P<debuff>[A-Za-z]+デバフ状態)の敵がいる場合、パーティの(?P<stats>[A-Z・]+)\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)\))?',
            flags=re.UNICODE
        ),
        lambda m: (
            f"All Allies: At the {'end' if m.group('timing') == '終了' else 'start'} of this unit's turn, "
            f"if there is a foe with a {m.group('debuff').replace('デバフ状態', '')} debuff, "
            f"{m.group('stats').replace('・', '/')} +#PER#%"
            f"({m.group('turns')}T)" if m.group('turns') else ''
        )
    ),

    # Conditional Buffs Based on Enemy Debuff Status, Self
    (
        re.compile(
            r'ターン(?P<timing>開始|終了)時、(?P<stat_debuff>[A-Z]+)デバフ状態の敵がいる場合、?自分の(?P<stats>[A-Z]+(?:・[A-Z]+)*)\+#PER#%(?:\((?P<turns>\d+)(?:T|ターン)?\)|（(?P<turns_alt>\d+)ターン）)?'
        ),
        lambda m: (
            f"Self: At the {'start' if m.group('timing') == '開始' else 'end'} of this unit's turn, "
            f"if there is a foe with a {m.group('stat_debuff')} debuff, "
            f"{m.group('stats').replace('・', '/')} +#PER#%"
            f"{f'({m.group('turns') or m.group('turns_alt')}T)' if (m.group('turns') or m.group('turns_alt')) else ''}"
        ),
    ),

    # Party [element] damage +#PER#% dealt/taken. Optional equipped weapon condition.
    (
        re.compile(
            r'^(?P<lead>、さらに|、|,)?(?:さらに)?(?:自分が(?P<weapon>剣|杖|魔物魔法|魔物物理|拳|銃|斧|弓|槍)武器装備時、)?'
            r'パーティが(?P<element>[一-龯無]+)属性攻撃で(?P<direction>与える|受ける)ダメージ[+-]?#PER#(?:%|％)$',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")  # Leading comma if it exists
            + (f"{weapon_map[m.group('weapon')]}-Equipped Self: " if m.group('weapon') else "")  # Include weapon if present
            + f"All Allies: {element_map.get(m.group('element'), m.group('element'))} "  # Map element dynamically
            + ("damage +#PER%" if m.group('direction') == "与える" else "damage taken -#PER%")  # Handle direction
        )
    ),

    # Self [element] damage +#PER#% dealt/taken. Optional equipped weapon condition
    (
        re.compile(
            r'(?P<lead>[、,])?自分が(?P<weapon>剣|杖|魔物魔法|魔物物理|拳|銃|斧|弓|槍)?'
            r'(武器装備時、)?(?P<element>無|炎|水|風|星)属性攻撃で(?P<type>与える|受ける)ダメージ'
            r'(?P<sign>\+|-)?(?P<percentage>(?:\d+%|#PER#％|#PER#%))',
            flags=re.UNICODE
        ),
        lambda m: (
            (", " if m.group('lead') else "")  # Leading comma if it exists
            + (f"{weapon_map[m.group('weapon')]}-Equipped Self: " if m.group('weapon') else "Self: ")  # If weapon is equipped, add it
            + f"{element_map[m.group('element')]} damage "
            + ("taken " if m.group('type') == '受ける' else "")  # Add "taken" for "received" damage
            + (
                # Directly use the percentage (whether #PER#% or a numeric percentage)
                f"{m.group('sign') or ''}{m.group('percentage')}"
            )
        )
    ),   
    

    # Damage buffs, optional leading comma, optional duration, optional "付与" suffix
    (
        re.compile(
            r'^(?P<lead>、|,)?'
            r'(?P<target>必殺技で与えるダメージ|与えるすべてのダメージ|与える全てのダメージ|属性攻撃で与えるダメージ|単体攻撃|全体攻撃|必殺技|通常攻撃|無属性攻撃|属性攻撃)'
            r'\+#PER#%'
            r'(?:\((?P<duration>\d+T|\d+ターン)\))?'
            r'(付与)?'
        ),
        lambda m: (
            (", " if m.group('lead') else "")
            + f"{damage_type_map[m.group('target')]}: +#PER#%"
            + (f"({m.group('duration').replace('ターン', 'T')})" if m.group('duration') else "")
        )
    )

]