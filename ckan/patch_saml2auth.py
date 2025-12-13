#!/usr/bin/env python3
"""
Patch ckanext-saml2auth for Flask 3.x compatibility.
This ensures session data is JSON serializable.
"""
import sys
import os
import re

# Try to find the virtual environment path - works both inside and outside Docker
VENV_PATHS = [
    '/usr/lib/adx/.adxvenv/adx-T9R9rqnS/lib/python3.10/site-packages',  # Docker path
    os.path.expanduser('~/fjelltopp/adx/adx_develop/.adxvenv/adx-T9R9rqnS/lib/python3.10/site-packages'),  # Local path
]

VENV_PATH = None
for path in VENV_PATHS:
    if os.path.exists(path):
        VENV_PATH = path
        break

if not VENV_PATH:
    print("Error: Could not find virtual environment path")
    sys.exit(1)

SAML2AUTH_FILE = os.path.join(VENV_PATH, 'ckanext/saml2auth/views/saml2auth.py')
CACHE_FILE = os.path.join(VENV_PATH, 'ckanext/saml2auth/cache.py')

def patch_saml2auth_views():
    """Patch the saml2auth views file to ensure ava is JSON serializable"""
    try:
        with open(SAML2AUTH_FILE, 'r') as f:
            content = f.read()

        # Check if already patched
        if 'FLASK3_PATCHED_AVA' in content:
            print("saml2auth views already patched for Flask 3.x (ava)")
            return True

        # Find and replace the problematic session assignments
        # Convert ava (attribute value assertion) dict to ensure it's JSON serializable
        original = '''    # SAML username - unique
    saml_id = user_info.text'''

        replacement = '''    # SAML username - unique
    saml_id = user_info.text
    # FLASK3_PATCHED_AVA: Ensure ava is JSON serializable for Flask 3.x session
    # Convert any non-serializable objects to strings
    auth_response.ava = {k: [str(v) for v in vals] for k, vals in auth_response.ava.items()}'''

        if original in content:
            content = content.replace(original, replacement)

            with open(SAML2AUTH_FILE, 'w') as f:
                f.write(content)

            print("Successfully patched saml2auth views for Flask 3.x compatibility (ava)")
            return True
        else:
            print("Could not find target code to patch in saml2auth views")
            return False

    except Exception as e:
        print(f"Error patching saml2auth views: {e}")
        return False

def patch_saml2auth_cache():
    """Patch the cache.py file to ensure session_info is JSON serializable"""
    try:
        with open(CACHE_FILE, 'r') as f:
            content = f.read()

        # Check if already patched
        if 'FLASK3_PATCHED_SESSION_INFO' in content:
            print("saml2auth cache already patched for Flask 3.x (session_info)")
            return True

        # Patch set_saml_session_info to convert NameID objects to strings
        original = '''def set_saml_session_info(session, saml_session_info):
    session['_saml_session_info'] = saml_session_info'''

        replacement = '''def set_saml_session_info(session, saml_session_info):
    # FLASK3_PATCHED_SESSION_INFO: Convert NameID objects to strings for JSON serialization
    serializable_info = {}
    for key, value in saml_session_info.items():
        if hasattr(value, 'text'):
            # NameID object - convert to string representation
            serializable_info[key] = str(value.text) if value.text else str(value)
        elif isinstance(value, dict):
            # Recursively handle nested dicts
            serializable_info[key] = {k: str(v) if hasattr(v, 'text') else v for k, v in value.items()}
        elif isinstance(value, list):
            # Handle lists that might contain NameID objects
            serializable_info[key] = [str(v.text) if hasattr(v, 'text') else v for v in value]
        else:
            serializable_info[key] = value
    session['_saml_session_info'] = serializable_info'''

        if original in content:
            content = content.replace(original, replacement)

            with open(CACHE_FILE, 'w') as f:
                f.write(content)

            print("Successfully patched saml2auth cache for Flask 3.x compatibility (session_info)")
            return True
        else:
            print("Could not find target code to patch in cache.py")
            return False

    except Exception as e:
        print(f"Error patching saml2auth cache: {e}")
        return False

if __name__ == '__main__':
    success1 = patch_saml2auth_views()
    success2 = patch_saml2auth_cache()
    sys.exit(0 if (success1 and success2) else 1)
