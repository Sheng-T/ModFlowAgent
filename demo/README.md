# ModFlowAgent Demo Dataset

This directory contains a small ONT DNA 5mC test dataset for checking
ModFlowAgent workflow routing, validation, command generation, and optional
end-to-end execution.

Files:

- `5mC_test_200.pod5`: POD5 input subset.
- `all_5mers.fa`: matching reference FASTA.
- `all_5mers_5mC_sites.bed`: expected 5mC sites from the validation reference.
- `test_200_ids.txt`: read IDs used to generate the subset.

Source:

The subset was derived from the Oxford Nanopore modified-base validation data
hosted in ONT Open Datasets:

```text
s3://ont-open-data/modbase-validation_2024.10/
```

Example ModFlowAgent prompt:

```text
Profile 5mC methylation from ONT DNA POD5 test data at /absolute/path/to/ModFlowAgent/demo/5mC_test_200.pod5 and use reference /absolute/path/to/ModFlowAgent/demo/all_5mers.fa.
```
