import io
import os
import json
import re
import time
from deep_translator import GoogleTranslator
import deepl
from datetime import datetime

from Code import EvilityRegex
from Code.config import Config, Paths


class DictionaryTranslator:
    def __init__(self):
        folder_path = Paths.DICTIONARIES_DIR
        self.dictionary = {}
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, 'r', encoding='utf8') as f:
                        try:
                            self.dictionary.update(json.load(f))
                        except json.JSONDecodeError:
                            print(f"⚠️ Skipping invalid JSON: {filename}")

    def translate(self, jp_text):
        return self.dictionary.get(jp_text)

    def has(self, jp_text):
        return jp_text in self.dictionary
    
class DeepLTranslator:
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.DEEPL_API_KEY
        self.client = None
        self.is_available = False

        if not self.api_key or self.api_key == "YOUR API KEY HERE":
            print("❌ No valid DeepL API key provided.")
            return

        try:
            self.client = deepl.Translator(self.api_key)
            usage = self.client.get_usage()
            self.is_available = True
            if usage.character.limit is None:
                print("⚠️ DeepL key valid, but usage limits unknown.")
        except deepl.exceptions.AuthorizationException:
            print("❌ Invalid DeepL API key.")
        except Exception as e:
            print(f"⚠️ Failed to initialize DeepL: {e}")

    def translate(self, text, source_lang="JA", target_lang="EN-US"):
        if not self.is_available:
            print("⚠️ DeepL not available — falling back or skipping.")
            return None
        try:
            result = self.client.translate_text(text, source_lang=source_lang, target_lang=target_lang)
            return result.text
        except Exception as e:
            print(f"⚠️ DeepL translation failed: {e}")
            return None

    def get_usage(self):
        if self.client:
            return self.client.get_usage()
        return None

class CharacterNameTranslator:
    def __init__(self):
        character_dir_path = Paths.CHARACTER_DICTIONARIES_DIR / 'CharacterNameDictionary.json'
        character_prefix_dir_path = Paths.CHARACTER_DICTIONARIES_DIR / 'CharacterNamePrefixDictionary.json'
        self.character_name_dict = {}
        self.character_prefix_dict = {}
        self.translator_deepl = DeepLTranslator()
        self.google_translator = GoogleTranslator(source='auto', target='en')

        if os.path.exists(Paths.CHARACTER_DICTIONARIES_DIR):
            # Load character name dict
            with io.open(character_dir_path, encoding='utf8') as f1:
                try:
                    self.character_name_dict.update(json.load(f1))
                except json.JSONDecodeError:
                        print(f"⚠️ Skipping invalid CharacterNameDictionary JSON")

            # Load character name prefix dict
            with io.open(character_prefix_dir_path, encoding='utf8') as f2:
                try:
                    self.character_prefix_dict.update(json.load(f2))
                except json.JSONDecodeError:
                        print(f"⚠️ Skipping invalid CharacterNamePrefixDictionary JSON")

    def _smart_title(self, text):
        small_words = {"of", "the", "a", "in", "and", "to"}
        words = text.lower().split()
        titled = [words[0].capitalize()] + [
            w if w in small_words else w.capitalize()
            for w in words[1:]
        ]
        return " ".join(titled)
    
    def translate(self, jp_name):
        # Build regex to match known names (longest first to avoid partial matches)
        name_pattern = "|".join(sorted(self.character_name_dict.keys(), key=len, reverse=True))
        regex = re.compile(f"({name_pattern})")

        match = regex.search(jp_name)
        # No match found in dictionary, use DeepL to translate entire name
        if not match:
            return self._translate_with_fallback(jp_name)

        char_jp = match.group(1)
        char_en = self.character_name_dict[char_jp]
        prefix = jp_name.replace(char_jp, "")

        if prefix:
            # Character name contains a prefix. Check if we have it in the prefix dictionary
            if prefix in self.character_prefix_dict:
                translated_prefix = self.character_prefix_dict[prefix]
                return f"{translated_prefix} {char_en}"
            # Otherwise, translate prefix via DeepL
            translated_prefix = self._translate_with_fallback(prefix)
            translated_prefix = self._smart_title(translated_prefix)
            return f"{translated_prefix} {char_en}"
        else:
            return char_en

    def _translate_with_fallback(self, text):
        try:
            return self.translator_deepl.translate(text=text, source_lang="JA", target_lang="EN-US")
        except deepl.DeepLException as e:
            msg = str(e).lower()
            if any(k in msg for k in ["quota", "limit", "too many requests"]):
                print("⚠️ DeepL quota exceeded — switching to Google Translate.")
                return self.google_translator.translate(text)
            raise

