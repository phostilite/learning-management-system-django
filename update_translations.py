import os
import subprocess

# List of language codes
languages = [
    'en', 'ar', 'fr', 'de', 'ja', 'hi', 'es', 'pt', 'ru', 'it', 'ko', 'nl', 'tr', 'pl', 'sv', 'da', 'fi', 'el', 'he', 'th', 'vi', 'id', 'bn', 'ta', 'te', 'kn', 'pa', 'mr', 'ml'
]

# Path to your Django project
project_path = os.getenv('PROJECT_PATH')

# Step 1: Extract strings
def extract_strings():
    subprocess.run(['django-admin', 'makemessages', '-a'], cwd=project_path)

# Step 2: Update .po files (this step is manual, but we can ensure the files exist)
def ensure_po_files():
    for lang in languages:
        po_file_path = os.path.join(project_path, 'locale', lang, 'LC_MESSAGES', 'django.po')
        if not os.path.exists(po_file_path):
            subprocess.run(['django-admin', 'makemessages', '-l', lang], cwd=project_path)

# Step 3: Compile messages
def compile_messages():
    subprocess.run(['django-admin', 'compilemessages'], cwd=project_path)

if __name__ == "__main__":
    extract_strings()
    ensure_po_files()
    compile_messages()
    print("Translation files updated and compiled successfully.")