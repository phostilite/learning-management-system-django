import os
import subprocess
import re
import chardet
import unicodedata
import codecs
import polib
from googletrans import Translator
from django.core.management import call_command
from django.apps import apps
from django.conf import settings
from django.db import connection, models
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# List of language codes
languages = [
    'en', 'ar', 'fr', 'de', 'ja', 'hi', 'es', 'pt', 'ru', 'it', 'ko', 'nl', 'tr', 'pl', 'sv', 'da', 'fi', 'el', 'he', 'th', 'vi', 'id', 'bn', 'ta', 'te', 'kn', 'pa', 'mr', 'ml'
]

# List of app names to process
apps_to_process = [
    'api', 'users', 'courses', 'authentication', 'website', 'certificates', 
    'quizzes', 'leaderboard', 'support', 'announcements', 'activities', 
    'events', 'organization', 'gamification'
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
    
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def sanitize_string(s):
    return ''.join(ch for ch in s if unicodedata.category(ch)[0] != 'C')

def unicode_escape(s):
    return ''.join('\\U{:08x}'.format(ord(c)) if ord(c) > 0xFFFF else c for c in s)

def translate_po_file(input_file, target_lang):
    try:
        encoding = detect_encoding(input_file)
        print(f"Detected encoding for {input_file}: {encoding}")
        
        po = polib.pofile(input_file, encoding=encoding)
        
        translator = Translator()
        
        po.metadata['Content-Type'] = 'text/plain; charset=UTF-8'
        
        for entry in po:
            if entry.msgstr == "" and not entry.obsolete:
                try:
                    placeholders = re.findall(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', entry.msgid)
                    sanitized_msgid = sanitize_string(re.sub(r'%\([^)]+\)[sd]|%[sd]|\{[^}]+\}', '{}', entry.msgid))
                    translated = translator.translate(sanitized_msgid, dest=target_lang).text
                    
                    for i, placeholder in enumerate(placeholders):
                        translated = translated.replace('{}', placeholder, 1)
                    
                    entry.msgstr = unicode_escape(translated)
                    print(f"Translated: '{entry.msgid}' -> '{entry.msgstr}'")
                except Exception as e:
                    print(f"Error translating '{entry.msgid}': {str(e)}")
        
        po.save(input_file)
    except Exception as e:
        print(f"Error processing PO file {input_file}: {str(e)}")

def compile_messages():
    try:
        result = subprocess.run(["django-admin", "compilemessages"], capture_output=True, text=True, check=True)
        print("Messages compiled successfully.")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling messages: {e}")
        print(e.output)

def translate_database_content(target_lang):
    try:
        translator = Translator()
        
        for app_name in apps_to_process:
            app_models = apps.get_app_config(app_name).get_models()
            
            for model in app_models:
                print(f"\nProcessing model: {model.__name__}")
                
                # Get specific fields of the model
                fields_to_translate = [
                    f for f in model._meta.fields 
                    if isinstance(f, (models.CharField, models.TextField, models.BooleanField))
                ]
                
                if not fields_to_translate:
                    print(f"No suitable fields found in {model.__name__}")
                    continue
                
                # Fetch all instances of the model
                instances = model.objects.all()
                
                for instance in instances:
                    for field in fields_to_translate:
                        original_value = getattr(instance, field.name)
                        if original_value:
                            try:
                                if isinstance(field, models.BooleanField):
                                    # For BooleanField, we just copy the value
                                    translated_value = original_value
                                else:
                                    translated_value = translator.translate(str(original_value), dest=target_lang).text
                                
                                setattr(instance, f"{field.name}_{target_lang}", translated_value)
                                print(f"Translated {model.__name__}.{field.name}: '{original_value}' -> '{translated_value}'")
                            except Exception as e:
                                print(f"Error translating {model.__name__}.{field.name}: {str(e)}")
                    
                    try:
                        instance.save()
                        print(f"Saved translated instance of {model.__name__}")
                    except Exception as e:
                        print(f"Error saving instance of {model.__name__}: {str(e)}")
    except Exception as e:
        print(f"Error translating database content: {str(e)}")

def main():
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.settings")
        import django
        django.setup()

        for target_lang in languages:
            print(f"\n--- Processing language: {target_lang} ---")
            locale_path = os.path.join('locale', target_lang, 'LC_MESSAGES')
            os.makedirs(locale_path, exist_ok=True)

            try:
                call_command("makemessages", locale=[target_lang], add_location="file")
                print(f"Message file for {target_lang} created/updated successfully.")
            except Exception as e:
                print(f"Error creating/updating message file for {target_lang}: {str(e)}")
                continue

            po_file = os.path.join(locale_path, 'django.po')
            print(f"\nTranslating PO file: {po_file}")
            translate_po_file(po_file, target_lang)
            
            print(f"\nTranslating database content for {target_lang}")
            translate_database_content(target_lang)
        
        compile_messages()
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()