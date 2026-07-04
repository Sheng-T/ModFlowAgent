# Modkit command-generation rules

## General
- Use documented subcommands. Never use bare `modkit extract <input> <output>`.
- Input/output are positional arguments, not `-i`/`--input`/`-o`/`--output`.
- Do not invent options not present in the modkit documentation.

## `modkit extract`

Valid forms:
1. `modkit extract read-stats <IN_BAM> <OUT_CSV> --mod-codes A:a`
2. `modkit extract full <IN_BAM> <OUT_TSV> [options]`
3. `modkit extract calls <IN_BAM> <OUT_TSV> [options]`

Forbidden options (all forms):
- `-i`, `--input`, `-o`, `--output`
- `--modification`, `--modified-bases`
- `--format`, `--output-format`
- `-m m6A`
- `--mod-codes` (only valid with `read-stats`)

Routing:
- Per-read counts or summary: `extract read-stats --mod-codes A:a`
- Per-read probability table: `extract full` (then `awk '$14 == "a"'` for m6A)
- Thresholded calls: `extract calls` (then `awk '$14 == "a"'` for m6A)

## `modkit summary`
- For overall modBAM summary only, not per-read m6A counts.
- Use stdout redirection or `--tsv` for output, not `-o`.
