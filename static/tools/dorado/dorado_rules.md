# Dorado command-generation rules

## Conceptual distinction
- **Basecalling model**: determines chemistry, pore/kit, speed/accuracy tier. Examples: `sup`, `hac`, `fast`, `dna_r10.4.1_e8.2_400bps_sup@v5.0.0`, `rna004_130bps_sup@v5.2.0`
- **Modification selector**: determines which base modifications are detected. Examples: `5mC_5hmC`, `5mCG_5hmCG`, `6mA`
- Do **not** treat modification names as the basecalling model.
- Do **not** invent combined model names unless explicitly documented.

## Example
** Style1: base model + `--modified-bases` (recommended)**
```bash
dorado basecaller <BASE_MODEL> --modified-bases <MOD_SELECTOR> <POD5> > output.bam
```
Example: `dorado basecaller sup --modified-bases 5mC_5hmC pod5/ > out.bam`

** Style2: base model (specify) + `--modified-bases-models`**
```bash
dorado basecaller <BASE_MODEL> --modified-bases-models <MOD_MODEL> <POD5> > output.bam
```
Example: `dorado basecaller dna_r10.4.1_e8.2_400bps_sup@v5.0.0 --modified-bases-models dna_r10.4.1_e8.2_400bps_sup@v5.0.0_5mC_5hmC@v3 pod5/ > out.bam`


## Forbidden patterns
- `--modification` or `--modifications` (must be `--modified-bases`)
- `dorado basecall` (must be `dorado basecaller`)
- **Mixing Style A and Style C**: Never use a full modification-aware model name TOGETHER with `--modified-bases`.
- `--modified-bases` and `--modified-bases-models` are mutually exclusive. Pick one: use `--modified-bases <MOD_SELECTOR>` or specify a model path via `--modified-bases-models <PATH>`, never both.
  Wrong: `dorado basecaller dna_...sup@v5.0.0_5mC_5hmC@v3 --modified-bases 5mC_5hmC pod5/ > out.bam`
- `--input` / `-i` / `--output` / `-o` (use positional POD5 input and stdout redirection)
- Inventing model names not in the registry.

## CpG vs non-CpG routing
- General 5mC/5hmC (no CpG mentioned): `--modified-bases 5mC_5hmC`
- CpG-specific: `--modified-bases 5mCG_5hmCG`
- 6mA: `--modified-bases 6mA`

## RNA vs DNA routing
- DNA: use DNA base models (`dna_r10.4.1_...`)
- RNA: use RNA base models (`rna004_130bps_...`)
- Do not use DNA models for RNA modification detection.

## RNA: m6A vs DRACH-context
- `m6A` (--modified-bases m6A or inosine_m6A): general N6-methyladenosine across all A positions
- `m6A_DRACH` (--modified-bases m6A_DRACH): restricts to DRACH motif (D=G/A/T, R=G/A, H=A/C/T). Use when only DRACH-context m6A is requested.
- Narrow RNA requests should use the narrowest compatible model when available: `pseU`, `m5C`, or the `inosine_m6A` joint model when the target is m6A or inosine.
- Combined RNA requests should use the documented combined model: `inosine_m6A_2OmeA`, `pseU_2OmeU`, or `m5C_2OmeC`.
- `2OmeG`: 2-O-methylguanosine
- Do not silently replace a single-modification request such as `pseU` with `pseU_2OmeU`; the combined model changes the biological target.

## Model naming
- Basecalling models follow: `dna_r10.4.1_e8.2_400bps_<tier>@v<version>`
- Tiers:
  - `sup`: super accuracy, highest accuracy
  - `hac`: high accuracy, balanced accuracy/speed
  - `fast`: fastest, lowest accuracy
- Modification models append: `_<mod>@v<version>` e.g. `_5mCG_5hmCG@v3`
