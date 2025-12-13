# Python 3.10 and CKAN 2.11.4 Migration Notes

## Overview
This document tracks all changes made to upgrade the ADX project from Python 3.x to Python 3.10 and CKAN 2.11.4.

## Dependency Changes

### Pipfile Updates
**File:** `/Pipfile`

#### Updated Core CKAN Dependencies to 2.11.4
- Flask: 1.x → 3.0.3
- Werkzeug: → 3.0.6
- SQLAlchemy: → 1.4.52
- Babel: → 2.15.0
- Jinja2: → 3.1.6
- And many more (see Pipfile for complete list)

#### Removed Obsolete Packages
- beaker
- fanstatic
- flask-multistatic
- routes
- webob
- nose
- pyutilib
- funcsigs
- unicodecsv
- shutilwhich

#### Added New Packages
- flask-session==0.8.0
- flask-wtf==1.2.1
- blinker==1.8.2
- msgspec==0.18.6
- packaging==24.1
- pyparsing==3.1.2
- frictionless>=5.0.0,<6.0.0 (required by ckanext-validation)
- markupsafe>=2.0.1 (required by ckanext-validation)
- async-timeout==4.0.3 (required by redis 5.0.7 on Python < 3.11)
- numpy>=1.21.0 (required by pandas>=1.4.2)

#### Version Fixes
- setuptools: Downgraded to 58.1.0 (from 67.2.0) for compatibility
- python-slugify: Updated to >=5.0.0
- repoze.who: Re-added ==2.3 (needed by ckanext-unaids)

#### Added Missing Extensions
- ckanext-authz-service: Added as editable submodule dependency
- ckanext-validation: Added as editable submodule dependency
- ckanext-pages: Converted from git dependency to local submodule (v0.5.2)
  - Note: Converted to submodule to apply SQLAlchemy 1.4 compatibility fix

## Code Changes

### 1. ckanext-unaids Plugin
**File:** `submodules/ckanext-unaids/ckanext/unaids/plugin.py`

#### Change: Updated user identification to avoid infinite recursion (CKAN 2.11.4 API change)
- **Line 16:** Changed imports from `from ckan.views import _identify_user_default` to `from ckan.common import g, current_user`
- **Lines 66-69:** Replaced `_identify_user_default()` call with direct assignment:
  ```python
  g.user = current_user.name
  g.userobj = '' if current_user.is_anonymous else current_user
  ```
- **Reason:** In CKAN 2.11.4, `_identify_user_default()` was removed. Calling `identify_user()` instead causes infinite recursion because it calls all IAuthenticator plugins' `identify()` methods, including this one. The solution is to directly set `g.user` and `g.userobj` from `current_user`, which is what the old `_identify_user_default()` function did.

#### Change: Removed ReclineView dependency
- **Line 47:** Removed `from ckanext.reclineview.plugin import ReclineViewBase`
- **Reason:** ReclineView plugin was removed from CKAN 2.11.4

#### Change: Replaced UNAIDSReclineView with UNAIDSDataTablesView
- **Lines 309-350:** Complete rewrite of view plugin class
- Changed from inheriting `ReclineViewBase` to implementing `p.IResourceView`
- Added required methods: `view_template()`, `form_template()`
- Renamed from `UNAIDSReclineView` to `UNAIDSDataTablesView`
- **Reason:** ReclineView removed in CKAN 2.11.4, replaced with DataTablesView pattern

### 2. ckanext-unaids Auth Logic
**File:** `submodules/ckanext-unaids/ckanext/unaids/auth_logic.py`

#### Change: Flask 3.x compatibility
- **Line 7:** Removed `_request_ctx_stack` from Flask imports
- **Line 95:** `_request_ctx_stack.top.current_user = payload` → `g.current_user = payload`
- **Reason:** `_request_ctx_stack` was removed in Flask 2.2+ / 3.x

### 3. ckanext-unaids User Info Blueprint
**File:** `submodules/ckanext-unaids/ckanext/unaids/blueprints/user_info_blueprint.py`

