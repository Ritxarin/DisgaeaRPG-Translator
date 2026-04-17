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
    GLOSSARY_HASH = "glossary_hash"
    GLOSSARY_ID = "glossary_id"
    GLOSSARY_NAME = "Disgaea_RPG_Glossary"
    TEXTURE_UPDATED_DATE = "texture_last_updated_date"
    CONFIG_PATH = 'config.json'
    DEVICE = ''
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    ADB_PATH = PROJECT_ROOT / "platform-tools" / "adb"

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
    
    @classmethod
    def get_string_field(cls, field_name: str) -> Optional[str]:
        """Get a string field from the config by name."""
        config = cls._load_config()

        if cls.DEVICE is None:
            raise RuntimeError("DEVICE not set. Use Config.set_device() first.")

        device_suffix = f"_{cls.DEVICE}"
        full_field_name = field_name + device_suffix

        value = config.get(full_field_name)
        return str(value) if value is not None else None


    @classmethod
    def set_string_field(cls, field_name: str, value: Optional[str]):
        """Set a string field in the config."""
        config = cls._load_config()

        if cls.DEVICE is None:
            raise RuntimeError("DEVICE not set. Use Config.set_device() first.")

        device_suffix = f"_{cls.DEVICE}"
        full_field_name = field_name + device_suffix

        if value is None:
            # Optional: remove the field if None is passed
            config.pop(full_field_name, None)
        else:
            config[full_field_name] = value

        cls._save_config(config)
        
    FILES_TO_TRANSLATE =  [
        'achievement', 'agenda', 'area', 'arenacategory', 'beginnermission', 'boost',
        'charactermission', 'character', 'characterclassname', 'characterintroduction', 'charactersubinfo', 
        'characterstory', 'characterstorytalk',
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
        'stage', 'stagemission', 'story', 'survey', 'tower', 
        'travelbenefit', 'travelnegativeeffect', 
        'trophy', 'trophydaily', 'trophydailyrequest', 'trophyrepetition', 'trophyweekly', 
        'weapon'
    ]

    FILES_TO_CHECK_FOR_UPDATES =  ['command', 'leaderskill']

    FIELDS_TO_CHECK_FOR_UPDATES = [ 'description', 'description_effect' ]

    FILES_TO_TRACK_NEW_ENTRIES =  ['character', 'characterclassname', 'command', 'event', 'item', 
                                   'leaderskill', 'product']

    FIELDS_TO_TRANSLATE = [
        'ability_description', 'body', 'boost_description', 'boost_title', 'button_text', 'category', 
        'chara1_name', 'chara2_name', 'chara3_name', 
        'class_name', 'class_name_1', 'class_name_2', 'class_name_3', 'class_name_4', 'class_name_5', 
        'condition_unit_name',
        'description', 'description_effect', 'description_format',
        'get_areas', 'item_name', 'm_text', 'name', 'name_battle', 'release_content_description',
        'resource_name', 'sheet_name', 'sub_name', 'talk_text', 'text', 'title', 
    ]

    CHARACTER_FILE = "character.json"

class Paths:
    CONFIG_PATH = Config.PROJECT_ROOT / "config.json"
    DICTIONARIES_DIR = Config.PROJECT_ROOT / "Dictionaries"
    CHARACTER_DICTIONARIES_DIR = Config.PROJECT_ROOT / "Dictionaries_Character"
    PATTERN_DICTIONARIES_DIR = Config.PROJECT_ROOT / "Dictionaries_Pattern"
    GLOBAL_ASSETS_DIR = Config.PROJECT_ROOT / "Global_Assets"
    SOURCE_TRANSLATED_DIR = Config.PROJECT_ROOT / "Source_Translated"
    DEEPL_DIR = Config.PROJECT_ROOT / "DeepL"
    SOURCE_DIR = "Source"
    NEW_ENTRIES_DIR = "New_Entries"
    TRANSLATED_FILES_DIR = "Translated_Files"
    TRANSLATED_PREFABS_DIR = "Translated_Prefabs"
    SOURCE_PREFABS_DIR = "Source_Prefabs"
    UPDATED_FILES_DIR = "Updated_Files"
    MASTERS_BACKUP = "Masters_Backup"
    ASSETS_BACKUP = "Assets_Backup"
    PATCHED_TEXTURES = "Patched_Textures"
    PATCHED_TEXTURES_Android = Config.PROJECT_ROOT / "Android/Patched_Textures"
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
    GAME_MASTERS_Android_Local = Config.PROJECT_ROOT / 'Android/master'
    GAME_ASSETS_Android_Local = Config.PROJECT_ROOT / 'Android/Game_Assets'