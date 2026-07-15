# Modcaller Profiles

This document explains how to write `modcaller_profiles.yaml` and `modcaller_profiles.local.yaml`.

## What A Modcaller Profile Does

A modcaller profile tells the local workflow system:

- which workflow this modcaller belongs to
- which modification types it supports
- how the runtime is prepared
- which ordered workflow steps are needed
- which generic postprocess steps should be appended afterward

The current implementation supports two layers:

1. `caller_steps`
   Ordered core steps for this modcaller.
2. `postprocess`
   Generic downstream steps appended after `caller_steps`.

`postprocess` is optional. Any postprocess key you do not write is treated as `false`.

## Important Current Limitation

The first version already supports profile discovery, availability filtering, runtime metadata, automatic modcaller resolution, dynamic step planning, and execution of `modcaller_run`.

The main limitation now is not "can it run", but "how much structure the platform understands after it runs":

- the platform can execute a custom `modcaller_run` command
- but it does not yet have per-tool parsers for every custom caller output
- and it does not yet support a user-configured post-analysis script hook after the caller finishes

So for the first version, custom callers are runnable, but downstream result interpretation may still need caller-specific follow-up work.

## File Locations

- Shared defaults: [modcaller_profiles.yaml](/E:/project/agent/modcaller_profiles.yaml:1)
- Local machine override: [modcaller_profiles.local.example.yaml](/E:/project/agent/modcaller_profiles.local.example.yaml:1)
- Your real local override should be: `modcaller_profiles.local.yaml`

The loader reads `modcaller_profiles.yaml` first and then deep-merges `modcaller_profiles.local.yaml` on top.

## Top-Level Structure

```yaml
version: 1

workflows:
  ont_dna:
    default_modification_type: 5mcpg
    fallback_modcaller: dorado
    modcallers:
      dorado:
        ...
```

## Supported Modification Types

### DNA

- `5mcpg`
- `5hmcg`
- `5mc`
- `5hmc`
- `4mc`
- `6ma`
- `none`

Aliases such as `cpg`, `5mcg`, and `5mcg5hmcg` are normalized to `5mcpg`.

### RNA

- `m6adrach`
- `m6a`
- `inosine`
- `2omea`
- `pseu`
- `m5c`
- `2omeg`
- `none`

Alias `drach` is normalized to `m6adrach`.

## Current ONT Scope

The current local ONT implementation is intentionally narrow:

- Dorado local workflows are treated as `R10.4.1 / E8.2 / 400bps`
- the built-in DNA base model is `dna_r10.4.1_e8.2_400bps_sup@v5.0.0`
- the DeepMod2 example also assumes an R10.4.1 model
- R9.x is not supported in this first version

So for now, if your data or your custom modcaller needs an R9-era model family, this local modcaller layer should be treated as unsupported.

## Workflow-Level Fields

### `default_modification_type`

Default modification type for the workflow when the user did not specify one.

### `fallback_modcaller`

The default modcaller name for this workflow.

Resolution rule:

- first find modcallers that support the requested modification type
- then sort by `priority`
- if none match, fall back to `fallback_modcaller` if it is available

## Modcaller-Level Fields

### `display_name`

Human-friendly label shown in the UI.

### `priority`

Higher priority wins when more than one available modcaller supports the same modification type.

### `runtime`

Execution environment description.

Supported forms:

```yaml
runtime:
  type: tool
  tool_name: dorado
```

```yaml
runtime:
  type: conda
  env_name: deepmod2
```

```yaml
runtime:
  type: singularity
  image: /data/images/my_tool.sif
```

```yaml
runtime:
  type: script
  script_path: /data/tools/run_wrapper.sh
```

### `workdir`

Optional working directory. Use this when the tool was cloned from Git and must run inside that directory.

Typical example:

```yaml
workdir: /data/tools/DeepMod2
```

### `entrypoint`

Optional executable prefix for the command author.

Examples:

```yaml
entrypoint: dorado
```

```yaml
entrypoint: python deepmod2
```

```yaml
entrypoint: python /data/tools/DeepMod2/deepmod2
```

Use `entrypoint` when the command is not on `PATH` or must be launched via Python.

### `modcaller_pre`

Optional hook executed before `modcaller_run` command rendering.

Use this when you want to:

- derive caller-specific placeholders from base placeholders such as `{device}`
- emit extra shell commands before the main modcaller command
- validate prerequisites for one custom caller without touching the global workflow code

Structure:

```yaml
modcaller_pre:
  mode: python | bash
  code: |
  script_path: /path/to/script
  required: false
```

