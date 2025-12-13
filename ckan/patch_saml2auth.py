#!/usr/bin/env python3
"""
Patch ckanext-saml2auth for Flask 3.x compatibility.
This ensures session data is JSON serializable.
"""
import sys
import re

SAML2AUTH_FILE = '/usr/lib/adx/.adxvenv/adx-T9R9rqnS/lib/python3.10/site-packages/ckanext/saml2auth/views/saml2auth.py'

def patch_file():
    try:
        with open(SAML2AUTH_FILE, 'r') as f:
            content = f.read()

        # Check if already patched
        if 'FLASK3_PATCHED' in content:
            print("saml2auth already patched for Flask 3.x")
            return True

        # Find and replace the problematic session assignments
        # Convert ava (attribute value assertion) dict to ensure it's JSON serializable
        original = '''    # SAML username - unique
    saml_id = user_info.text'''

        replacement = '''    # SAML username - unique
    saml_id = user_info.text
    # FLASK3_PATCHED: Ensure ava is JSON serializable for Flask 3.x session
    # Convert any non-serializable objects to strings
    auth_response.ava = {k: [str(v) for v in vals] for k, vals in auth_response.ava.items()}'''

        if original in content:
            content = content.replace(original, replacement)

            with open(SAML2AUTH_FILE, 'w') as f:
                f.write(content)

            print("Successfully patched saml2auth for Flask 3.x compatibility")
            return True
        else:
            print("Could not find target code to patch")
            return False

    except Exception as e:
        print(f"Error patching saml2auth: {e}")
        return False

if __name__ == '__main__':
    success = patch_file()
    sys.exit(0 if success else 1)
