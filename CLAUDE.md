# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Sandbox/proof-of-concept code for the CDISC 360i program (see the official [360i repo](https://github.com/cdisc-org/360i)). The scripts here generate CDASH eCRF metadata (ODM XML v1.3.2 and v2.0, JSON, HTML CRF/annotated CRF renditions) from Excel-based CRF Specialization and Forms metadata. Treat everything here as sandbox/example code, not production infrastructure — there are no automated tests.

## Environment setup

- Python 3.12, virtual env in `venv/` (already created on this machine).
- Activate: `venv/Scripts/Activate` (PowerShell) — Windows-only environment (see `.vscode/launch.json`, path conventions).
- Install deps: `python -m pip install -r requirements.txt`
- **Required one-time setup**: `config/config.ini` does not ship in git-clean form for a new checkout; copy either `config/config-relative-paths.ini` or `config/config-absolute-paths.ini` to `config/config.ini` and edit paths. `config/config.py` (`AppSettings`) will hard-`exit()` if `config.ini` is missing.

## Common commands

Lint: `flake8` (config in `.flake8`: max-line-length 120, max-complexity 10, excludes `venv`/`build`/`dist`).

There is no test suite, build step, or package manager beyond pip/requirements.txt.

Generate a CRF (ODM v2.0):
```
python ./bc_dss2crf/cdash_poc_odm20.py -f VS1 -p vital_signs
```

Generate a CRF (ODM v1.3.2):
```
python ./bc_dss2crf/cdash_poc_odm132.py -f VS1 -p vital_signs
```

Override default metadata sources (both scripts support this):
```
python ./bc_dss2crf/cdash_poc_odm20.py -cp metadata/crf_qrs_kfss_draft.xlsx -cs CRF_QRS_KFSS -fp metadata/form_qrs_kfss_draft.xlsx -fs Forms-KFSS -f KFSS_01 -p kfss
```

Refresh CRF Specializations metadata from the COSMoS GitHub repo (saves a timestamped file under `metadata/`, does not overwrite the active file):
```
python ./bc_dss2crf/cdash_poc_odm20.py -ucm
```

`.vscode/launch.json` has pre-built debug configs (and two compounds, "Create all 132 CRFs" / "Create all 20 CRFs") for every sample form under `crf/` — useful as a reference for the full set of valid `--form`/`--prefix` pairs.

## Architecture

**Pipeline (both `bc_dss2crf/cdash_poc_odm132.py` and `cdash_poc_odm20.py` follow the same shape, one per ODM version):**

1. `create_df_from_excel()` — reads two Excel sources: CRF Specializations (item/codelist-level metadata) and Forms (form/section-level metadata), filters both to the requested `--form` ID, and inner-merges them on `crf_group_id`. Values are read with `keep_default_na=False`, so downstream code checks emptiness as `row["x"] != ""` rather than `pd.isna`. Excel sources may be local paths or `https://` URLs (fetched via `requests`).
2. `create_odm()` — walks the merged DataFrame row by row and builds an in-memory `odmlib` object tree: `ODM > Study > MetaDataVersion > ItemGroupDef (Form/Section/Concept) > ItemDef / CodeList`. OIDs for every element are generated deterministically by `create_oid(type, row)`, which is the single source of truth for the ID scheme (`IG.*` for item groups, `IT.*` for items, `CL.*` for codelists) — change this function, not ad hoc string formatting elsewhere, if the OID scheme needs to change.
3. The `main()` CLI (Click-based) wires it together: build the DataFrame → build the ODM object → `odm.write_xml()` / `odm.write_json()` → validate against the ODM XSD (`utilities.validate_odm_xml_file`, uses `xmlschema` via odmlib's `odm_parser`) → transform XML to HTML CRF and annotated CRF via Saxon-HE XSLT (`utilities.transform_xml_saxonche`, using `stylesheet/odm_1-3-2_transform.xsl` or `odm_2-0_transform.xsl`) → round-trip load the written XML back through `odmlib`'s `ODMLoader`/`XMLODMLoader` (sanity check) → package XML+JSON+HTML into a per-form zip under `crf/<FORM_ID>/` via `utilities.update_zip_file` (which does an in-place replace-in-zip rather than full rebuild-from-scratch when the zip already exists).
4. All outputs land in `crf/<FORM_ID>/` (one subfolder per form): `<prefix>_odmv{version}.xml`, `.json`, `_crf.html`, `_acrf.html` (annotated), and `_odm.zip` bundling all four.

**Config (`config/config.py`):** `AppSettings` loads `config/config.ini` via `configparser` and exposes flat attributes (`crf_path`, `odm132_schema`, `odm20_schema`, `odm132_stylesheet`, `odm20_stylesheet`, `metadata_path`, `crf_specializations_metadata_excel*`, `forms_metadata_excel*`). Scripts read config once at import time via `CFG()` and treat CLI options as overrides of these config defaults (Click `default=` is wired to the config value).

**`utilities/utils.py`:** shared helpers — `create_directory`, `validate_odm_xml_file` (schema validation, swallows `XMLSchemaChildrenValidationError` into a log, doesn't re-raise), `transform_xml_saxonche` (Saxon-HE-based XSLT transform, the one actually used by the CLI scripts), `transform_xml` (unused lxml-based XSLT alternative), `create_crf_html`/`write_html_doc`/`gen_codelist_items` (an alternate `dominate`-based HTML generator not used by the current CLI flow — the CLI scripts use the XSLT stylesheets instead), `update_zip_file`.

**`odmlib` dependency:** the scripts import the published `odmlib` PyPI package (pinned in `requirements.txt`).

**Data flow gotcha:** `crf_group_id` is the join key between CRF Specializations and Forms metadata, and also the change-detection key inside `create_odm()`'s main loop (a new `ItemGroupDef`/"Concept" is started each time `crf_group_id` changes) — the input Excel must be pre-sorted/grouped consistently by `form_section_order_number`, `bc_order_number`, `order_number` for this to produce correct groupings (this sort is done explicitly at the end of `create_df_from_excel()`).

**Static reference assets (not code, but relevant when scripts fail):** `schema/cdisc-odm1-3-2/` and `schema/cdisc-odm2-0/` hold the XSD schemas used for validation; `stylesheet/` holds the XSLT used for HTML rendition. `crf/<FORM>/` folders contain previously generated example outputs for each sample CDASH form (ADASCOGSC1, DEMOG_LZZT, EC1, ECG1, EQ5D02, IE_LZZT, KFSS_01, MH_LZZT, PR_LZZT, SC_LZZT, SIXMW1, SU_LZZT, VS1) — useful as known-good references when debugging a regression.
