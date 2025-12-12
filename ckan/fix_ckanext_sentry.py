#!/usr/bin/env python3
"""
Fix ckanext-sentry setup.py to avoid importing the module before installation.
This script patches the setup.py file after pipenv downloads it.
"""
import os
import re
import glob

def fix_sentry_setup():
    # Find the ckanext-sentry setup.py in the pipenv virtualenv
    workon_home = os.environ.get('WORKON_HOME', '/usr/lib/adx/.adxvenv')
    pattern = os.path.join(workon_home, 'adx*/src/ckanext-sentry/setup.py')
    
    setup_files = glob.glob(pattern)
    
    for setup_file in setup_files:
        if os.path.exists(setup_file):
            print(f"Found ckanext-sentry setup.py at: {setup_file}")
            
            with open(setup_file, 'r') as f:
                content = f.read()
            
            # Replace the problematic import with direct variable definitions
            new_content = re.sub(
                r'from ckanext\.sentry import __version__, __description__',
                "__version__ = '0.0.2'\n__description__ = 'Sentry support for CKAN'",
                content
            )
            
            if new_content != content:
                with open(setup_file, 'w') as f:
                    f.write(new_content)
                print(f"Successfully patched {setup_file}")
                return True
            else:
                print(f"No changes needed for {setup_file}")
                return True
    
    print("ckanext-sentry setup.py not found")
    return False

if __name__ == '__main__':
    fix_sentry_setup()