#### Change: CKAN 2.11.4 blueprint pattern
- **Line 6:** Removed `from ckan.views.user import before_request`
- **Line 3:** Added `current_user` import from `ckan.common`
- **Lines 19-24:** Added local `before_request()` function with `@user_info_blueprint.before_request` decorator
- **Reason:** CKAN 2.11.4 changed from shared before_request to per-blueprint pattern

### 4. ckanext-authz-service
**File:** `submodules/ckanext-authz-service/ckanext/authz_service/authzzie.py`

#### Change: Python 3.10 collections.abc compatibility
- **Lines 11-12:** Split imports:
  - `from collections import Iterable, defaultdict` →
  - `from collections.abc import Iterable`
  - `from collections import defaultdict`
- **Reason:** In Python 3.10, `Iterable` moved from `collections` to `collections.abc`

### 5. ckanext-ytp-request Model
**File:** `submodules/ckanext-ytp-request/ckanext/ytp_request/model.py`

#### Change: CKAN 2.11.4 model import
- **Line 10:** `from ckan.lib.base import model` → `import ckan.model as model`
- **Reason:** `model` is no longer exported from `ckan.lib.base` in CKAN 2.11.4

### 6. ckanext-unaids Setup
**File:** `submodules/ckanext-unaids/setup.py`

#### Change: Updated plugin entry point
- **Line 25:** `unaids_recline_view=ckanext.unaids.plugin:UNAIDSReclineView` →
  `unaids_datatables_view=ckanext.unaids.plugin:UNAIDSDataTablesView`
- **Reason:** Renamed view plugin to match code changes

### 7. ckanext-versions Model
**File:** `submodules/ckanext-versions/ckanext/versions/model.py`

#### Change: SQLAlchemy 1.4 compatibility
- **Lines 46-67:** Updated `create_tables()` and `tables_exist()` functions
- Use `inspector.has_table()` instead of deprecated `table.exists()`
- Pass engine to `table.create()` method
- Add None check for engine during early startup
- **Reason:** SQLAlchemy 1.4 deprecated table.exists() and requires explicit engine

### 8. ckanext-validation Model
**File:** `submodules/ckanext-validation/ckanext/validation/model.py`

#### Change: SQLAlchemy 1.4 compatibility
- **Lines 35-58:** Updated `create_tables()` and `tables_exist()` functions
- Use `inspector.has_table()` instead of deprecated `table.exists()`
- Pass engine to `table.create()` method
- Add None check for engine during early startup
- **Reason:** SQLAlchemy 1.4 deprecated table.exists() and requires explicit engine

### 9. ckanext-unaids Dataset Transfer Model
**File:** `submodules/ckanext-unaids/ckanext/unaids/dataset_transfer/model.py`

#### Change: SQLAlchemy 1.4 compatibility
- **Lines 31-53:** Updated `init_tables()` and `tables_exists()` functions
- Use `inspector.has_table()` instead of deprecated `table.exists()`
- Pass engine to `table.create()` method
- Add None check for engine during early startup
- **Reason:** SQLAlchemy 1.4 deprecated table.exists() and requires explicit engine

### 10. ckanext-pages Database Model
**File:** `submodules/ckanext-pages/ckanext/pages/db.py`

#### Change: SQLAlchemy 1.4 compatibility
- **Lines 27-39:** Updated `init_db()` function
- Use `inspector.has_table()` instead of deprecated `table.exists()`
- Pass engine to `table.create()` method
- Add None check for engine during early startup
- **Note:** Converted from git dependency to local submodule to apply this fix
- **Reason:** SQLAlchemy 1.4 deprecated table.exists() and requires explicit engine

### 11. ckanext-harvest Model
**File:** `submodules/ckanext-harvest/ckanext/harvest/model/__init__.py`

