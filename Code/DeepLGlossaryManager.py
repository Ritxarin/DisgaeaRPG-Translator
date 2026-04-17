import os
import json
import hashlib
import deepl
from pathlib import Path
from Code.config import Config, Paths
import requests

class DeepLGlossaryManager:
    """
    Manages DeepL glossary lifecycle:
    - Auto-setup on first run
    - Smart updates only when character dictionary changes
    - Retrieves existing glossary ID if already uploaded
    """
    
    def __init__(self):
        self.glossary_file = Paths.DEEPL_DIR / "Glossary.csv"
        self.character_master_path = Paths.CHARACTER_DICTIONARIES_DIR / "CharacterMasterDictionary.json"
        self.BASE_URL = "https://api-free.deepl.com/v2"
        self.headers = {
            "Authorization": f"DeepL-Auth-Key {Config.DEEPL_API_KEY}",
            "Content-Type": "application/json"
        }
        self.client = None
        self.glossary_id = None
        
    def setup(self):
        """
        Main entry point - sets up glossary if DeepL is available
        Returns: glossary_id (str) or None if DeepL not available
        """
        # Check if DeepL is configured
        if not Config.DEEPL_API_KEY or Config.DEEPL_API_KEY == "YOUR API KEY HERE":
            print("ℹ️  DeepL API key not configured - skipping glossary setup")
            return None
        
        try:
            self.client = deepl.Translator(Config.DEEPL_API_KEY)
            print("✅ DeepL API key validated")
        except deepl.exceptions.AuthorizationException:
            print("❌ Invalid DeepL API key - skipping glossary setup")
            return None
        except Exception as e:
            print(f"⚠️  DeepL initialization failed: {e}")
            return None
        
        # Check if we need to update the glossary
        needs_update, reason = self._needs_glossary_update()
        
        if not needs_update:
            print(f"ℹ️  Glossary up-to-date: {reason}")
            return Config.get_string_field(Config.GLOSSARY_ID)
        
        print(f"🔄 Updating glossary: {reason}")
        return self._sync_glossary()
    
    def _needs_glossary_update(self):
        """
        Determine if glossary needs to be created/updated
        Returns: (bool, str) - (needs_update, reason)
        """
        # If cache does not exist - first run, upload from codebase
        if not Config.get_string_field(Config.GLOSSARY_HASH):
            glossary_id = self._upload_glossary_from_codebase()
            Config.set_string_field(Config.GLOSSARY_ID, glossary_id)
            current_hash = self._hash_glossary()
            Config.set_string_field(Config.GLOSSARY_HASH, current_hash)
            return False, "First run, uploading glossary"
        
        # Load cache
        try:
            current_hash = self._hash_glossary()
        except:
            return True, "Cache file corrupted"
        
        # Check if CharacterMasterDictionary has changed
        current_hash = self._hash_glossary()
        cached_hash = Config.get_string_field(Config.GLOSSARY_HASH)
        
        if current_hash != cached_hash:
            return True, "Glossary has been updated"
        
        # Verify glossary still exists on DeepL
        glossary_id = Config.get_string_field(Config.GLOSSARY_ID)
        if not self._glossary_exists(glossary_id):
            return True, "Glossary not found on DeepL (may have been deleted)"
        
        return False, f"Using existing glossary (ID: {glossary_id})"
    
    def _hash_glossary(self):
        """Create hash of glossary for change detection"""
        if not self.glossary_file.exists():
            return None
        
        with open(self.glossary_file, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _glossary_exists(self, glossary_id):
        """Check if glossary exists on DeepL"""
        if not glossary_id or not self.client:
            return False
        
        try:
            self.client.get_glossary(glossary_id)
            return True
        except:
            return False
    
    def _upload_glossary_from_codebase(self):
        """
        If no glossary exists on DeepL
        Load from codebase and upload
        """       
        # Step 1: Delete old glossary (if exists)
        old_glossary_id = self._get_cached_glossary_id()
        if old_glossary_id and self._glossary_exists(old_glossary_id):
            try:
                self.client.delete_glossary(old_glossary_id)
                print(f"🗑️  Deleted old glossary: {old_glossary_id}")
            except Exception as e:
                print(f"⚠️  Could not delete old glossary: {e}")
        
        # Step 3: Upload new glossary
        glossary_id = self._upload_glossary()
        if not glossary_id:
            print("❌ Failed to upload glossary")
            return None
        
        # Step 4: Cache the result        
        return glossary_id
    
    def _sync_glossary(self):
        """
        Main sync logic:
        1. Delete old glossary if exists
        2. Upload new glossary
        3. Cache the result
        """

        # Step 1: Delete old glossary (if exists)
        old_glossary_id = self._get_cached_glossary_id()
        if old_glossary_id and self._glossary_exists(old_glossary_id):
            try:
                self.client.delete_glossary(old_glossary_id)
                print(f"🗑️  Deleted old glossary: {old_glossary_id}")
            except Exception as e:
                print(f"⚠️  Could not delete old glossary: {e}")
        
        # Step 2: Upload new glossary
        glossary_id = self._upload_glossary_from_codebase()
        if not glossary_id:
            print("❌ Failed to upload glossary")
            return None
        
        # Step 3: Cache the result
        Config.set_string_field(Config.GLOSSARY_ID, glossary_id)
        current_hash = self._hash_glossary()
        Config.set_string_field(Config.GLOSSARY_HASH, current_hash)
        
        return glossary_id
    
    def _sync_glossary_old(self):
        """
        Main sync logic:
        1. Generate TSV from CharacterMasterDictionary
        2. Delete old glossary if exists
        3. Upload new glossary
        4. Cache the result
        """
        # Step 1: Generate TSV
        if not self._generate_glossary_tsv():
            print("❌ Failed to generate glossary TSV")
            return None
        
        # Step 2: Delete old glossary (if exists)
        old_glossary_id = self._get_cached_glossary_id()
        if old_glossary_id and self._glossary_exists(old_glossary_id):
            try:
                self.client.delete_glossary(old_glossary_id)
                print(f"🗑️  Deleted old glossary: {old_glossary_id}")
            except Exception as e:
                print(f"⚠️  Could not delete old glossary: {e}")
        
        # Step 3: Upload new glossary
        glossary_id = self._upload_glossary()
        if not glossary_id:
            print("❌ Failed to upload glossary")
            return None
        
        # Step 4: Cache the result
        self._save_cache(glossary_id)
        
        return glossary_id
    
    def _generate_glossary_tsv(self):
        """
        Generate TSV file from CharacterMasterDictionary + game terminology
        """
        if not self.character_master_path.exists():
            print("⚠️  CharacterMasterDictionary.json not found")
            return False
        
        try:
            # Load character dictionary
            with open(self.character_master_path, 'r', encoding='utf8') as f:
                characters = json.load(f)
            
            # Core game terminology (manually maintained)
            game_terms = {
                "魔界": "Netherworld",
                "天界": "Celestia",
                "人間界": "Human World",
                "魔王": "Overlord",
                "天使": "Angel",
                "魔界王子": "Demon Prince",
                "悪魔": "demon",
                "堕天使": "Fallen Angel",
                "プリニー": "Prinny",
                "マナ": "Mana",
                "暗黒議会": "Dark Assembly",
                "ッス": "dood",
                "ッス!": "dood!",
            }
            
            # Combine dictionaries
            combined = {**characters, **game_terms}
            
            # Write TSV
            with open(self.glossary_file, 'w', encoding='utf8') as f:
                for jp, en in combined.items():
                    f.write(f"{jp}\t{en}\n")
            
            print(f"📝 Generated glossary TSV with {len(combined)} entries")
            return True
            
        except Exception as e:
            print(f"❌ Error generating TSV: {e}")
            return False
    
    def _upload_glossary(self):
        """Upload glossary to DeepL"""
        if not self.glossary_file.exists():
            print("❌ CSV file not found")
            return None
        
        try:
            with open(self.glossary_file, 'r', encoding='utf8') as f:
                entries = f.read()
            
            # Create glossary
            payload = {
                "name": Config.GLOSSARY_NAME,
                "source_lang": "JA",
                "target_lang": "EN",
                "entries": entries,
                "entries_format": "csv"
            }
            r = requests.post(f"{self.BASE_URL}/glossaries", headers=self.headers, json=payload)
            print(f"✅ Uploaded glossary")
            glossaries = self.client.list_glossaries()
            for g in glossaries:
                if g.name == Config.GLOSSARY_NAME:
                    return g.glossary_id
            
        except Exception as e:
            print(f"❌ Failed to upload glossary: {e}")
            return None
    
    def _save_cache(self, glossary_id):
        """Save glossary metadata to cache"""
        cache = {
            "glossary_id": glossary_id,
            "character_dict_hash": self._hash_character_dictionary(),
            "glossary_name": Config.GLOSSARY_NAME
        }
        
        with open(self.glossary_file, 'w', encoding='utf8') as f:
            json.dump(cache, f, indent=2)
        
        print(f"💾 Cached glossary metadata")
    
    def _get_cached_glossary_id(self):
        """Retrieve glossary ID from config"""
        return Config.get_string_field(Config.GLOSSARY_ID)


# Integration helper function
def setup_deepl_with_glossary():
    """
    Convenience function to set up DeepL with glossary support
    Call this at the start of your translation process
    
    Returns: glossary_id (str) or None
    """
    manager = DeepLGlossaryManager()
    return manager.setup()