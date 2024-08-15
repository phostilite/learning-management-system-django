import polib
from googletrans import Translator
import os
import subprocess
import re

def translate_po_file(input_file, target_lang):
    po = polib.pofile(input_file)
    translator = Translator()
    
    for entry in po:
        if entry.msgstr == "" and not entry.obsolete:
            try:
                # Preserve format specifiers
                placeholders = re.findall(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', entry.msgid)
                translated = translator.translate(re.sub(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', '{}', entry.msgid), dest=target_lang).text
                
                # Reinsert placeholders
                for i, placeholder in enumerate(placeholders):
                    translated = translated.replace('{}', placeholder, 1)
                
                entry.msgstr = translated
                print(f"Translated '{entry.msgid}' to '{entry.msgstr}'")
            except Exception as e:
                print(f"Error translating '{entry.msgid}': {str(e)}")
    
    po.save(input_file)

def compile_messages():
    try:
        result = subprocess.run(["python", "manage.py", "compilemessages"], capture_output=True, text=True, check=True)
        print("Messages compiled successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling messages: {e}")
        print(e.output)

def main(target_lang):
    locale_path = os.path.join('locale', target_lang, 'LC_MESSAGES')
    os.makedirs(locale_path, exist_ok=True)

    try:
        subprocess.run(["python", "manage.py", "makemessages", "-l", target_lang], check=True)
        print(f"Message file for {target_lang} created/updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating/updating message file: {e}")
        return

    po_file = os.path.join(locale_path, 'django.po')
    translate_po_file(po_file, target_lang)
    compile_messages()

if __name__ == "__main__":
    target_language = 'ar'  # Change this to your target language code
    main(target_language)