Rules:

- `mode` supports `python` and `bash`
- use either `code` or `script_path`
- if `required: true`, hook failure blocks this modcaller command with a readable error
- if `required: false`, hook failure only emits a warning and continues

### `modcaller_post`

Optional hook executed after the main `modcaller_run` command is rendered.

Use this when you want to:

- append a caller-specific cleanup command
- append an extra result-normalization step
- keep that logic local to one modcaller profile

It uses the same structure as `modcaller_pre`.

### Base Placeholders For Hooks

The system-level device input is expected to look like:

- `cpu`
- `cuda:0`
- `cuda:0,1`

Base placeholders available to hooks:

- `{device}`: resolved device string such as `cpu` or `cuda:0`
- `{device_gpu_count}`: GPU count such as `1` or `2`
- `{device_gpu_pool}`: GPU ids separated by spaces, such as `0` or `0 1`
- `{device_first_gpu}`: first GPU id such as `0`
- `{device_is_gpu}`: `true` or `false`
- `{device_gpu_ids_csv}`: GPU ids separated by commas, such as `0` or `0,1`

### Hook Code Behaviour

When `mode: python`:

- the code is rendered with base placeholders first
- it must assign a dict to `result`

The returned dict can contain:

- arbitrary key/value pairs, which become modcaller-only placeholders
- `command_prefix`
- `command_suffix`

Example:

```yaml
modcaller_pre:
  mode: python
  required: true
  code: |
    device = "{device}"
    if not device.startswith("cuda:"):
        raise ValueError("GPU required")
    gpu_ids = [x for x in device.split(":", 1)[1].split(",") if x]
    result = {
        "device_gpu_count": str(len(gpu_ids)),
        "device_gpu_pool": " ".join(gpu_ids),
        "device_first_gpu": gpu_ids[0],
    }
```

When `mode: bash`:

- the code is rendered with base placeholders first
- it receives environment variables:
  - `DEVICE`
  - `DEVICE_GPU_COUNT`
  - `DEVICE_GPU_POOL`
  - `DEVICE_FIRST_GPU`
  - `DEVICE_IS_GPU`
  - `DEVICE_GPU_IDS_CSV`
- it must print a JSON object to stdout

Example:

```yaml
modcaller_pre:
  mode: bash
  code: |
    python - <<'PY'
    import json, os
    gpu_pool = os.environ["DEVICE_GPU_POOL"]
    print(json.dumps({
        "device_gpu_count": os.environ["DEVICE_GPU_COUNT"],
        "device_gpu_pool": gpu_pool,
        "device_first_gpu": gpu_pool.split()[0] if gpu_pool else "",
    }))
    PY
```

### Scope Of Hook Placeholders

The placeholders returned by `modcaller_pre` are only available inside the `modcaller_run` rendering stage.

That means:

- they do not affect Dorado / samtools / modkit / pbmm2 steps
- they can be used multiple times inside one `command_example`
- if your `command_example` contains multiple chained commands, the hook-generated placeholders are available to all of them

### `supported_modification_types`

Explicit list of modification types this modcaller supports.

Example:

```yaml
supported_modification_types:
  - 5mcpg
  - 5mc
```

### `caller_steps`

Ordered list of symbolic workflow steps.

This is the most important rule in the current version:

`caller_steps` is not a place to paste raw shell commands.

Current built-in step names:

- `dorado_download`
- `dorado_basecaller`
- `samtools_sort`
- `samtools_index`
- `samtools_faidx`
- `modcaller_run`
- `modkit_pileup`
- `modkit_extract`

`modcaller_run` is the hook for a fully custom caller command.

### `postprocess`

Booleans for generic downstream steps appended after `caller_steps`.

Example:

```yaml
postprocess:
  samtools_sort: true
  samtools_index: true
  samtools_faidx: true
  modkit_pileup: true
  modkit_extract: true
```

Semantics:

- `postprocess` always runs after `caller_steps`
- omitted keys default to `false`
- duplicate steps are suppressed automatically
- `dorado_basecaller` automatically implies `samtools_sort` and `samtools_index`
- if a common step must happen before the custom modcaller, put it in `caller_steps`
- if you moved a step into `caller_steps`, set the same `postprocess` flag to `false` when you do not want it added again later

This means:

- Dorado-only ONT workflows do not need to repeat `samtools_sort` or `samtools_index` in the profile
- DeepMod2-like workflows can rely on the automatic Dorado-to-samtools chain and only add `modcaller_run`

