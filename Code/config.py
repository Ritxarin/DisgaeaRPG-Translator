from datetime import datetime
from enum import IntEnum
import json
import os
from pathlib import Path
from typing import List, Optional

class Device(IntEnum):
    DMM = 1
    Android = 2

class Config:

    DEEPL_API_KEY = "YOUR API KEY HERE"
    INITIAL_SETUP = "initial_setup_date"
    LAST_EXECUTION = "last_execution_date"
    TEXTURE_UPDATED_DATE = "texture_last_updated_date"
    CONFIG_PATH = 'config.json'
    DEVICE = ''

    @classmethod
    def set_device(cls, device:Device):
        if device == Device.DMM:
            cls.DEVICE = 'DMM'
        elif device == Device.Android:
            cls.DEVICE = 'Android'

    @classmethod
    def get_device(cls):
        if cls.DEVICE:
            return cls.DEVICE  # returns "DMM" or "Android"
        raise RuntimeError("Device not set. Call Config.set_device(Device.DMM or Device.Android) before running.")

    @classmethod
    def _load_config(cls):
        config_path = Path(cls.CONFIG_PATH)
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    @classmethod
    def _save_config(cls, config: dict):
        config_path = Path(cls.CONFIG_PATH)
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    @classmethod
    def get_datetime_field(cls, field_name: str) -> Optional[datetime]:
        """Get a datetime field from the config by name."""
        config = cls._load_config()
        # Append _Android or _DMM based on device
        if cls.DEVICE is None:
            raise RuntimeError("DEVICE not set. Use Config.set_device() first.")
        
        device_suffix = f"_{cls.DEVICE}"  # e.g., _Android
        full_field_name = field_name + device_suffix
        date_str = config.get(full_field_name)

        if date_str:
            try:
                # Parse ISO 8601 format
                return datetime.fromisoformat(date_str.rstrip("Z"))
            except ValueError:
                print(f"⚠️ Failed to parse datetime field '{field_name}': {date_str}")
        return None

    @classmethod
    def set_datetime_field(cls, field_name: str, dt: Optional[datetime] = None):
        """Set a datetime field in the config using local time."""
        config = cls._load_config()
        dt_str = (dt or datetime.now()).isoformat()  # Local time
        # Append _Android or _DMM based on device
        if cls.DEVICE is None:
            raise RuntimeError("DEVICE not set. Use Config.set_device() first.")        
        device_suffix = f"_{cls.DEVICE}"  # e.g., _Android
        full_field_name = field_name + device_suffix
        config[full_field_name] = dt_str
        cls._save_config(config)

    @classmethod
    def set_updated_files(cls, updated_files: List[str]):
        config = cls._load_config()
        config['updated_files'] = updated_files
        cls._save_config(config)

    @classmethod
    def get_updated_files(cls) -> List[str]:
        config = cls._load_config()
        return config.get('updated_files', [])
        
    FILES_TO_TRANSLATE =  [
        'achievement', 'agenda', 'area', 'arenacategory', 'beginnermission', 'boost',
        'charactermission', 'character', 'characterclassname', 'characterintroduction', 'charactersubinfo',
        'command', 'collaborationtext',
        'customdailymission', 'custommonthlymission', 'custompartskind', 'customtotalmission', 
        'drink', 'drinkskill', 
        'episode', 
        'equipment', 'equipmenteffecttype', 
        'eventmission', 'eventmissiondaily', 'eventmissionrepetition', 
        'garapon', 'garaponlot',
        'help', 'hospital', 
        'innocent', 'innocentrecipe',
        'item', 'iteminformation', 
        'kingdomrank', 'leaderskill', 'liqueur', 'loginbonus',
        'memory', 'memoryeffecttype', 'museum', 
        'potentialclass', 'potentialkind', 'product', 'ritualtrainings',
        'stage', 'stagemission', 'survey', 'tower', 
        'travelbenefit', 'travelnegativeeffect', 
        'trophy', 'trophydaily', 'trophydailyrequest', 'trophyrepetition', 'trophyweekly', 
        'weapon'
    ]

    FILES_TO_IGNORE = ['areareward', 'banner', 'campaign', 'campaignloginbonus', 
            'characterboost', 'charactermagiccommand', 'charactercommand', 'charactermaterial', 'characterretrofit',
            'divisionbattle', 'divisionbattlehpreducereward', 'divisionbattlerankingreward', 'divisionbattlereward',
            'divisionbattlerewardgroup', 'divisionbattlestage', 
            'enemy', 'enemygroupposition', 'enemyleaderskill', 
            'eventboostcharacter', 'eventterm',
            'gacha', 'gachabonus', 'gachabonuscategory', 'gachabonusgroup', 'gachabutton', 'gachagroup', 'gachagroupitem', 
            'gachalot', 'gachapickup', 'gachaspecificcountbonus', 'gachaspecificprice',
            'itemshop', 'mapeventbattlerankingreward', 'mapeventbattlereward', 'mapeventbattlerewardgroup',
            'memorystory',
            'product', 'productpresent', 'renewstoryeventboss', 'ritualtrainingmaterialdata', 'ritualtrainingstage',
            'stageenemygroup', 'story', 'storycharacter', 'storytalk', 'stopnotificationterm'
          ]

    FILES_TO_CHECK_FOR_UPDATES =  ['command', 'leaderskill']

    FILES_TO_TRACK_NEW_ENTRIES =  ['command', 'leaderskill', 'character', 'characterclassname', 'item', 'product', 'event']

    FIELDS_TO_TRANSLATE = [
        'ability_description', 'body', 'boost_description', 'boost_title', 'button_text', 'category', 'class_name', 'class_name_1',
        'class_name_2', 'class_name_3', 'class_name_4', 'class_name_5', 'condition_unit_name',
        'description', 'description_effect', 'description_format',
        'get_areas', 'item_name', 'm_text', 'name', 'name_battle', 'release_content_description',
        'resource_name', 'sheet_name', 'sub_name', 'text', 'title'
    ]

    FIELDS_TO_CHECK_FOR_UPDATES = [ 'description', 'description_effect' ]