class EffectTranslator:
    def __init__(self):
        self.dictionary_path =  Paths.PATTERN_DICTIONARIES_DIR / 'EffectDictionary.json'
        self.replacements = []
        if os.path.exists(self.dictionary_path):
            with open(self.dictionary_path, 'r', encoding='utf8') as f:
                raw_dict = json.load(f)
                self.replacements = sorted(
                    [(re.compile(re.escape(k)), v) for k, v in raw_dict.items()],
                    key=lambda x: len(x[0].pattern),
                    reverse=True
                )

    def translate(self, text):
        for pattern, replacement in self.replacements:
            text = pattern.sub(replacement, text)
        return text
    
class EvilityTranslator:    
    def __init__(self):
        self.patterns = EvilityRegex.patterns
        return

    def translate(self, text):
        for pattern, repl in self.patterns:
            match = pattern.search(text)
            if match:
                return repl(match)
        return text

class Translator:
    def __init__(self):
        self.dict_translator = DictionaryTranslator()
        self.effect_translator = EffectTranslator()
        self.evility_translator = EvilityTranslator()
        self.translator_deepl = DeepLTranslator()
        self.character_translator = CharacterNameTranslator()
        self.translator_google = GoogleTranslator(source='auto', target='en')

        # External services
        self.files_for_deepl = ['stage', 'character', 'memory', 'episode', 'command']        

    # ---------------------------
    # Main Translation Dispatcher
    # ---------------------------
    def translate(self, filename, field, value) -> str:
        if not value or not isinstance(value, str):
            return value

        try:
            # 1️⃣ Dictionary lookup (always first)
            if self.dict_translator.has(value):
                return self.dict_translator.translate(value)
        
            # 2️⃣ Regex replacement for specific files/fields
            if filename == "command" and field == "description_effect":
                return self.effect_translator.translate(value)
            
            # 3️⃣ Character name translation
            if filename == "character" and field == "name":
                return self.character_translator.translate(value)

            if filename == "leaderskill" and field == "description":
                translation = self.evility_translator.translate(value)
                if translation != value:
                    return translation

            # 3️⃣ External translators
            if filename in self.files_for_deepl and self.translator_deepl:
                result = self._translate_with_fallback(value)
            else:
                result = self._translate_google(value)

        except Exception as e:
            print(f"❌ Translation error in {filename}.{field}: {e}")
            result = value  # Fallback to original text

        return result

    # ---------------------------
    # Fallback Chain: DeepL → Google
    # ---------------------------
    def _translate_with_fallback(self, text):
        try:
            return self._translate_deepl(text)
        except deepl.DeepLException as e:
            msg = str(e).lower()
            if any(k in msg for k in ["quota", "limit", "too many requests"]):
                print("⚠️ DeepL quota exceeded — switching to Google Translate.")
                return self._translate_google(text)
            raise

    # ---------------------------
    # DeepL Translator
    # ---------------------------
    def _translate_deepl(self, text, max_retries=3, delay=5):
        for attempt in range(max_retries):
            try:
                result = self.translator_deepl.translate(text, source_lang="JA", target_lang="EN-US")
                return result
            except deepl.DeepLException as e:
                print(f"🌀 DeepL attempt {attempt+1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                else:
                    raise

    # ---------------------------
    # Google Translator
    # ---------------------------
    def _translate_google(self, text):
        try:
            return self.translator_google.translate(text)
        except Exception as e:
            print(f"⚠️ Google Translate failed: {e}")
            return text
