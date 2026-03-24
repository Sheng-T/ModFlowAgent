# nf-core / Nextflow Notes

This repository supports running nf-core pipelines through Nextflow.

## Recommended baseline command

nextflow run nf-core/rnaseq -profile singularity --input samplesheet.csv --outdir results -resume -with-report -with-trace -with-timeline

## Supported pipelines in first release

- methylong (first workflow)
- rnaseq
- sarek
- ampliseq
- methylseq
- mag
- taxprofiler

## methylong focus

For long-read methylation calling on ONT/PacBio, prioritize `nf-core/methylong`.
Reference: [nf-core/methylong](https://github.com/nf-core/methylong)

## Required fields

- pipeline
- input
- outdir

## Runtime notes

- Prefer `-profile singularity` in HPC/containerized environments.
- Use `-resume` for retries and iterative tuning.
- Keep `work` directory stable for resumable execution.