class Paths:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    CONFIG_PATH = PROJECT_ROOT / "config.json"
    DICTIONARIES_DIR = PROJECT_ROOT / "Dictionaries"
    SOURCE_DIR = "./Source"
    GLOBAL_ASSETS_DIR = PROJECT_ROOT / "Global_Assets"
    SOURCE_TRANSLATED_DIR = PROJECT_ROOT / "Source_Translated"
    NEW_ENTRIES_DIR = "./New_Entries"
    TRANSLATED_FILES_DIR = "./Translated_Files"
    TRANSLATED_PREFABS_DIR = "./Translated_Prefabs"
    SOURCE_PREFABS_DIR = "./Source_Prefabs"
    UPDATED_FILES_DIR = "./Updated_Files"
    MASTERS_BACKUP = "./Masters_Backup"
    ASSETS_BACKUP = "./Assets_Backup"
    PATCHED_TEXTURES = "Patched_Textures"
    PATCHED_TEXTURES_Android = "./Android/Patched_Textures"
    GAME_ASSETS = os.path.join(
        os.getenv("LOCALAPPDATA").replace("Local", "LocalLow"),
        "disgaearpg",
        "DisgaeaRPG",
        "assetbundle"
    )

    GAME_ASSETS_DMM = os.path.join(
        os.getenv("LOCALAPPDATA").replace("Local", "LocalLow"),
        "disgaearpg",
        "DisgaeaRPG",
        "assetbundle"
    )

    GAME_MASTERS_DMM = os.path.join(
        os.getenv("LOCALAPPDATA").replace("Local", "LocalLow"),
        "disgaearpg",
        "DisgaeaRPG",
        "assetbundle",
        "masters"
    )

    GAME_MASTERS_Android = '/sdcard/Android/data/com.disgaearpg.forwardworks/files/assetbundle/masters'
    GAME_ASSETS_Android = '/sdcard/Android/data/com.disgaearpg.forwardworks/files/assetbundle/'
    GAME_MASTERS_Android_Local = './Android/master'
    GAME_ASSETS_Android_Local = './Android/Game_Assets'