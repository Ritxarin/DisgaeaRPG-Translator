from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from Code.config import Config, Device, Paths

class Helper:
    def __init__(self):
        character_file_path = os.path.join(Paths.SOURCE_TRANSLATED_DIR, 'character.json')
        with open(character_file_path, 'r', encoding='utf8') as f:
            self.character_data = json.load(f)
        # Build lookup dict: id -> character data
        self.char_lookup = {char['id']: char for char in self.character_data}

        charactercommand_file_path = os.path.join(Paths.UPDATED_FILES_DIR, 'charactercommand.json')
        with open(charactercommand_file_path, 'r', encoding='utf8') as f:
            self.character_command_data = json.load(f)
        # Build lookup dict: m_command_id -> m_character_id
        self.character_command_lookup = {entry['m_command_id']: entry['m_character_id'] for entry in self.character_command_data}

    def find_character_by_leaderskill_id(self, leaderskill_id:int):
        for char in self.character_data:
            if leaderskill_id in (
                char.get("m_leader_skill_id"),
                char.get("additional_m_leader_skill_id"),
                char.get("m_leader_skill_id_sub_1"),
                char.get("additional_m_leader_skill_id_sub_1"),
                char.get("m_leader_skill_id_sub_2"),
                char.get("additional_m_leader_skill_id_sub_2"),
                char.get("m_leader_skill_id_sub_3"),
                char.get("additional_m_leader_skill_id_sub_3")
            ):
                return char
    
        return None
    
    def find_character_by_command_id(self, command_id:int):
        character_id = self.character_command_lookup.get(command_id)
        if character_id is None:
            return None
        return self.char_lookup.get(character_id)

    def safe_save_json(self, data, final_path):
        # Create a temporary file in the same directory
        dir_name = os.path.dirname(final_path)
        with tempfile.NamedTemporaryFile('w', encoding='utf8', delete=False, dir=dir_name, suffix='.tmp') as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            temp_path = tmp.name

        # Replace the original file with the temp file
        shutil.move(temp_path, final_path)

    def back_up_file(self, filename):
        masters_path = Path(Paths.GAME_MASTERS)
        source_file = masters_path / filename
        backup_path = Path(Paths.MASTERS_BACKUP)
        backup_file = backup_path / filename
        # Make sure the backup directory exists
        backup_file.parent.mkdir(parents=True, exist_ok=True)

        # Copy only if it hasn't already been backed up
        if not backup_file.exists():
            try:
                shutil.copy2(source_file, backup_file)
                print(f"            ├─ 🔒 Backed up Unity asset to: {backup_file}")
            except Exception as e:
                print(f"            ├─ ❌ Failed to back up {source_file}: {e}")

    def get_android_file_timestamps(self, android_path) -> dict:
        result = subprocess.run(
            ["adb", "shell", "ls", "-lR", android_path],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to list remote files: {result.stderr}")

        pattern = re.compile(r"^\S+\s+\d+\s+\S+\s+\S+\s+\d+\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)$")
        timestamps = {}

        for line in result.stdout.splitlines():
            match = pattern.match(line.strip())
            if match:
                date_str, time_str, filename = match.groups()
                full_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                timestamps[filename] = full_dt

        return timestamps
    
    def pull_updated_files_from_mobile(self, remote_path, local_path, last_execution_timestamp, initial_setup_timestamp):
        remote_files = self.get_android_file_timestamps(remote_path)

        for filename, mod_time in remote_files.items():
            if filename in Config.FILES_TO_TRANSLATE:
                # Pull files that have been modified after the last execution timestamp 
                # And files with a modified date earlier than the initial execution (it is a new file that has been added to the translated files list)
                if ( mod_time > last_execution_timestamp) or mod_time < initial_setup_timestamp:
                    print(f"Pulling updated file: {filename}")
                    subprocess.run([
                        "adb", "pull",
                        f"{remote_path}/{filename}",
                        f"{local_path}/{filename}"
                    ])

    def pull_masters_from_mobile():
        output_dir = Path('./Android')
        output_dir.mkdir(exist_ok=True)

        result = subprocess.run([
            "./platform-tools//adb.exe", "pull",
            Paths.GAME_MASTERS_Android,
            str(output_dir)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(" ❌ Error pulling masters files. Make sure phone is connected and usb debugging enabled. Error message:" , result.stderr)
            sys.exit(1)

    def pull_file_from_mobile(remote_file, local_file):
        command = ["./platform-tools//adb.exe", "pull", remote_file, local_file]
        result = subprocess.run(command, check=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(" ❌ Error pulling file. Make sure phone is connected and usb debugging enabled. Error message:" , result.stderr)
            sys.exit(1)

    def check_file_exists_on_device(remote_file):
        """
        Check if a specific file exists on the Android device using ADB.
        """
        command = ["./platform-tools//adb.exe", "shell", "test", "-f", remote_file]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # If the file exists, test will return a 0 status code
        if result.returncode == 0:
            return True
        else:
            return False
        
    def push_patched_textures_to_android():
        #patched_root = Path(Paths.PATCHED_TEXTURES_Android)
        patched_root = Config.PROJECT_ROOT / Device.Android / Paths.PATCHED_TEXTURES
        android_root = "/sdcard/Android/data/com.disgaearpg.forwardworks/files/assetbundle"

        print(f"\n    🚀 Pushing patched textures to Android...")

        for patched_file in patched_root.rglob("*"):
            if patched_file.is_file():

                relative_path = patched_file.relative_to(patched_root)
                remote_file = f"{android_root}/{relative_path}"
                remote_file = Path(remote_file).as_posix()
                if os.path.exists(patched_file):  # Check if the file exists in local working dir
                    if Helper.check_file_exists_on_device(remote_file):                       
                        print(f"           ├─ 📤 Pushing {relative_path} → {remote_file}")
                        command = ["./platform-tools//adb.exe", "push", str(patched_file), remote_file]
                        subprocess.run(command, check=True)

        print(f"       ├─ ✅ Finished pushing all patched textures.")

    def adb_push_file(local_path: Path, remote_path: str, filename:str):
        # Push each file to the target location on the device
        result = subprocess.run([
            "./platform-tools//adb.exe", "push", str(local_path), f"{remote_path}/{filename}"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"Files pushed successfully: {filename}")
        else:
            print(f"Error pushing {filename}:", result.stderr)