## TODO: User Post-Analysis Scripts

This is intentionally not implemented in the first version.

The future direction is:

- let users optionally register a post-analysis script per modcaller
- run it after the main caller output is produced
- let that script generate caller-specific summaries, plots, or normalized output tables

For now, treat this as a TODO rather than part of the stable schema.

## Does Dorado Still Get `--modified-bases-models`?

Current rule after the latest fix:

- if the selected modcaller is `dorado`, `dorado_basecaller` will attach `--modified-bases-models` when the chosen modification type maps to a Dorado mod model
- if the selected modcaller is not `dorado`, `dorado_basecaller` is treated as plain upstream basecalling and will not attach `--modified-bases-models`
- if `modification_type = none`, Dorado also behaves as plain basecalling

This avoids a DeepMod2-style profile accidentally inheriting Dorado modified-base calling when Dorado is only being used to create the upstream BAM.

## Example 1: ONT DNA With Dorado

```yaml
workflows:
  ont_dna:
    default_modification_type: 5mcpg
    fallback_modcaller: dorado
    modcallers:
      dorado:
        display_name: Dorado
        priority: 100
        runtime:
          type: tool
          tool_name: dorado
        entrypoint: dorado
        workdir: ""
        supported_modification_types:
          - 5mcpg
          - 5hmcg
          - 5mc
          - 5hmc
          - 4mc
          - 6ma
          - none
        caller_steps:
          - dorado_download
          - dorado_basecaller
        postprocess:
          samtools_faidx: true
          modkit_pileup: true
          modkit_extract: true
```

This is the cleanest case:

- Dorado does the basecalling and mod calling itself
- `samtools_sort` and `samtools_index` are platform defaults after `dorado_basecaller`
- `modkit_*` stays as generic downstream work
- nothing needs to be repeated in `caller_steps`

## Example 2: ONT RNA With Dorado

```yaml
workflows:
  ont_rna:
    default_modification_type: m6a
    fallback_modcaller: dorado
    modcallers:
      dorado:
        display_name: Dorado
        priority: 100
        runtime:
          type: tool
          tool_name: dorado
        entrypoint: dorado
        workdir: ""
        supported_modification_types:
          - m6adrach
          - m6a
          - inosine
          - 2omea
          - pseu
          - m5c
          - 2omeg
          - none
        caller_steps:
          - dorado_download
          - dorado_basecaller
        postprocess:
          samtools_faidx: true
          modkit_pileup: true
          modkit_extract: true
```

## Example 3: DeepMod2 As A Target Profile

This is the corrected shape for a DeepMod2 profile if Dorado is only used to create the upstream BAM and DeepMod2 performs the final mod-calling step.

```yaml
workflows:
  ont_dna:
    modcallers:
      deepmod2:
        display_name: DeepMod2
        priority: 90
        runtime:
          type: conda
          env_name: deepmod2
        workdir: /data/tools/DeepMod2
        entrypoint: python deepmod2
        supported_modification_types:
          - 5mcpg
        caller_steps:
          - dorado_download
          - dorado_basecaller
          - modcaller_run
        command_example: |
          {entrypoint} detect \
            --bam {sorted_bam} \
            --input {data_file} \
            --model bilstm_r10.4.1_5khz_v5.0 \
            --file_type pod5 \
            --threads {threads} \
            --ref {reference} \
            --output {step_dir}/deepmod2 \
            --seq_type dna
```

Why this is the corrected shape:

- the raw DeepMod2 shell command is documented in `command_example`, not pasted into `caller_steps`
- `samtools_sort` and `samtools_index` do not need to be listed because the platform adds them after `dorado_basecaller`
- `postprocess` is omitted entirely, so no extra downstream branch is appended

## Example 4: DeepRM For ONT RNA

```yaml
workflows:
  ont_rna:
    modcallers:
      deeprm:
        display_name: DeepRM
        priority: 120
        runtime:
          type: conda
          env_name: deeprm
        workdir: ""
        entrypoint: deeprm
        modcaller_pre:
          mode: python
          required: true
          code: |
            device = "{device}"
            if not device.startswith("cuda:"):
                raise ValueError("DeepRM requires a CUDA device")
            gpu_ids = [x for x in device.split(":", 1)[1].split(",") if x]
            result = {
                "device_gpu_count": str(len(gpu_ids)),
                "device_gpu_pool": " ".join(gpu_ids),
                "device_first_gpu": gpu_ids[0],
            }
        supported_modification_types:
          - m6a
        caller_steps:
          - dorado_download
          - dorado_basecaller
          - modcaller_run
        command_example: |
          mkdir -p "{step_dir}/prep" "{step_dir}/pred" && \
          {entrypoint} call prep \
            -p "{data_file}" \
            -b "{sorted_bam}" \
            -o "{step_dir}/prep" \
            --thread {threads} \
            --chunk 5000 && \
          {entrypoint} call run \
            -i "{step_dir}/prep" \
            -b "{sorted_bam}" \
            -o "{step_dir}/pred" \
            -s 3000 \
            -t 1 \
            -f 10 \
            --gpu {device_gpu_count} \
            --gpu-pool {device_gpu_pool}
```

