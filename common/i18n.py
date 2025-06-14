import json
import os

class Translator:
    def __init__(self, language_code='en'):
        self.language_code = language_code
        # Assuming i18n directory is at the project root, two levels up from common/i18n.py
        # common -> project_root -> i18n
        self.i18n_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'i18n'))
        self.translations = {}
        self.load_translations(self.language_code)

    def load_translations(self, language_code):
        file_path = os.path.join(self.i18n_dir, f"{language_code}.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Language file not found: {file_path}")
            if language_code != 'en': # Avoid infinite recursion if en.json is also missing
                print("Warning: Falling back to English.")
                self.load_translations('en')
            else:
                self.translations = {} # English is missing, no fallback
        except json.JSONDecodeError:
            print(f"Warning: Error decoding JSON from language file: {file_path}")
            if language_code != 'en':
                print("Warning: Falling back to English due to decode error.")
                self.load_translations('en')
            else:
                self.translations = {} # English has decode error

    def get_string(self, key, default_value=None, **kwargs):
        value = self.translations.get(key, default_value if default_value is not None else key)
        if kwargs:
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                print(f"Warning: Missing key '{e}' in translation for '{key}' with arguments {kwargs}")
        return value

    def set_language(self, language_code):
        self.language_code = language_code
        self.load_translations(language_code)
