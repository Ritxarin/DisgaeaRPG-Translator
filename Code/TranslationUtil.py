from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any, List
from Code.Helper import Helper
from Code.UnityHelper import UnityHelper
from Code.config import Config, Paths
from Code.Translator import Translator

class Translator_Util:
    
    def __init__(self):
        self.translator = Translator()
        self.helper = Helper()
        self.device = Config.get_device()
        if self.device == 'DMM':
            self.masters_path = Path(Paths.GAME_MASTERS_DMM)
            self.game_assets_path = Path(Paths.GAME_ASSETS_DMM) 
        elif self.device == 'Android':
            self.masters_path = Path(Paths.GAME_MASTERS_Android_Local)    
            self.game_assets_path = Path(Paths.GAME_ASSETS_Android_Local)   
        self.source_path = Path(self.device) / Path(Paths.SOURCE_DIR)        
        self.source_path.mkdir(parents=True, exist_ok=True)
        self.updated_files_path = Path(self.device) / Path(Paths.UPDATED_FILES_DIR)        
        self.updated_files_path.mkdir(parents=True, exist_ok=True)
        self.new_entries_path = Path(self.device) / Path(Paths.NEW_ENTRIES_DIR)        
        self.new_entries_path.mkdir(parents=True, exist_ok=True)
        self.translated_files_path = Path(self.device) / Path(Paths.TRANSLATED_FILES_DIR)        
        self.translated_files_path.mkdir(parents=True, exist_ok=True)
        self.masters_backup_path = Path(self.device) / Path(Paths.MASTERS_BACKUP)        
        self.masters_backup_path.mkdir(parents=True, exist_ok=True)

    def __translate_file(self, filename:str, path:str):
        print(f"       ├─ 🔁 Translating file {filename}.")
        start_time = time.time()
        source_path = os.path.join(path, f'{filename}')
        out_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, f'{filename}')
        temp_path = out_path + '.tmp'
        
        name_only = os.path.splitext(filename)[0]
        new_entries_path = os.path.join(self.new_entries_path, f"{name_only}_new_entries.json")

        # Load JP source (list of entries)
        with open(source_path, 'r', encoding='utf8') as f:
            jp_data = json.load(f)

        # Load existing translated data if any (resume support)
        translated_data = []
        if os.path.exists(out_path):
            try:
                with open(out_path, 'r', encoding='utf8') as f:
                    translated_data = json.load(f)
            except json.JSONDecodeError:
                print("            ├─ ⚠️ Couldn't decode existing output file. Starting from scratch.")

        # Track already translated IDs to skip
        translated_ids = {entry["id"] for entry in translated_data}

        count = 0
        new_count = 0
        new_entries = []
        for entry in jp_data:
            count += 1
            if entry["id"] in translated_ids:
                continue

            merged = entry.copy()
            for key in Config.FIELDS_TO_TRANSLATE:
                if key in merged and merged[key] != '':
                    translated = self.translator.translate(name_only, key, merged[key])
                    merged[key] = translated

            translated_data.append(merged)
            new_entries.append(merged) #track additions
            new_count += 1

            # Periodic save every 100 entries
            if count % 200 == 0:
                try:
                    with open(temp_path, 'w', encoding='utf8') as f:
                        json.dump(translated_data, f, ensure_ascii=False, indent=2)
                    shutil.move(temp_path, out_path)
                except Exception as e:
                    print(f"            ├─ ❌ Error writing progress: {e}")
                    if os.path.exists(temp_path):
                        print(f"            ├─ ⚠️ Temp file preserved at: {temp_path}")

        # Final save
        with open(out_path, 'w', encoding='utf8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)

        # Save just the new entries to a separate file
        if new_entries and name_only in Config.FILES_TO_TRACK_NEW_ENTRIES:
            with open(new_entries_path, 'w', encoding='utf8') as f:
                json.dump(new_entries, f, ensure_ascii=False, indent=2)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"            ├─ 📝 Finished translating file {filename}: {len(translated_data)} total entries written to {out_path} in {elapsed:.2f}s")
        if new_count > 0:
            print(f"                ├─ 🛠️ Added {new_count} new lines to the file")

    def __translate_file_changes(self, source_data:dict[Any, Any], updated_data:dict[Any, Any], filename):
        print(f"       ├─ 🔁 Checking {filename} for updates.")
        start_time = time.time()

        # Load existing translated data
        out_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, f'{filename}.json')  
        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf8') as f:
                translated_data = json.load(f)
                # Create a lookup dictionary by 'id' (so you can easily access by 'id')
                translated_data_lookup = {entry["id"]: entry for entry in translated_data}
        else:
            translated_data = []
        
        updated_count = 0
        updated_character_ids = []

        for id_, old_entry in source_data.items():
            if id_ not in updated_data:
                continue  # Entry was removed in JP (unlikely, but safe check)

            new_entry = updated_data[id_]
            #translated_entry = translated_data.get(id_, new_entry.copy())
            translated_entry = translated_data_lookup[id_]

            entry_updated = False
            for field in Config.FIELDS_TO_CHECK_FOR_UPDATES:
                if field in new_entry:
                    old_value = old_entry.get(field)
                    new_value = new_entry.get(field)

                    if old_value != new_value:

                        if filename == "leaderskill":
                            char = self.helper.find_character_by_leaderskill_id(new_entry['id'])
                            if char is not None:
                                if char['id'] not in updated_character_ids:
                                    updated_character_ids.append(char['id'])
                            char_name = 'N/A' if char is None else char['name']
                            print(f"            ├─ ℹ️  Updating Evility {translated_entry['name']} with ID: {id_} for Character: {char_name}")

                        elif filename == "command":
                            char = self.helper.find_character_by_command_id(new_entry['id'])
                            if char is not None:
                                if char['id'] not in updated_character_ids:
                                    updated_character_ids.append(char['id'])
                            char_name = 'N/A' if char is None else char['name']
                            print(f"            ├─ ℹ️  Updating Skill {translated_entry['name']} with ID: {id_} for Character: {char_name}")                     

                        print(f"                ├─ Old Value: {translated_entry[field]}")
                        translated_text = self.translator.translate(filename=filename, field=field, value=new_value)
                        if translated_text:
                            translated_entry[field] = translated_text
                            print(f"                ├─ New Value: {translated_text}")
                            updated_count += 1
                            entry_updated = True
                        else:
                            print(f"⚠️ No translation for ID {id_} field '{field}': {new_value}")    
                        
            # Update the entry directly in the translated_data dictionary
            #if entry_updated:                
            #    translated_data[id_] = translated_entry  # Replace the old entry with the updated one

            #updated_translated_data.append(translated_entry)

        # Save updated translation file
        out_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, f'{filename}.json')
        # with open(out_path, 'w', encoding='utf8') as f:
        #     json.dump(translated_data, f, ensure_ascii=False, indent=2)
        self.helper.safe_save_json(translated_data, out_path)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"            ├─ 🛠️ Finished checking {filename}: {updated_count} entries updated in {elapsed:.2f}s")
 
    def __patch_new_entries(self, new_entries_file, source_file, filename):
        source_data_lookup = {entry["id"]: entry for entry in source_file}
        new_entries_lookup = {entry["id"]: entry for entry in new_entries_file}
        for id_, new_entry in new_entries_lookup.items():
            if id_ not in source_data_lookup:
                continue  # Entry was removed in JP (unlikely, but safe check)

            #translated_entry = translated_data.get(id_, new_entry.copy())
            source_entry = source_data_lookup[id_]
            entry_updated = False
            for field in Config.FIELDS_TO_TRANSLATE:
                if field in source_entry:
                    old_value = source_entry.get(field)
                    new_value = new_entry.get(field)

                    if old_value != new_value:
                        source_entry[field] = new_value  # ✅ update the source entry
                        entry_updated = True
                          
                        
            # Update the entry directly in the translated_data dictionary
            if entry_updated:                
               source_data_lookup[id_] = source_entry  # Replace the old entry with the updated one


        # Save updated translation file
        patched_source = list(source_data_lookup.values())
        out_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, f'{filename}.json')
        # with open(out_path, 'w', encoding='utf8') as f:
        #     json.dump(translated_data, f, ensure_ascii=False, indent=2)
        self.helper.safe_save_json(patched_source, out_path)
    
    # in case the initial files are not up to date. Look for new entries, translate and update our translations
    def initial_translation(self):
        print(f"\n    ℹ️ Running initial translation")
        start_time = time.time()
        for filename in os.listdir(self.updated_files_path):
            file_path = os.path.join(self.updated_files_path, filename)
            # Skip subfolders
            if not os.path.isfile(file_path):
                continue
            self.__translate_file(filename=filename, path=self.updated_files_path)

            ## Keep leaderkill and command files to check for buffs
            ## They will become the new source to compare against on future updates
            ## Keep character command as well
            if Path(filename).stem not in Config.FILES_TO_CHECK_FOR_UPDATES and Path(filename).stem != 'charactercommand':
                os.remove(file_path)  # delete the file if not in KEEP_FILES

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Completed initial translation in {elapsed:.2f}s.")

    # Look for files changed after last execution
    def find_updated_files(self):     
        # Get last run time so we can look for updated files
        last_execution_timestamp = Config.get_datetime_field(Config.LAST_EXECUTION)
        if last_execution_timestamp is None:
            last_execution_timestamp = Config.get_datetime_field(Config.INITIAL_SETUP)
        initial_setup_timestamp = Config.get_datetime_field(Config.INITIAL_SETUP)

        print(f'\n    ℹ️  Looking for files updated after {last_execution_timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
        start_time = time.time()

        #Reset config
        updated_files = []
        Config.set_updated_files(updated_files)

        # Delete backups before generating new files
        backup_dir = Path(self.masters_backup_path)
        for file in backup_dir.iterdir():
            if file.is_file():
                file.unlink()

        source_dir = Path(self.new_entries_path)
        for file in source_dir.iterdir():
            if file.is_file():
                file.unlink()

        # For android, pull updated files from phone
        if self.device == 'Android':
            source_dir = Path(self.masters_path)
            for file in source_dir.iterdir():
                if file.is_file():
                    file.unlink()
            self.helper.pull_updated_files_from_mobile(Paths.GAME_MASTERS_Android, Paths.GAME_MASTERS_Android_Local, last_execution_timestamp, initial_setup_timestamp)

            for file in Path(Paths.GAME_MASTERS_Android_Local).iterdir():
                if file.is_file():
                    updated_files.append(file.name)

        # 🔁 For DMM iterate game folder
        if self.device == 'DMM':
            for filename in os.listdir(self.masters_path):
                file_path = os.path.join(self.masters_path, filename)

                # Skip subfolders
                if not os.path.isfile(file_path):
                    continue

                # Get last modified time
                mtime = os.path.getmtime(file_path)
                modified_date = datetime.fromtimestamp(mtime)

                # Compare with cutoff date. Get if modified more recently OR before initial setup (means this is a file that's now bein)
                if modified_date > last_execution_timestamp or modified_date < initial_setup_timestamp:
                    updated_files.append(filename)

        # 🖨️ Print or use the list
        print("            ├─  🔁 Files updated since last execution:")
        for f in updated_files:
            print(f"                 ├─  📦 {f}")

        unity_helper = UnityHelper()
        unity_helper.datamine_files(updated_files)   
        Config.set_updated_files(updated_files)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished looking for updated files in {elapsed:.2f}s.")   

    # translate updated files
    def translate_updated_files(self):

        print(f"\n    ℹ️  Translating updated files")
        start_time = time.time()
        updated_files = Config.get_updated_files()

        for filename in os.listdir(self.updated_files_path):
            file_path = os.path.join(self.updated_files_path, filename)
            name_only = os.path.splitext(filename)[0]

            # Skip subfolders
            if not os.path.isfile(file_path):
                continue

            if name_only in Config.FILES_TO_TRANSLATE and name_only in updated_files:
                self.__translate_file(filename, path=self.updated_files_path)

                if name_only not in Config.FILES_TO_CHECK_FOR_UPDATES:
                    os.remove(file_path)   

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished translating updated files in {elapsed:.2f}s.")  

    # translate updated files
    def translate_files(self, filenames):
        for filename in filenames:
            self.__translate_file(filename=filename, path=self.updated_files_path)

    # patch updated files
    def patch_new_entries(self, filenames:List[str]):

        print(f"ℹ️  Patching new entries into source file")
        start_time = time.time()

        for filename in filenames:
            print(f"    🔁  Processing file : {filename}")
            # Add the suffix to target the new entries file
            new_entries_filename = f"{filename}_new_entries.json"
            new_entries_file_path = os.path.join(self.new_entries_path, new_entries_filename)
            source_filename = f"{filename}.json"
            source_file_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, source_filename)            

            if not os.path.isfile(new_entries_file_path):
                print(f"    ⚠️  File not found: {new_entries_file_path}")
                continue

            # Load the JSON file
            with open(new_entries_file_path, "r", encoding="utf-8") as f:
                new_entries_file = json.load(f)
            with open(source_file_path, "r", encoding="utf-8") as f:
                source_file = json.load(f)

            self.__patch_new_entries(new_entries_file, source_file, filename)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"├─ ✅ Finished translating updated files in {elapsed:.2f}s.")  

    def find_and_translate_file_changes(self):

        print(f"\n    ℹ️  Looking for character updates")
        start_time = time.time()

        for updated_file in os.listdir(self.updated_files_path):
            updated_file_path = os.path.join(self.updated_files_path, updated_file)
            updated_file_name = os.path.splitext(updated_file)[0]

            original_file_path = os.path.join(self.source_path, updated_file)

            # Skip subfolders
            if not os.path.isfile(original_file_path):
                continue

            if updated_file_name in Config.FILES_TO_CHECK_FOR_UPDATES:

                # Load updated data
                with open(updated_file_path, 'r', encoding='utf8') as f:
                    updated_data = {entry["id"]: entry for entry in json.load(f)}

                # Load source data
                with open(original_file_path, 'r', encoding='utf8') as f:
                    source_data = {entry["id"]: entry for entry in json.load(f)}

                self.__translate_file_changes(source_data=source_data, updated_data=updated_data, filename=updated_file_name)

            # Move files to source for the next update
            destination_folder = self.source_path
            os.makedirs(destination_folder, exist_ok=True)
            destination_path = os.path.join(destination_folder, f'{updated_file_name}.json')
            # Move the file
            shutil.move(updated_file_path, destination_path)

        end_time = time.time()
        elapsed = end_time - start_time
        print(f"       ├─ ✅ Finished looking for character updates in {elapsed:.2f}s.")  

    def __update_game_files_dmm(self, files_to_update:List[str] = None):
        source_dir = Path(self.translated_files_path)
        target_dir = Path(Paths.GAME_MASTERS_DMM)

        # Ensure the destination exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files (ignoring subdirectories)
        for file in source_dir.iterdir():
            if file.is_file():
                if files_to_update is None or file.stem in files_to_update:
                    target_file = target_dir / file.name
                    shutil.copy2(file, target_file)
                    print(f"       ├─ 🔁 Copied {file.name} to {target_file}")

    def __update_game_files_android(self, files_to_update:List[str] = None):
        source_dir = Path(self.translated_files_path)
        target_dir = Paths.GAME_MASTERS_Android
    
        # Ensure files_to_update is provided or use all files in Translated_Files
        if files_to_update is None:
            files_to_update = [file.name for file in source_dir.iterdir() if file.is_file()]
        
        for filename in files_to_update:
            file_path = source_dir / filename
            
            if file_path.exists() and file_path.is_file():
                # Push each file to the target location on the device
                result = subprocess.run([
                    "./platform-tools//adb.exe", "push", str(file_path), f"{target_dir}/{filename}"
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"Files pushed successfully: {filename}")
                else:
                    print(f"Error pushing {filename}:", result.stderr)
            else:
                print(f"File not found: {file_path}")
        print("   ├─ ✅ Finished pushing translated files.")

    def update_game_files(self, files_to_update:List[str] = None):
        print(f"\n    ℹ️ Updating game files")

        if self.device == "DMM":
            self.__update_game_files_dmm(files_to_update)
        elif self.device == "Android":
            self.__update_game_files_android(files_to_update)
            
        print("   ├─ ✅ Finished updating game files.")

    def update_game_textures(self, files_to_update:List[str] = None):
        print(f"\n    ℹ️ Updating game assets")

        if self.device == "DMM":
            self.__update_game_textures_dmm(files_to_update)
        elif self.device == "Android":
            Helper.push_patched_textures_to_android(files_to_update)
            
        print("   ├─ ✅ Finished updating game files.")

    def __update_game_textures_dmm(self, files_to_update:List[str] = None):   

        source_dir = Path(Paths.PATCHED_TEXTURES)
        target_dir = Path(Paths.GAME_ASSETS_DMM)

        # Ensure the destination exists
        target_dir.mkdir(parents=True, exist_ok=True)

        updated_count = 0

        for patch_file in source_dir.rglob("*"):
            if patch_file.is_file():
                relative_path = patch_file.relative_to(source_dir)
                target_game_file = Path(Paths.GAME_ASSETS_DMM) / relative_path

                # If filtering is enabled, check filename match
                if files_to_update is not None:
                    if patch_file.name not in files_to_update:
                        continue

                if not target_game_file.exists():
                    print(f"           ├─ ⚠️ Game file not found: {relative_path}")
                    continue

                target_file = target_dir / patch_file.name
                # Copy the patched file to game directory
                shutil.copy2(patch_file, target_game_file)
                print(f"           ├─ 📁 Copied: {relative_path} to {target_file}")
                updated_count += 1

        print(f"       ├─ ✅ Finished updating {updated_count} texture(s).")