This is the recommended first DeepRM profile shape today.

Notes:

- `m6a` is the workflow-level modification type currently exposed for this caller
- `sorted_bam` comes from `dorado_basecaller -> samtools_sort`
- the two DeepRM subcommands are chained inside one `modcaller_run`
- `modcaller_pre` converts the UI `device` field into the placeholders DeepRM needs

## PacBio Placeholder Planning

The current repository already contains useful guidance in the local `methylong` docs:

- PacBio general workflow is documented as `modcalling -> alignment -> methylation pileup`, with `ccsmeth` as a modcaller option and `pbmm2` as the default aligner in [methylong_doc.md](/E:/project/agent/static/workflows/methylong/methylong_doc.md:28).
- `pb-CpG-tools` is documented there as the PacBio pileup step after alignment in [methylong_doc.md](/E:/project/agent/static/workflows/methylong/methylong_doc.md:32).
- The same docs describe both `jasmine` and `ccsmeth` as PacBio modcallers that write MM/ML tags into BAM in [methylong_doc.md](/E:/project/agent/static/workflows/methylong/methylong_doc.md:270).

From that, the current placeholder plan is:

- `pb-CpG-tools`
  - not a user-facing modcaller
  - used as the PacBio CpG pileup/downstream step after `jasmine` alignment
  - rationale: this is really a pileup/scoring-style downstream tool, not the first PacBio modcalling step

- `ccsmeth`
  - user-facing modification: `5mcpg`
  - planned order: `modcaller_run -> pbmm2_align -> samtools_index -> samtools_faidx -> pb-CpG-tools -> ccsmeth call_freqb`
  - rationale: `methylong` uses `ccsmeth call_mods` for modBAM generation and additionally runs `ccsmeth call_freqb` after alignment

- `jasmine`
  - user-facing modifications: `5mcpg`, `5mc`, `6ma`
  - planned order: `modcaller_run -> pbmm2_align -> samtools_index`
  - rationale: use one stable PacBio modBAM-producing caller path for the currently exposed local placeholder workflow

This PacBio section is intentionally marked as placeholder planning, not as a completed executor contract.

## Placeholder Meanings For `command_example`

These placeholders are the intended vocabulary for profile documentation:

- `{entrypoint}`: usually from `profile.entrypoint`
- `{data_file}`: the raw data file from the local workflow form
- `{reference}`: reference FASTA from the local workflow form
- `{threads}`: thread count chosen by the platform
- `{device}`: normalized device string such as `cpu` or `cuda:0`
- `{run_dir}`: run root directory
- `{step_dir}`: current step output directory
- `{sorted_bam}`: output from an earlier `samtools_sort` step
- `{calls_bam}`: output from an earlier `dorado_basecaller` step

At the moment this placeholder vocabulary is mostly for human-readable examples and for the upcoming generic custom-command executor.

## Availability Filtering

A modcaller is hidden from automatic resolution if its runtime is not available.

Current checks include:

- conda environment exists
- singularity image exists
- tool runtime has an image or a `TOOL_EXEC_ENV` fallback
- script runtime path exists
- `workdir` exists when configured
- host entrypoint exists when required

So if a user writes:

```yaml
runtime:
  type: conda
  env_name: deepmod2
```

but the `deepmod2` environment does not exist locally, that modcaller will not be auto-selected.

## Recommended Authoring Rules

- Keep `caller_steps` symbolic and ordered.
- Put only truly generic downstream work into `postprocess`.
- If a `postprocess` key is not needed, omit it instead of writing `false`.
- If a step is required before your custom modcaller, move it into `caller_steps`.
- Use `workdir` when the tool was cloned from Git and is not globally installed.
- Use `entrypoint` when the command is not directly on `PATH`.
- Disable `postprocess.modkit_*` unless the final output is really meant to enter the modkit branch.
- Use `none` only for plain basecalling with no modification downstream.
