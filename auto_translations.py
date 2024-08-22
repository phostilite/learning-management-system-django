import polib
from googletrans import Translator
import os
import subprocess
import re
import chardet
import unicodedata
import codecs

# List of language codes
languages = [
    'en', 'ar', 'fr', 'de', 'ja', 'hi', 'es', 'pt', 'ru', 'it', 'ko', 'nl', 'tr', 'pl', 'sv', 'da', 'fi', 'el', 'he', 'th', 'vi', 'id', 'bn', 'ta', 'te', 'kn', 'pa', 'mr', 'ml'
]

def detect_encoding(file_path):
    encodings = ['utf-8', 'iso-8859-1', 'windows-1252', 'ascii']
    for enc in encodings:
        try:
            with codecs.open(file_path, 'r', encoding=enc) as file:
                file.read()
            return enc
        except UnicodeDecodeError:
            continue
    
    # If none of the above work, use chardet as a fallback
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def sanitize_string(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')

def unicode_escape(s):
    return ''.join('\\U{:08x}'.format(ord(c)) if ord(c) > 0xFFFF else c for c in s)

def translate_po_file(input_file, target_lang):
    encoding = detect_encoding(input_file)
    print(f"Detected encoding: {encoding}")
    
    try:
        po = polib.pofile(input_file, encoding=encoding)
    except Exception as e:
        print(f"Error reading PO file: {str(e)}")
        return
    
    translator = Translator()
    
    # Update header
    po.metadata['Content-Type'] = 'text/plain; charset=UTF-8'
    
    for entry in po:
        if entry.msgstr == "" and not entry.obsolete:
            try:
                # Preserve format specifiers
                placeholders = re.findall(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', entry.msgid)
                sanitized_msgid = sanitize_string(re.sub(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', '{}', entry.msgid))
                translated = translator.translate(sanitized_msgid, dest=target_lang).text
                
                # Reinsert placeholders
                for i, placeholder in enumerate(placeholders):
                    translated = translated.replace('{}', placeholder, 1)
                
                entry.msgstr = unicode_escape(translated)
                print(f"Translated '{entry.msgid}' to '{entry.msgstr}'")
            except Exception as e:
                print(f"Error translating '{entry.msgid}': {str(e)}")
    
    po.save(input_file)

def compile_messages():
    try:
        result = subprocess.run(["django-admin", "compilemessages"], capture_output=True, text=True, check=True)
        print("Messages compiled successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling messages: {e}")
        print(e.output)

def main():
    for target_lang in languages:
        locale_path = os.path.join('locale', target_lang, 'LC_MESSAGES')
        os.makedirs(locale_path, exist_ok=True)

        try:
            subprocess.run(["django-admin", "makemessages", "-l", target_lang, "--add-location", "file"], check=True)
            print(f"Message file for {target_lang} created/updated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating/updating message file: {e}")
            continue

        po_file = os.path.join(locale_path, 'django.po')
        translate_po_file(po_file, target_lang)
    
    compile_messages()

if __name__ == "__main__":
    main()