#### Change: SQLAlchemy 1.4 compatibility
- **Lines 44-76:** Updated `setup()` function
- Use `inspector.has_table()` instead of deprecated `table.exists()` for both `model.package_table` and `harvest_source_table`
- Pass engine to all `table.create()` method calls
- Add None check for engine during early startup
- Move inspector initialization to top of function for reuse
- **Reason:** SQLAlchemy 1.4 deprecated table.exists() and requires explicit engine

### 12. ckanext-restricted Logic
**File:** `submodules/ckanext-restricted/ckanext/restricted/logic.py`

#### Change: Handle AnonymousUser in CKAN 2.11.4 (Flask-Login compatibility)
- **Lines 33-46:** Updated `restricted_get_username_from_context()` function
- Check `is_authenticated` attribute before calling `as_dict()` on auth_user_obj
- In CKAN 2.11.4, `auth_user_obj` is always set (either User or AnonymousUser from Flask-Login)
- AnonymousUser doesn't have `as_dict()` method, causing AttributeError
- **Reason:** CKAN 2.11.4 uses Flask-Login which always provides a user object (authenticated or anonymous)

## Configuration Changes

### CKAN Configuration
**File:** `ckan/adx_config.ini`

#### Change: Updated plugin list (Lines 127-131)
**Removed plugins:**
- `unaids_recline_view` → replaced with `unaids_datatables_view`
- `recline_graph_view` (removed from CKAN 2.11.4)
- `recline_map_view` (removed from CKAN 2.11.4)
- `recline_grid_view` (removed from CKAN 2.11.4)
- `geo_view` (removed from CKAN 2.11.4)
- `geojson_view` (removed from CKAN 2.11.4)
- `pdf_view` (removed from CKAN 2.11.4)

**Added plugins:**
- `activity` (REQUIRED in CKAN 2.11.4 - provides activity stream actions like package_activity_list)
- `unaids_datatables_view` (custom view plugin)
- `datatables_view` (CKAN 2.11.4 core plugin)
- `webpage_view` (CKAN 2.11.4 core plugin)

#### Change: Updated default views (Line 205)
- **Before:** `geojson_view unaids_recline_view pdf_view image_view text_view`
- **After:** `unaids_datatables_view image_view text_view webpage_view`

#### Change: Added DataPusher API token configuration (Lines 274-280)
**Added settings:**
- `ckan.datapusher.callback_url_base = http://ckan:5000/`
- `ckan.datapusher.api_token = ${CKAN_DATAPUSHER_API_TOKEN}`
- **Reason:** CKAN 2.11.4 requires API token for DataPusher authentication

### Docker Configuration
**Files:** `docker-compose.yml`, `.env`, `ckan/bootstrap.sh`

#### Change: Added DataPusher API token environment variable
**docker-compose.yml:**
- Added `CKAN_DATAPUSHER_API_TOKEN=${CKAN_DATAPUSHER_API_TOKEN}` to both `ckan` and `supervisor` services
- **Reason:** Pass API token from environment to CKAN configuration

**.env:**
- Added `CKAN_DATAPUSHER_API_TOKEN` with development token
- **Reason:** Store API token for local development environment

#### Change: Fixed pipenv installation in bootstrap script
**ckan/bootstrap.sh (Line 28):**
- Removed `--skip-lock` flag from pipenv install command
- **Before:** `pipenv install --dev --python /usr/local/bin/python3 --skip-lock`
- **After:** `pipenv install --dev --python /usr/local/bin/python3`
- **Reason:** `--skip-lock` bypasses Pipfile.lock and can cause incomplete dependency installations. This was causing the `ModuleNotFoundError: No module named 'click.testing'` error even though click was in the Pipfile

## Git Submodule Changes

### Added ckanext-authz-service
```bash
git submodule add https://github.com/datopian/ckanext-authz-service.git submodules/ckanext-authz-service
cd submodules/ckanext-authz-service
git checkout bd4c80f55a714c1117a0e130d07463e383c494c7
```

