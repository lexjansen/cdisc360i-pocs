# cdisc360i-poc

![under development](https://img.shields.io/badge/under-development-blue)

Lex Jansen's public Github repository for CDISC 360i Proof of Concepts.

This project consists of example programs to try out steps in the 360i pipeline.

Here's the official [CDISC 360i repository](https://github.com/cdisc-org/360i)

## Introduction

These programs are designed to function as command-line applications that can run as standalone applications or can be chained together to function as a pipeline of sorts. Everything in this repo should be considered sandbox development work in support of the 360i program.

## Overview of folders

**bc_dss2crf**:

- cdash_poc_odm20.py: script to create ODM XML v2.0 XML, CRFs in HTML, and annotated CRFs in HTML.
- cdash_poc_odm132.py: script to create ODM XML v1.3.2 XML, CRFs in HTML, and annotated CRFs in HTML.

**config**:

- config.py loads the configuration settings
- config-relative-paths.ini, config-absolute-paths.ini: templates for configuration settings. Either copy config-relative-paths.ini to config.ini, or copy config-absolute-paths.ini to config.ini, and edit the paths to match your environment.

**crf**: Output folder for generated CRF files. Every form gets it's own subfolder.

**metadata**:  Metadata used by the scripts.

- cdisc_collection_dataset_specializations_draft.xlsx: Collection Dataset Specialization metadata. Generated from the draft CDISC Collection Dataset Specializations (see: [https://github.com/cdisc-org/COSMoS/tree/main/curation/draft](https://github.com/cdisc-org/COSMoS/tree/main/curation/draft)).
- cdisc_collection_forms.xlsx: Forms metadata.

**odmlib**:

- Updates to the odmlib library to support the final ODM v2.0 schema. These updates are intendede to be merged with the odmlib library at [https://github.com/swhume/odmlib](https://github.com/swhume/odmlib).

**schema**:

- XML Schema files to validate ODM XML v1.3.2 and v2.0 files.

**stylesheet**:

- XSLT stylesheets to convert ODM XML CRF files to HTML CRFs and annotated CRFs.

**utilities**:

- Utilities used by scripts to create directories, validate XML, convert XML to HTML.

## Environment Setup

- Create a virtual environment:
`python -m venv <virtual-env-name>`

- Activate the environment:  
Linux:
`<virtual-env-name>/bin/activate`  
Windows:
`<virtual-env-name>/Scripts/Activate`

- Install requirements:
`pip install -r requirements.txt`

## Running the Examples

The following command-line example uses Collection Dataset Specializations and Forms metadata (VS1) to generate an ODM v2.0 XML CRF, and HTML renditions of the CRF and annotated CRF in the **crf/VS1** folder.:

```python
python .\bc_dss2crf\cdash_poc_odm20.py -f VS1
```

The following command-line example does the same, but then for ODM v 1.3.2:

```python
python .\bc_dss2crf\cdash_poc_odm132.py -f VS1
```

## License

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
This project uses the [MIT](http://www.opensource.org/licenses/MIT "The MIT License | Open Source Initiative")
license (see [`LICENSE`](LICENSE)) for code and scripts.
