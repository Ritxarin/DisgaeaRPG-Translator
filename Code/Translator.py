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


class EffectTranslator:
    def __init__(self, path='./PatternDictionaries/EffectDictionary.json'):
        self.replacements = []
        if os.path.exists(path):
            with open(path, 'r', encoding='utf8') as f:
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

        # External services
        self.files_for_deepl = ['stage', 'character', 'memory', 'episode', 'command']

        self.translator_google = GoogleTranslator(source='auto', target='en')

        # Try initialize DeepL safely
        self.translator_deepl = None
        if Config.DEEPL_API_KEY and Config.DEEPL_API_KEY != "YOUR API KEY HERE":
            try:
                self.translator_deepl = deepl.Translator(Config.DEEPL_API_KEY)
                usage = self.translator_deepl.get_usage()
                if usage.character.limit is None:
                    print("⚠️ DeepL key valid but usage limits unknown.")
            except deepl.exceptions.AuthorizationException:
                print("❌ Invalid DeepL API key.")
            except Exception as e:
                print(f"⚠️ Failed to initialize DeepL: {e}")

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

            # elif filename == "leaderskill" and field == "description":
            #     translation = self.evility_translator.translate(value)
            #     if translation != value:
            #         return translation

            # 3️⃣ External translators
            elif filename in self.files_for_deepl and self.translator_deepl:
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
                result = self.translator_deepl.translate_text(text, target_lang="EN-US")
                return result.text
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