### Added ckanext-pages
```bash
git submodule add https://github.com/ckan/ckanext-pages.git submodules/ckanext-pages
cd submodules/ckanext-pages
git checkout v0.5.2
# Applied SQLAlchemy 1.4 compatibility fix to ckanext/pages/db.py
```

## Issues Fixed

1. **setuptools compatibility:** Downgraded to 58.1.0 to fix `install_layout` attribute error
2. **Permission issues:** Cleaned egg-info directories with `find submodules/ckanext-* -name "*.egg-info" -type d -exec rm -rf {} +`
3. **Flask 3.x compatibility:** Updated all Flask imports and context handling
4. **Python 3.10 compatibility:** Fixed collections.abc imports
5. **CKAN 2.11.4 API changes:** Updated all changed/removed function imports
6. **View plugins:** Migrated from deprecated ReclineView to DataTablesView pattern
7. **pipenv --skip-lock issue:** Removed `--skip-lock` flag from bootstrap.sh causing incomplete dependency installations
8. **Missing async-timeout:** Added async-timeout==4.0.3 (required by redis 5.0.7 on Python 3.10)
9. **Missing numpy:** Added numpy>=1.21.0 (required by pandas>=1.4.2)

## Known Missing Features

The following plugins were removed and may need replacement extensions if functionality is required:
- **PDF viewing:** `pdf_view` - may need separate ckanext-pdfview extension
- **GeoJSON/Map viewing:** `geo_view`, `geojson_view` - may need separate mapping extension
- **Graph views:** `recline_graph_view` - functionality may need alternative
- **Error tracking:** `sentry` - ckanext-sentry was not installed, removed from config

## Testing Required

After these changes, the following should be tested:
1. CKAN starts without errors
2. All extensions load correctly
3. Data explorer/table views work for CSV, XLS, XLSX, TSV files
4. User authentication and authorization work correctly
5. File uploads work correctly
6. All API endpoints function properly
7. Dataset transfer functionality works
8. Validation extension works correctly

## Next Steps

1. Test CKAN startup and basic functionality
2. Identify any additional runtime errors
3. Test all custom extensions thoroughly
4. Consider installing additional view extensions for PDF/GeoJSON if needed
5. Update any custom code that may depend on removed features
6. Run full test suite once CKAN is stable

## Files Modified Summary

### Configuration Files
- `/Pipfile` - Dependency updates
- `ckan/adx_config.ini` - Plugin configuration updates and DataPusher API token
- `docker-compose.yml` - Added DataPusher API token environment variable
- `.env` - Added CKAN_DATAPUSHER_API_TOKEN
- `ckan/bootstrap.sh` - Removed `--skip-lock` flag from pipenv install

### Extension Code
- `submodules/ckanext-unaids/ckanext/unaids/plugin.py` - Multiple API updates
- `submodules/ckanext-unaids/ckanext/unaids/auth_logic.py` - Flask 3.x updates
- `submodules/ckanext-unaids/ckanext/unaids/blueprints/user_info_blueprint.py` - Blueprint pattern update
- `submodules/ckanext-unaids/ckanext/unaids/dataset_transfer/model.py` - SQLAlchemy 1.4 compatibility
- `submodules/ckanext-unaids/setup.py` - Entry point update
- `submodules/ckanext-authz-service/ckanext/authz_service/authzzie.py` - Python 3.10 fix
- `submodules/ckanext-ytp-request/ckanext/ytp_request/model.py` - CKAN 2.11.4 import fix
- `submodules/ckanext-versions/ckanext/versions/model.py` - SQLAlchemy 1.4 compatibility
- `submodules/ckanext-validation/ckanext/validation/model.py` - SQLAlchemy 1.4 compatibility
- `submodules/ckanext-pages/ckanext/pages/db.py` - SQLAlchemy 1.4 compatibility
- `submodules/ckanext-harvest/ckanext/harvest/model/__init__.py` - SQLAlchemy 1.4 compatibility
- `submodules/ckanext-blob-storage/setup.py` - Fixed version import

## Date
December 12, 2025
