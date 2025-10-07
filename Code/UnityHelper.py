from datetime import datetime
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
from typing import List
import UnityPy
from Code.Helper import Helper
from Code.Translator import Translator
from Code.config import Config, Paths
from io import BytesIO

class UnityHelper:
    def __init__(self):            
        
        self.device = Config.get_device()
        self.helper = Helper()

        self.__load_env(self.device)
        #Ensure required folders exist

        self.backup_path = Config.PROJECT_ROOT / self.device / Paths.MASTERS_BACKUP       
        self.backup_path.mkdir(parents=True, exist_ok=True)

        self.assets_backup_path = Config.PROJECT_ROOT / self.device / Paths.ASSETS_BACKUP
        self.assets_backup_path.mkdir(parents=True, exist_ok=True)

        self.patched_textures =  Config.PROJECT_ROOT / self.device / Paths.PATCHED_TEXTURES        
        self.patched_textures.mkdir(parents=True, exist_ok=True)        

        self.global_assets_path = Config.PROJECT_ROOT / Paths.GLOBAL_ASSETS_DIR    
        self.global_assets_path.mkdir(parents=True, exist_ok=True)

        self.translation_source_path = Config.PROJECT_ROOT / Paths.SOURCE_TRANSLATED_DIR     
        self.translation_source_path.mkdir(parents=True, exist_ok=True)

        self.source_path = Config.PROJECT_ROOT / self.device / Paths.SOURCE_DIR     
        self.source_path.mkdir(parents=True, exist_ok=True)

        self.updated_files_path = Config.PROJECT_ROOT / self.device / Paths.UPDATED_FILES_DIR          
        self.updated_files_path.mkdir(parents=True, exist_ok=True)
        
        self.translated_files_path = Config.PROJECT_ROOT / self.device / Paths.TRANSLATED_FILES_DIR      
        self.translated_files_path.mkdir(parents=True, exist_ok=True)

        # self.source_prefab_path = Config.PROJECT_ROOT / self.device / Paths.SOURCE_PREFABS_DIR        
        # self.source_prefab_path.mkdir(parents=True, exist_ok=True)
        # self.translated_prefab_path = Config.PROJECT_ROOT / self.device / Paths.TRANSLATED_PREFABS_DIR     
        # self.translated_prefab_path.mkdir(parents=True, exist_ok=True)
 
        self.new_entries_path = Config.PROJECT_ROOT / self.device / Paths.NEW_ENTRIES_DIR 
        self.new_entries_path.mkdir(parents=True, exist_ok=True)

        self.translator = Translator()

    # Initial datamine. Returns True if the initial setup was already done. False otherwise
    def initial_datamine(self) -> bool:
        """Extract only the missing JSON files from FILES_TO_TRANSLATE."""

        print(f"\n    ℹ️ Running initial setup")
        start_time = time.time()

        if Config.get_datetime_field(Config.INITIAL_SETUP):
            print("       ├─ ✅ Initial setup already completed.")
            return True

        print("       ├─ 🔁 Datamining game files...")
        for obj in self.env.objects:
            if obj.type.name != "MonoBehaviour":
                continue

            if not obj.serialized_type.nodes:
                continue

            data = obj.read()
            name = data.m_Name

            if name not in Config.FILES_TO_TRANSLATE and name != 'charactercommand':
                continue

            self._export_json(obj, name, self.updated_files_path)

            source_file = self.masters_path / name
            backup_file = self.backup_path / name
            # Make sure the backup directory exists
            backup_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy only if it hasn't already been backed up
            if not backup_file.exists():
                try:
                    shutil.copy2(source_file, backup_file)
                    print(f"            ├─ 🔒 Backed up Unity asset to: {backup_file}")
                except Exception as e:
                    print(f"            ├─ ❌ Failed to back up {source_file}: {e}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Completed initial setup in {elapsed:.2f}s.")
        return False

    # Datamine files specified on a list
    def datamine_files(self, files_to_datamine:list[str]) -> None:
        for obj in self.env.objects:
            if obj.type.name != "MonoBehaviour":
                continue

            if not obj.serialized_type.nodes:
                continue

            data = obj.read()
            name = data.m_Name

            # Datamine updated files and export to updated files folder
            if name in files_to_datamine and (name in Config.FILES_TO_TRANSLATE or name == 'charactercommand' or name == 'event'):
                self._export_json(obj, name, self.updated_files_path)
                source_file = self.masters_path / name
                backup_file = self.backup_path / name
                # Make sure the backup directory exists
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                # Backup file (overwrite if if existed)
                shutil.copy2(source_file, backup_file)
                print(f"                 ├─  🔒 Backed up Unity asset to: {backup_file}")
  
    # Generate translated game files and place them in the Translated_Files folder
    def generate_translated_game_files(self, files_to_translate:List[str] = None) -> None:
        
        print(f"\n    ℹ️ Generating translated game files")
        start_time = time.time()

        # Delete before generating new files
        source_dir = Path(self.translated_files_path)
        for file in source_dir.iterdir():
            if file.is_file():
                file.unlink()

        for obj in self.env.objects:
            if obj.type.name == "MonoBehaviour":
                filename = ''
                if obj.serialized_type.nodes:            
                    data = obj.read()
                    filename = data.m_Name
                    # If translating only updated files check if the file needs to be translated:
                    if files_to_translate is not None and filename not in files_to_translate: 
                        continue
                    # Check if the file is in the lit of files to translate
                    if filename not in Config.FILES_TO_TRANSLATE: 
                        continue
                    tree = obj.read_typetree()

                    updated = False
                    translated_data = self.__load_translated_data(filename)
                    translated_index = {entry["id"]: entry for entry in translated_data}

                    for item in tree['DataList']:
                        tid = item.get("id")
                        en_data = translated_index.get(tid)
                        if en_data is not None:
                            for key in Config.FIELDS_TO_TRANSLATE:
                                if key in en_data:
                                    item[key] = en_data[key]
                                    updated = True
                if updated:
                    obj.save_typetree(tree)
                    print(f"            ├─ 📦 Generated file: {filename}")

        for path, env_file in self.env.files.items():
            output_path = os.path.join(self.translated_files_path, os.path.basename(path))
            filename = path[path.rfind('/') + 1:]
            if files_to_translate is not None and filename not in files_to_translate: 
                continue
            if filename in Config.FILES_TO_TRANSLATE:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(env_file.save(packer=(64,2)))
        
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished generating translated game files in {elapsed:.2f}s.")
 
    # Generate translated game files and place them in the Translated_Files folder
    def generate_translated_prefabs(self, files_to_translate:List[str] = None) -> None:
        
        print(f"\n    ℹ️ Generating translated game files")
        start_time = time.time()

        # Delete before generating new files
        source_dir = Path(self.translated_files_path)
        for file in source_dir.iterdir():
            if file.is_file():
                file.unlink()
        
        prefab_env = UnityPy.load(self.source_prefab_path.as_posix())

        for obj in prefab_env.objects:
            if obj.type.name == "MonoBehaviour":
                filename = ''
                if obj.serialized_type.nodes:            
                    data = obj.read()
                    tree = obj.read_typetree()
                    if 'm_text' not in tree:
                        continue
                    tree['m_text'] = self.translator.translate("command", "m_text", tree["m_text"])
                    obj.save_typetree(tree)

        for path, env_file in prefab_env.files.items():
            output_path = os.path.join(self.translated_prefab_path, os.path.basename(path))
            filename = path[path.rfind('/') + 1:]

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(env_file.save(packer=(64,2)))
        
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished generating translated game files in {elapsed:.2f}s.")

    def find_and_patch_textures(self, force=False):

        start_time = time.time()

        texture_update_timestamp = Config.get_datetime_field(Config.TEXTURE_UPDATED_DATE)
        if texture_update_timestamp is None:
            texture_update_timestamp = datetime.min
        remote_files = {}

        # Pull assets from android device first
        if self.device == 'Android':
            print(f"           ├─  ⬇️ Pulling assets from Android...")
            # Only pull files from Android that exist in self.global_assets_path
            # Temporarily store them in assets android local folder
            remote_path = Paths.GAME_ASSETS_Android
            # Retrieve timestamps from Android device
            remote_files = self.helper.get_android_file_timestamps(remote_path)
            
            for asset_file in self.global_assets_path.rglob("*"):
                if asset_file.is_file():
                    relative_path = asset_file.relative_to(self.global_assets_path)
                    remote_file = f"{remote_path}/{relative_path}"
                    remote_file = Path(remote_file).as_posix()
                    
                    if os.path.exists(asset_file):  # Check if the file exists in local working dir
                        if Helper.check_file_exists_on_device(remote_file):
                            # Local output path (where we actually pull the file to)
                            local_pull_target = Paths.GAME_ASSETS_Android_Local / relative_path
                            # Make sure the directory exists
                            local_pull_target.parent.mkdir(parents=True, exist_ok=True)
                            Helper.pull_file_from_mobile(remote_file, local_pull_target)

            print(f"           ├─  ✅ Finished pulling assets from Android...")
            
        # Iterate global assets and use them to patch game assets
        print(f"\n    🔍 Scanning for assets to patch...")
        for asset_file in self.global_assets_path.rglob("*"):
            if asset_file.is_file():
                # Reconstruct relative path from assets dir
                relative_path = asset_file.relative_to(self.global_assets_path)

                # Build corresponding path in game masters
                game_asset_file = self.game_assets_path / relative_path
                backup_file = self.assets_backup_path / relative_path

                # Build expected path for patched output
                patched_output_file = Path(self.patched_textures_path) / relative_path
                
                # # Patched texture file already exists. Skip to next asset
                # if patched_output_file.exists():
                #     continue 

                if game_asset_file.exists() and not force:
                    print(f"           ├─  🖼️ Found texture to patch: {relative_path}")

                    # Check if texture needs updating based on the modified timestamp
                    does_file_need_updating = False
                    if not patched_output_file.exists():
                            does_file_need_updating = True
                    else:
                        #patch_updated_time = os.path.getmtime(patched_output_file)
                        #patch_updated_time = datetime.fromtimestamp(patch_updated_time)
                        if self.device == 'Android':
                            game_asset_time = remote_files[game_asset_file.stem]
                            does_file_need_updating = game_asset_time > texture_update_timestamp                        
                        elif  self.device == 'DMM':                            
                            game_asset_time = os.path.getmtime(game_asset_file)
                            game_asset_time = datetime.fromtimestamp(game_asset_time)
                            does_file_need_updating = game_asset_time > texture_update_timestamp                             

                    if not does_file_need_updating:
                        print(f"            ├─  ℹ️  Texture is already up to date.")
                        continue

                    # Make sure backup folder exists for the file
                    backup_file.parent.mkdir(parents=True, exist_ok=True)

                    # Backup existing game file (only if not already backed up)
                    if not backup_file.exists():
                        shutil.copy2(game_asset_file, backup_file)
                    print(f"                ├─ 🔒 Backed up asset to {relative_path}")

                    # Load both Unity environments
                    with asset_file.open("rb") as f:
                        source_env = UnityPy.load(f)
                    with game_asset_file.open("rb") as f:
                        target_env = UnityPy.load(f)

                    # Example: Patch textures
                    self.__patch_textures(source_env, target_env, asset_file.name, relative_path)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished patching textures in in {elapsed:.2f}s.")

    def __load_translated_data(self, filename:str):  
        filepath = os.path.join(Paths.SOURCE_TRANSLATED_DIR, filename + '.json')  
        with io.open(filepath, encoding='utf8') as fj:
            translated_source_data=json.load(fj)
            return translated_source_data
    
    def _export_json(self, obj, name: str, path=None) -> None:
        """Internal helper to write JSON to output folder."""

        if path is None:
            path = self.source_path

        if not isinstance(path, Path):
            path = Path(path)

        tree = obj.read_typetree()
        output_path = path / f"{name}.json"

        with open(output_path, "wt", encoding="utf8") as f:
            json.dump(tree['DataList'], f, ensure_ascii=False, indent=4)

        print(f"            ├─ 📝 Extracted: {name}")

    def __patch_textures(self, source_env, target_env, filename, relative_path):

        # Map sprites by name from both environments
        sprites_jp = {}
        sprites_en = {}
        patched = 0
        skipped = []
        mismatches = []

        # Map sprites by name
        sprites_jp = {s.m_Name: s for obj in target_env.objects if obj.type.name == "Sprite" for s in [obj.read()]}
        sprites_en = {s.m_Name: s for obj in source_env.objects if obj.type.name == "Sprite" for s in [obj.read()]}

        # Load textures
        jp_texture = next((obj.read() for obj in target_env.objects if obj.type.name == "Texture2D"), None)
        en_texture = next((obj.read() for obj in source_env.objects if obj.type.name == "Texture2D"), None)

        # Pre-convert once
        jp_img = jp_texture.image.convert("RGBA")
        en_img = en_texture.image.convert("RGBA")

        for name, jp_sprite in sprites_jp.items():
            en_sprite = sprites_en.get(name)
            if not en_sprite:
                skipped.append(name)
                continue

            rect_jp = jp_sprite.m_RD.textureRect
            rect_en = en_sprite.m_RD.textureRect

            if (int(rect_en.width) != int(rect_jp.width)) or (int(rect_en.height) != int(rect_jp.height)):
                # If sizes don't match, resize the EN texture to match the JP sprite size
                crop = en_img.crop((
                    int(rect_en.x),
                    en_img.height - int(rect_en.y + rect_en.height),
                    int(rect_en.x + rect_en.width),
                    en_img.height - int(rect_en.y)
                ))

                # Resize crop to match JP size (if mismatched)
                crop_resized = crop.resize((int(rect_jp.width), int(rect_jp.height)))

                # Paste resized crop into JP texture
                paste_x = int(rect_jp.x)
                paste_y = jp_img.height - int(rect_jp.y + rect_jp.height)
                jp_img.paste(crop_resized, (paste_x, paste_y))
                patched += 1
            else:
                # If sizes match, just crop and paste without resizing
                crop = en_img.crop((
                    int(rect_en.x),
                    en_img.height - int(rect_en.y + rect_en.height),
                    int(rect_en.x + rect_en.width),
                    en_img.height - int(rect_en.y)
                ))

                paste_x = int(rect_jp.x)
                paste_y = jp_img.height - int(rect_jp.y + rect_jp.height)
                jp_img.paste(crop, (paste_x, paste_y))
                patched += 1

        # Final save
        #jp_texture.image = jp_img
        buffer = BytesIO()
        jp_img.save(buffer, format="PNG")
        buffer.seek(0)
        # Just pass the PNG bytes directly — no keyword arguments
        jp_texture.set_image(buffer)
        jp_texture.save()

        print(f"                ├─ 💾 Patched {patched} sprite(s)")
        if mismatches:
            print(f"                ├─ ❌ Mismatches: {len(mismatches)} → {mismatches}")

        # Step 3: Save the whole environment (updated bundle)
        output_dir = self.patched_textures_path

        for path, env_file in target_env.files.items():
            save_path = output_dir / relative_path
            # Ensure parent directory exists
            save_path.parent.mkdir(parents=True, exist_ok=True)
            # Save the modified Unity asset file
            with open(save_path, "wb") as f:
                f.write(env_file.save(packer=(64, 2)))

    def __load_env(self, device:str):
        if device == 'DMM':
            self.masters_path = Path(Paths.GAME_MASTERS_DMM)
            self.env = UnityPy.load(Paths.GAME_MASTERS_DMM)
            self.game_assets_path = Path(Paths.GAME_ASSETS_DMM) 
        elif device == 'Android':
            Helper.pull_masters_from_mobile()
            self.masters_path = Paths.GAME_MASTERS_Android_Local
            self.env = UnityPy.load(str(Paths.GAME_MASTERS_Android_Local))
            self.game_assets_path = Path(Paths.GAME_ASSETS_Android_Local) 
            
        self.patched_textures_path = Config.PROJECT_ROOT / self.device / Paths.PATCHED_TEXTURES
                   
        # Check if the folder exists and is not empty
        if not self.masters_path.is_dir():
            print(f" ❌ Error: The folder '{self.masters_path}' does not exist.")
            sys.exit(1)

        if not any(self.masters_path.iterdir()):
            print(f" ❌ Error: The folder '{self.masters_path}' is empty.")
            sys.exit(1)