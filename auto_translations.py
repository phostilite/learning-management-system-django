import polib
from googletrans import Translator
import os
import subprocess
import re
import chardet
import unicodedata
import codecs
import logging
from typing import List, Tuple, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TranslationManager:
    LANGUAGES = [
    'ar', 'fr', 'de', 'ja', 'hi', 'es', 'pt', 'ru', 'it', 'ko', 'nl', 'tr', 'pl', 'sv', 'da', 'fi', 'el', 'he', 'th', 'vi', 'id', 'bn', 'ta', 'te', 'kn', 'pa', 'mr', 'ml'
    ]
    
    IGNORE_PATTERNS = [
        'node_modules/*',
        'staticfiles/*',
        'venv/*',
        '*.txt'
    ]
    
    def __init__(self):
        self.translator = Translator()
        
    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """Detect file encoding with fallback options."""
        encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'ascii']
        for enc in encodings:
            try:
                with codecs.open(file_path, 'r', encoding=enc) as file:
                    file.read()
                return enc
            except UnicodeDecodeError:
                continue
        
        with open(file_path, 'rb') as file:
            return chardet.detect(file.read())['encoding']

    def validate_po_entry(self, entry: polib.POEntry) -> Tuple[bool, str]:
        """Validate a single PO entry."""
        if not entry.msgid or not isinstance(entry.msgid, str):
            return False, "Invalid msgid"
        if entry.msgstr and not isinstance(entry.msgstr, str):
            return False, "Invalid msgstr"
        return True, ""

    def remove_duplicates(self, po_file: polib.POFile) -> int:
        """Remove duplicate entries from PO file."""
        seen: Dict[str, polib.POEntry] = {}
        duplicates: List[polib.POEntry] = []
        
        for entry in po_file:
            if entry.msgid in seen:
                duplicates.append(entry)
            else:
                seen[entry.msgid] = entry
        
        for dup in duplicates:
            po_file.remove(dup)
        
        return len(duplicates)

    def validate_po_file(self, po_file: polib.POFile) -> List[str]:
        """Validate entire PO file."""
        errors = []
        
        if not po_file.metadata.get('Content-Type'):
            errors.append("Missing Content-Type in header")
        
        for entry in po_file:
            is_valid, error = self.validate_po_entry(entry)
            if not is_valid:
                errors.append(f"Error in msgid '{entry.msgid}': {error}")
        
        return errors

    def translate_string(self, text: str, target_lang: str) -> str:
        """Translate a single string with format preservation."""
        format_specs = []
        counter = 0
        
        # Handle Python format strings
        for pattern in [r'\{\}', r'\{[0-9]+\}']:
            matches = re.finditer(pattern, text)
            for match in matches:
                placeholder = f'[[{counter}]]'
                text = text.replace(match.group(), placeholder)
                format_specs.append(match.group())
                counter += 1
        
        # Translate
        translated = self.translator.translate(text, dest=target_lang).text
        
        # Restore format specifiers
        for i, spec in enumerate(format_specs):
            translated = translated.replace(f'[[{i}]]', spec)
            
        return translated

    def translate_po_file(self, input_file: str, target_lang: str) -> None:
        """Translate PO file contents."""
        try:
            encoding = self.detect_encoding(input_file)
            logging.info(f"Detected encoding: {encoding}")
            
            po = polib.pofile(input_file, encoding=encoding)
            
            # Validate and clean
            errors = self.validate_po_file(po)
            if errors:
                for error in errors:
                    logging.error(error)
                return
            
            num_duplicates = self.remove_duplicates(po)
            if num_duplicates:
                logging.info(f"Removed {num_duplicates} duplicate entries")
            
            po.metadata['Content-Type'] = 'text/plain; charset=UTF-8'
            
            # Translate entries
            for entry in po:
                # Handle both fuzzy and non-fuzzy entries that need translation
                if (entry.fuzzy or not entry.msgstr) and not entry.obsolete:
                    try:
                        translated = self.translate_string(entry.msgid, target_lang)
                        entry.msgstr = translated
                        # Clear the fuzzy flag after successful translation
                        if 'fuzzy' in entry.flags:
                            entry.flags.remove('fuzzy')
                        logging.info(f"Translated: {entry.msgid} -> {translated}")
                    except Exception as e:
                        logging.error(f"Translation error for '{entry.msgid}': {str(e)}")
            
            po.save(input_file)
            logging.info(f"Successfully saved translations to {input_file}")
            
        except Exception as e:
            logging.error(f"Error processing PO file: {str(e)}")

    def compile_messages(self) -> None:
        """Compile message files."""
        try:
            result = subprocess.run(
                ["django-admin", "compilemessages"],
                capture_output=True,
                text=True,
                check=True
            )
            logging.info("Messages compiled successfully")
            logging.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error(f"Compilation error: {e.output}")

    def make_messages(self, target_lang: str) -> None:
        """Create/update message files."""
        ignore_patterns = ' '.join([f'--ignore={pattern}' for pattern in self.IGNORE_PATTERNS])
        
        try:
            cmd = f"django-admin makemessages -l {target_lang} --add-location file {ignore_patterns}"
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                check=True
            )
            logging.info(f"Message file for {target_lang} created/updated successfully")
            logging.info(result.stdout)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error creating messages: {e.stderr}")

    def process_translations(self) -> None:
        """Main processing function."""
        for target_lang in self.LANGUAGES:
            locale_path = os.path.join('locale', target_lang, 'LC_MESSAGES')
            os.makedirs(locale_path, exist_ok=True)
            
            self.make_messages(target_lang)
            
            po_file = os.path.join(locale_path, 'django.po')
            if os.path.exists(po_file):
                self.translate_po_file(po_file, target_lang)
            else:
                logging.warning(f"PO file not found: {po_file}")
        
        self.compile_messages()

def main():
    """Entry point."""
    translator = TranslationManager()
    translator.process_translations()

if __name__ == "__main__":
    main()