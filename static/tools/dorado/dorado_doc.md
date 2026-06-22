# Dorado Document

## 文档章节: Dorado Correct - Dorado Documentation

# Dorado Correct

Warning

**Dorado`correct` is not yet supported on Nvidia DGX Spark. Support for Dorado `correct` on Nvidia DGX Spark will be added in a future release.**

Should I use `correct` or `polish`?

[See here](../polish/#should-i-use-correct-or-polish)

Dorado supports single-read error correction with the integration of the [HERRO](https://github.com/lbcb-sci/herro) algorithm in Dorado `correct`. `dorado correct` is essentially a reimplementation of the HERRO algorithm.

## HERRO Algorithm

Citation

Telomere-to-telomere phased genome assembly using error-corrected Simplex nanopore reads

Dominik StanojeviÄ, Dehui Lin, Paola Florez de Sessions, Mile Å ikiÄ bioRxiv 2024.05.18.594796;

HERRO uses all-vs-all alignment followed by haplotype-aware correction using a deep learning model to achieve higher single-read accuracies. The corrected reads are primarily useful for generating de novo assemblies of diploid organisms.

The original paper containing implementation details can be downloaded from [bioRxiv](https://www.biorxiv.org/content/10.1101/2024.05.18.594796v1).

## Quick start

To run Dorado `correct`, pass in a FASTQ or a [bgz](https://www.htslib.org/doc/bgzip.html) compressed FASTQ.gz file. Note that `bgzip` needs to be used for compression instead of the vanilla `gzip` because Htslib does not support FASTA/FASTQ with plain `gzip`. Dorado will perform read correction on this dataset after automatically downloading the required [HERRO](https://github.com/lbcb-sci/herro) model.
    
    
    dorado correct reads.fastq > corrected_reads.fasta
    

You may pre-download the [HERRO](https://github.com/lbcb-sci/herro) model if required:
    
    
    dorado download --model herro-v1
    

and select it as shown:
    
    
    dorado correct reads.fastq --model-path herro-v1 > corrected_reads.fasta
    

Important

Currently there is only one Dorado `correct` model which is `herro-v1` for the `r10.4` run condition.

## Usage

Dorado `correct` supports FASTQ(.gz) as the input and generates a FASTA file as output.

An index file is generated for the input FASTQ file in the same folder unless one is already present. Please ensure that the folder with the input file is writeable by the Dorado process and has sufficient disk space (no more than 10GB should be necessary for a whole genome dataset).

To correct reads, run:
    
    
    dorado correct reads.fastq > corrected_reads.fasta
    

All required model weights are downloaded automatically by Dorado. However, the weights can also be pre-downloaded and passed via command line in case of offline execution. To do so, run:
    
    
    dorado download --model herro-v1
    dorado correct --model-path herro-v1 reads.fq.gz > corrected_reads.fasta
    

### Separate mapping and inference

Dorado `correct` can run mapping (CPU-only stage) and inference (GPU-intensive stage) individually. This enables separation of the CPU and GPU heavy stages into individual steps which can even be run on different nodes with appropriate compute characteristics. For example:
    
    
    dorado correct reads.fastq --to-paf > overlaps.paf
    dorado correct reads.fastq --from-paf overlaps.paf > corrected_reads.fasta
    

Gzipped PAF is currently not supported for the `--from-paf` option.

### Resume

If a run was stopped or has failed, Dorado `correct` provides functionality to resume from where the previous run stopped.

The `--resume-from` argument takes a list of previously corrected reads provided via a `.fai` index from the outputs of the previous run. The reads that have been previously processed are then skipped when resuming.

To generate the `.fai` file from a previous output from Dorado `correct` use:
    
    
    # corrected_reads.fasta is the output from the previously interrupted run.
    mv corrected_reads.fasta corrected_reads.res.fasta
    samtools faidx corrected_reads.res.fasta
    

And to continue Dorado `correct` using `--resume-from` use:
    
    
    dorado correct reads.fastq --resume-from corrected_reads.res.fasta.fai > corrected_reads.fasta
    

The input file format for the `--resume-from` feature can be any plain text file where the first whitespace-delimited column (or a full row) consists of sequence names to skip, one per row.

## Specifying resources

Dorado correct will automatically select all available compute resources to perform error correction.

To specify resources manually use:

  * `-x / --device` to specify specific GPU resources (if available).
  * `--threads` to set the maximum number of threads to be used during correction.
  * `--infer-threads` to set the number of threads used per-device for inference.

    
    
    dorado correct reads.fastq --device cuda:0 --threads 64 --infer-threads 1 > corrected_reads.fasta
    

The error correction tool is both compute and memory intensive.

As a result, it is best run on a system with:

  * multiple high performance CPU cores ( > 64 cores)
  * large system memory ( > 256GB)
  * a modern GPU with a large VRAM ( > 32GB)

#### HPC support

Dorado `correct` now also provides a feature to enable simpler distributed computation. It is now possible to run a single block of the input target reads file, specified by the block ID. This enables granularization of the correction process, making it possible to easily utilise distributed HPC architectures.

For example, this is now possible: 
    
    
    # Determine the number of input target blocks.
    num_blocks=$(dorado correct in.fastq --compute-num-blocks)
    
    # For every block, run correction of those target reads.
    for ((i=0; i<${num_blocks}; i++)); do
        dorado correct in.fastq --run-block-id ${i} > out.block_${i}.fasta
    done
    
    # Optionally, concatenate the corrected reads.
    cat out.block_*.fasta > out.all.fasta
    

On an HPC system, individual blocks can simply be submitted to the cluster management system. For example: 
    
    
    # Determine the number of input target blocks.
    num_blocks=$(dorado correct in.fastq --compute-num-blocks)
    
    # For every block, run correction of those target reads.
    for ((i=0; i<${num_blocks}; i++)); do
        qsub <options> dorado correct in.fastq --run-block-id ${i} > out.block_${i}.fasta
    done
    

In case that the available HPC nodes do not have GPUs available, the CPU power of those nodes can still be leveraged for overlap computation - it is possible to combine a blocked run with the `--to-paf` option. Inference stage can then be run afterwards on another node with GPU devices from the generated PAF and the `--from-paf` option.

## Frequently asked questions / Troubleshooting

### High memory consumption

In case the process is consuming too much memory (RAM) for your system, try running it with a smaller index size. For example:
    
    
    dorado correct reads.fastq --index-size 4G > corrected_reads.fasta
    

The auto-computed inference batch size may still be too high for your system. If you are experiencing warnings/errors regarding available GPU memory, try reducing the batch size by selecting it manually. For example:
    
    
    dorado correct reads.fastq --batch-size <number> > corrected_reads.fasta
    

### Missing reads

In case your output FASTA file contains a very low amount of corrected reads compared to the input, please check the following:

  1. The input dataset has average read length >=10kbp.
     * Dorado Correct is designed for long reads, and it will not work on short libraries.
  2. Input coverage is reasonable, preferably >=30x.
  3. Check the average base qualities of the input dataset. Dorado Correct expects accurate inputs for both mapping and inference.

### Some corrected reads have a suffix of type `:0`, `:1`, etc.

When a region of an input read has low/zero coverage, Dorado `correct` (and HERRO) will split it in this region and produce one or more chunks for that read.

If this occurs, the corrected chunks will have a suffix of type `:<number>` added to the header, where `<number>` is the ordinal ID of this chunk along the input read.

## CLI reference

Here's a slightly re-formatted output from the Dorado `correct` subcommand for reference.

Info

Please check the --help output of your own installation of dorado as this page may be outdated and argument defaults have been omitted as they are platform specific.
    
    
    > dorado correct --help
    
    Positional arguments:
      reads             Path to a file with reads to correct in FASTQ format.
    
    Optional arguments:
      -h, --help        shows help message and exits
      -v, --verbose     [may be repeated]
    
    Resources arguments:
      -x, --device      Specify CPU or GPU device
      -t, --threads     Number of threads for processing. Default uses all available threads.
      --infer-threads   Number of threads per device.
    
    Input/output arguments:
      -m, --model-path  Path to correction model folder.
      -p, --from-paf    Path to a PAF file with alignments. Skips alignment computation.
      --to-paf          Generate PAF alignments and skip consensus.
      --resume-from     Resume a previously interrupted run.
                            Requires a path to a file where sequence headers are stored in the first column
                            (whitespace delimited), one per row.
    
    Advanced arguments:
      -b, --batch-size  Batch size for inference.
      -i, --index-size  Size of index for mapping and alignment. Decrease index size to lower memory footprint.
    

Back to top 

## 文档章节: Dorado Polish - Dorado Documentation

# Dorado Polish

Should I use `correct` or `polish`?

See here

Should I use `variant` or `polish`?

[See here](../variant/#should-i-use-variant-or-polish)

Dorado `polish` is a high accuracy assembly polishing tool which outperforms similar tools for most ONT-based assemblies.

It takes as input a draft assembly produced by a tool such as [Hifiasm](https://github.com/chhylp123/hifiasm) or [Flye](https://github.com/mikolmogorov/Flye) and aligned reads, and outputs an updated version of the assembly.

Additionally, Dorado `polish` can output a VCF file containing records for all variants discovered during polishing, or a gVCF file containing records for all locations in the input draft sequences.

Note that Dorado `polish` is a **haploid** polishing tool and does _not_ implement any sort of phasing internally. It will take input alignment data _as is_ and run it through the polishing model to produce the consensus sequences. For more information, please take a look at this section.

## Quick Start

### Consensus
    
    
    # Align unmapped reads to a reference using dorado aligner, sort and index
    dorado aligner <draft.fasta> <unmapped_reads.bam> | samtools sort --threads <num_threads> > aligned_reads.bam
    samtools index aligned_reads.bam
    
    # Call consensus
    dorado polish <aligned_reads.bam> <draft.fasta> > polished_assembly.fasta
    

In the above example, `<aligned_reads>` is a BAM of reads aligned to a draft by Dorado `aligner` and `<draft>` is a FASTA or FASTQ file containing the draft assembly. The draft can be uncompressed or compressed with `bgzip`.

### Consensus from a FASTQ input instead of BAM

This feature supports only FASTQ files with HTS-style tags in the header and will not work for the old MinKnow style FASTQ files.

Here is a full example:
    
    
    # Align reads to a reference using dorado aligner, sort and index
    dorado aligner <draft.fasta> <reads.fastq> | samtools sort --threads <num_threads> > aligned_reads.bam
    samtools index aligned_reads.bam
    
    # Call consensus
    dorado polish <aligned_reads.bam> <draft.fasta> > polished_assembly.fasta
    

### Consensus on bacterial genomes
    
    
    dorado polish <aligned_reads> <draft> --bacteria > polished_assembly.fasta
    

This will automatically resolve a suitable bacterial polishing model, if one exits for the input data type.

### Variant calling
    
    
    dorado polish <aligned_reads> <draft> --vcf > polished_assembly.vcf
    dorado polish <aligned_reads> <draft> --gvcf > polished_assembly.all.vcf
    

Specifying `--vcf` or `--gvcf` flags will output a VCF file to stdout instead of the consensus sequences.

### Output to a folder
    
    
    dorado polish <aligned_reads> <draft> -o <output_dir>
    

Specifying `-o` will write multiple files to a given output directory (and create the directory if it doesn't exist):

  * Consensus file: `<output_dir>/consensus.fasta` by default, or `<output_dir>/consensus.fastq` if `--qualities` is specified.
  * VCF file: `<output_dir>/variants.vcf` which contains only variant calls by default, or records for all positions if `--gvcf` is specified.

## Resources

Dorado `polish` will automatically select the compute resources to perform polishing. It can use one or more GPU devices, or the CPU, to call consensus.

To specify resources manually use:

  * `-x / --device` \- to specify specific GPU resources (if available).
  * `--threads` \- to set the maximum number of threads to be used for everything but the inference.
  * `--infer-threads` \- to set the number of CPU threads for inference (when "--device cpu" is used).
  * `--batchsize` \- batch size for inference, important to control memory usage on the GPUs. Automatically computed by default (`--batchsize 0`).

Example:
    
    
    dorado polish reads_to_draft.bam draft.fasta --device cuda:0 --threads 24 > consensus.fasta
    

## Models

Dorado `polish` auto-resolves the polishing model based on the input BAM file. The BAM file needs to contain the `@RG` headers with the basecaller model name specified, otherwise the model will not be resolved. If the input BAM records contain move tables, an appropriate move-aware polishing model will be selected.

Once the model is resolved, Dorado `polish` will either download it or look it up in the models-directory if specified.

For example:
    
    
    dorado polish reads_to_draft.bam draft.fasta > consensus.fasta
    

will find the compatible model based on the input BAM file and download it to a temporary folder.

When `--models-directory` is specified, the resolved polishing model will first be looked up in the models-directory, and only downloaded if the model does not exist. The specified models-directory must exist. Example:
    
    
    mkdir -p models
    dorado polish --models-directory models reads_to_draft.bam draft.fasta > consensus.fasta
    

More information about the `--models-directory` can be found in this section

If there are multiple read groups in the input dataset which were generated using different basecaller models, Dorado `polish` will report an error and stop execution.

### Move Table Aware Models

Significantly more accurate assemblies can be produced by giving the polishing model access to additional information about the underlying signal for each read. For more information, see this section from the [NCM 2024](https://youtu.be/IB6DmU40NIU?t=377) secondary analysis update.

Dorado `polish` includes models which can use the move table to get temporal information about each read. These models will be selected automatically if the corresponding `mv` tag is in the input BAM. To do this, pass the `--emit-moves` tag to Dorado `basecaller` when basecalling. To check if a BAM contains the move table for reads, use samtools:
    
    
    samtools view --keep-tag "mv" -c <reads_to_draft_bam>
    

The output should be equal to the total number of reads in the bam (`samtools view -c <reads_to_draft_bam>`).

If move tables are not available in the BAM, then the non-move table-aware model will be automatically selected.

## FAQ

### How is Dorado `polish` different from Medaka?

[Medaka](https://github.com/nanoporetech/medaka) and Dorado `polish` are both assembly polishing tools. They accept the same input formats and produce the same output formats, and in principle they could run the same polishing model to produce equivalent results. However, Dorado `polish` is optimised for higher performance, and can support more accurate models with more computationally intensive architectures. For use cases in low-resource settings (small genomes such as bacteria with CPUs only available) Medaka remains the recommended tool. For large genomes or in other instances where speed is important, we suggest trying Dorado `polish`.

### Should I use `correct` or `polish`?

Dorado `polish` is a post-assembly tool and it is intended to improve the accuracy of pre-existing assemblies. Dorado `correct` conversely is a pre-assembly tool and is intended to improve the contiguity of an assembly by improving the fidelity of reads used to create it.

### How do I go from raw POD5 data to a polished T2T assembly?

Here is a high-level example workflow:
    
    
    # Generate basecalled data with dorado basecaller
    dorado basecaller <model> pod5s/ --emit-moves > calls.bam
    samtools fastq calls.bam > calls.fastq
    
    # Apply dorado correct to a set of reads that can be used as input in an assembly program.
    dorado correct calls.fastq > corrected.fasta
    
    # Assemble the genome using those corrected reads
    <some_assembler> --input corrected.fasta > draft_assembly.fasta
    
    # Align original calls to the draft assembly
    dorado aligner draft_assembly.fasta calls.bam > aligned_calls.bam
    
    # Run dorado polish using the raw reads aligned to the draft assembly
    dorado polish aligned_calls.bam draft_assembly.fasta > polished_assembly.fasta
    

### Polishing diploid/polyploid assemblies

Dorado `polish` is a **haploid** polishing tool and does _not_ implement any sort of phasing internally. It will take input alignment data _as is_ and run it through the polishing model to produce the consensus sequences.

In order to polish diploid/polyploid assemblies, it is up to the user to properly separate haplotypes before giving the data to Dorado `polish`.

We are currently working on a set of best practices. In the meantime, an unofficially suggested approach to polish diploid genomes would be to align the reads using the `lr:hqae` [Minimap2 setting](https://github.com/lh3/minimap2/releases/tag/v2.28) as this was specifically designed for alignment back to a diploid genome. This setting is available through Dorado `aligner` using the following option:
    
    
    dorado aligner --mm2-opts "-x lr:hqae" <ref> <reads>
    

## Troubleshooting

### Memory consumption / Torch out-of-memory (OOM) issues

The inference batch size is computed to fit the largest possible batches into the available GPU memory (default `--batchsize 0`).

There are two cases when an OOM issue can happen:

  1. The auto batch size feature is underestimating the memory consumption. If an Out-Of-Memory (OOM) warning/error is raised with the default auto batch size, try setting the batch size manually to a fixed value instead. For example:
         
         dorado polish reads_to_draft.bam draft.fasta --batchsize <number> > consensus.fasta
         

A good rule of thumb would be `--batchsize 16` for a large GPU, or try using a smaller value if this is still too high.

Additionally, the number of inference workers can be reduced to lower the memory usage (the default is `2` workers per device):
         
         dorado polish reads_to_draft.bam draft.fasta --infer-threads 1 > consensus.fasta
         

Alternatively, consider running inference on the CPU, although this can take longer:
         
         dorado polish reads_to_draft.bam draft.fasta --device "cpu" > consensus.fasta
         

Note that using multiple CPU inference threads can cause much higher memory usage.

  2. GPU memory fragmentation during the run. This can happen when there were many small allocations followed by a large memory allocation which then cannot be fitted into a single contiguous block of memory. Such errors will have a specific Torch error message which looks like this: > Exception caught: CUDA out of memory. Tried to allocate 15.12 GiB. GPU 1 has a total capacity of 31.73 GiB of which 14.77 GiB is free. Including non-PyTorch memory, this process has 16.95 GiB memory in use. Of the allocated memory 2.10 GiB is allocated by PyTorch, and 14.46 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation. See documentation for Memory Management (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The key portion here is: `2.10 GiB is allocated by PyTorch, and 14.46 GiB is reserved by PyTorch but unallocated.`, which means that almost all non-free memory is actually unused.

In this case, follow the suggestion from the error message, and it should resolve the issue.

Example:
         
         PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True dorado polish reads_to_draft.bam draft.fasta > consensus.fasta
         

### "[error] Could not open index for BAM file: 'aln.bam'!"

Example message:
    
    
    $ dorado polish aln.bam assembly.fasta > polished.fasta
    [2024-12-23 07:18:23.978] [info] Running: "polish" "aln.bam" "assembly.fasta"
    [E::idx_find_and_load] Could not retrieve index file for 'aln.bam'
    [2024-12-23 07:18:23.987] [error] Could not open index for BAM file: 'aln.bam'!
    

This message means that there the input BAM file does not have an accompanying index file `.bai`. This may also mean that the input BAM file is not sorted, which is a prerequisite for producing the `.bai` index using `samtools`.

Dorado `polish` requires input alignments to be produced using Dorado `aligner`. When Dorado `aligner` outputs alignments to `stdout`, they are not sorted automatically. Instead, `samtools` needs to be used to sort and index the BAM file. For example:
    
    
    dorado aligner <draft.fasta> <reads.bam> | samtools sort --threads <num_threads> > aln.bam
    samtools index aln.bam
    

Note that the sorting step is added after the pipe symbol.

The output from dorado aligner is already sorted when the output is to a folder, specified using the `--output-dir` option.
    
    
    dorado aligner --output-dir <out_dir> <draft.fasta> <reads.bam>
    

### "[error] Input BAM file has no basecaller models listed in the header."

Dorado `polish` requires that the aligned BAM has one or more `@RG` lines in the header. Each `@RG` line needs to contain a basecaller model used for generating the reads in this group. This information is required to determine the compatibility of the selected polishing model, as well as for auto-resolving the model from data.

When using Dorado `aligner` please provide the input basecalled reads in the BAM format. The basecalled reads BAM file (`e.g. calls.bam`) contains the `@RG` header lines, and this will be propagated into the aligned BAM file. Example:
    
    
    dorado aligner draft.fasta calls.bam | samtools sort --threads <num_threads> > aligned_reads.bam
    samtools index aligned_reads.bam
    

Alternatively, Dorado `aligner` will automatically sort and index the alignments when an output directory is specified instead of `stdout`.
    
    
    dorado aligner --output-dir out draft.fasta calls.bam
    

Note that this feature will only work for the HTS-style FASTQ headers, such as:
    
    
    @74960cfd-0b82-43ed-ae04-05162e3c0a5a qs:f:27.7534 du:f:75.1604 ns:i:375802 ts:i:1858 mx:i:1 ch:i:295 st:Z:2024-08-29T22:06:03.400+00:00 rn:i:585 fn:Z:FBA17175_7da7e070_f8e851a5_5.pod5 sm:f:414.101 sd:f:107.157 sv:Z:pa dx:i:0 RG:Z:f8e851a5d56475e9ecaa43496da18fad316883d8_dna_r10.4.1_e8.2_400bps_sup@v5.0.0
    

Dorado `polish` currently supports data generated using only the simplex basecallers.

### "[error] Input BAM file was not aligned using Dorado."

Dorado `polish` accepts only BAMs aligned with Dorado `aligner`. Aligners other than Dorado `aligner` are not supported.

Example usage:
    
    
    dorado aligner <draft.fasta> <reads.bam> | samtools sort --threads <num_threads> > aln.bam
    samtools index aln.bam
    

### "[error] The input BAM contains more than one read group. Please specify --RG to select which read group to process."

It is possible that the input BAM file contains more than 1 read group. In this case, Dorado `polish` requires that a single read group is selected for processing using the `--RG <id>` command line argument. The `<id>` should exactly match the `ID:` field in one of the `@RG` lines in the input BAM/SAM file.

Specifying the `--RG` option will filter out any read which does not belong to that read group and will apply the appropriate polishing model for that read group based on the basecaller model specified in the corresponding `@RG` line in the input BAM file.

Specifying a read group which corresponds to duplex data will not work because Dorado `polish` currently does not have duplex polishing models available.

In case of a duplex BAM - note that by default the simplex parents of the duplex reads will also be present in the output BAM file from Dorado. Consider filtering these out first if this could bias your results.

### "[error] Duplex basecalling models are not supported."

Dorado `polish` currently supports data generated using only the simplex basecallers.

### I created a merged BAM file composed of multiple different data types. Why can't I polish it? Using `--ignore-read-groups` does not help either

In case you created a merged BAM file, one of the following scenarios is possible:

  1. **There are zero read groups in the merged BAM file.** Something went wrong in the process of data preparation. There needs to be at least one read group in the BAM file which links the data to a basecaller model.
  2. **The merged BAM file has only one read group.** This is the best option, and merging was performed in a way that all colliding `@RG` headers were merged too. Since there is only one read group, there is also one basecaller model for the entire merged BAM dataset.
  3. **The merged BAM file has more than one read group, but only a single basecaller model.** This can occur when data originally belonged to the same read group but the colliding read groups were not merged in the process (check the `-c` option of `samtools merge`). For example, `samtools merge` will add a unique hash to the end of each read group, because the prefix of the read groups is the same (e.g. `bc8993f4557dd53bf0cbda5fd68453fea5e94485_dna_r10.4.1_e8.2_400bps_hac@v5.0.0-1C79A650` and `bc8993f4557dd53bf0cbda5fd68453fea5e94485_dna_r10.4.1_e8.2_400bps_hac@v5.0.0-6E00935B`). Alternatively, data from multiple sequencing runs were combined, but the same basecaller model was used in all cases.
     * Using `--ignore-read-groups` will run the process using all data in this case, since it was generated using a single basecaller model.
     * Alternatively, using `--RG <read_group_id>` will select only reads which belong to this specific read group, and ignore all other reads.
     * Auto model detection is possible from the BAM file in this case, since only one basecaller model was used to produce the data.
  4. **The merged BAM file has more than one read group and _more than one basecaller model_.** One or more read groups were generated using one particular basecaller model, while some other read groups were generated using another particular basecaller model. (For example, combining old and new data.) Sometimes, users may attempt to combine simplex and duplex reads into the same BAM file.
     * Dorado `polish`/`variant` can use only one selected model for inference. All currently available models were trained on individual data types (data generated by a single basecaller version) and not on a mixture of data (with the exception of the bacterial methylation polishing model). Running any model on a mixture of data may produce inferior results. This is why Dorado `polish` and Dorado `variant` enforce that only a single basecaller model is present in the input.
     * In this case, not even `--ignore-read-groups` will work because there was more than one basecaller model used to produce the data in this BAM file.
     * Using `--RG <read_group_id>` will select only reads which belong to one specific read group, and ignore all other reads.
     * Using the auto model selection cannot resolve a model from a BAM file if the input BAM file contains multiple models.
     * Auto model selection in this case is only possible if `--RG` is used.
     * Duplex basecaller models are not supported by Dorado `polish` or Dorado `variant`.

Back to top 

## 文档章节: Dorado Variant - Dorado Documentation

# Dorado Variant

Alpha Release

Dorado `variant` is an early-stage diploid small variant caller, it is released for experimental and evaluation purposes.

This version is intended for feedback and should not yet be considered production-ready.

## Should I use `variant` or `polish`?

Dorado variant is a short variant caller for diploid samples aligned to a haploid species reference (e.g. GRCh38) whereas `polish` is intended for workflows involving reads aligned to a haplotype-resolved (or haploid) draft assembly.

Although Dorado `polish` can also generate a VCF file of variants, there are some substantial distinctions between the two tools.

`dorado polish` | `dorado variant`  
---|---  
\- Polishing of draft assemblies  
\- Input is a haplotype-resolved draft assembly  
\- Output is a polished sequence  
\- Optionally, a VCF/gVCF of diffs is output  
\- Uses specialised polishing models | \- Diploid variant calling  
\- Input is a reference genome  
\- Output is a VCF/gVCF of called diploid variants  
\- Uses specialised variant calling models  
  
## Quick Start
    
    
    # Align the reads using dorado aligner, sort and index
    dorado aligner <ref.fasta> <reads.bam> | samtools sort --threads <num_threads> > aligned_reads.bam
    samtools index aligned_reads.bam
    
    # Call variants
    dorado variant <aligned_reads.bam> <ref.fasta> > variants.vcf
    

For this preview release, current models require signal-level information encoded in the move tables in the input BAM file. This requires the `--emit-moves` flag to be set during basecalling.
    
    
    # Align the reads using dorado aligner, sort and index
    dorado aligner <ref.fasta> <reads.fastq> | samtools sort --threads <num_threads> > aligned_reads.bam
    samtools index aligned_reads.bam
    

### Output to a folder
    
    
    dorado variant <aligned_reads> <reference> -o <output_dir>
    

Specifying `-o` will write the output to one or more files stored in the given output directory (and create the directory if it doesn't exist). Concretely:

  * VCF file: `<output_dir>/variants.vcf` which contains only variant calls by default, or records for all positions if `--gvcf` is specified.

## Resources

Dorado `variant` will automatically select the compute resources to perform variant calling. It can use one or more GPU devices. Variant calling can be performed on CPU-only, but we highly recommend to run on GPU for desired performance. High-memory GPUs are recommended to run this tool.

To specify resources manually use:

  * `-x / --device` \- to specify specific GPU resources (if available).
  * `--threads` \- to set the maximum number of threads to be used for everything but the inference.
  * `--infer-threads` \- number of inference workers to use (per device). For CPU-only runs, this specifies the number of CPU inference threads.
  * `--batchsize` \- batch size for inference, important to control memory usage on the GPUs. Automatically computed by default (`--batchsize 0`).

Example:
    
    
    dorado variant aligned_reads.bam reference.fasta --device cuda:0 --threads 24 > variants.vcf
    

## Models

By default, `variant` queries the BAM and selects the best model for the basecalled reads, if supported.

Alternatively, a model can be selected through the command line in the following way:
    
    
    dorado variant --model <value> ...
    

Value | Description  
---|---  
`auto` | Determine the best compatible model based on input data.  
`<basecaller_model>` | Simplex basecaller model name (e.g. `dna_r10.4.1_e8.2_400bps_hac@v5.0.0`)  
`<variant_model>` | Variant calling model name (e.g. `dna_r10.4.1_e8.2_400bps_hac@v5.0.0_variant_mv@v1.0`)  
`<path>` | Local path on disk where the model can be loaded from.  
  
When the `auto` or the `<basecaller_model>` syntax is used the most recent version of a compatible model will be selected for variant calling.

Current variant calling models require the presence of move tables in the input BAM file. Move tables need to be exported during basecalling.

If a non-compatible model is selected for the input data, or if there are multiple read groups in the input dataset which were generated using different basecaller models, Dorado `variant` will report an error and stop execution.

### Supported basecaller models

  * `dna_r10.4.1_e8.2_400bps_hac@v5.0.0`

More models will be supported in the near future. This is an alpha release.

## Common questions and Troubleshooting

### I created a merged BAM file composed of multiple different data types. Why can't I call variants on this dataset? Using `--ignore-read-groups` does not help either

Please see the following section in Dorado `polish`: [I created a merged BAM file composed of multiple different data types](../polish/#i-created-a-merged-bam-file-composed-of-multiple-different-data-types-why-cant-i-polish-it-using-ignore-read-groups-does-not-help-either)

### Memory consumption / Torch out-of-memory (OOM) issues

The inference batch size is computed to fit the largest possible batches into the available GPU memory (default `--batchsize 0`).

There are two cases when an OOM issue can happen:

  1. The auto batch size feature is underestimating the memory consumption. If an Out-Of-Memory (OOM) warning/error is raised with the default auto batch size, try setting the batch size manually to a fixed value instead. For example:
         
         dorado variant aligned_reads.bam reference.fasta --batchsize <number> > variants.vcf
         

A good rule of thumb would be `--batchsize 10` for a large GPU, or try using a smaller value if this is still too high.

Additionally, the number of inference workers can be reduced to lower the memory usage (the default is `2` workers per device):
         
         dorado variant aligned_reads.bam reference.fasta --infer-threads 1 > variants.vcf
         

  2. GPU memory fragmentation during the run. This can happen when there were many small allocations followed by a large memory allocation which then cannot be fitted into a single contiguous block of memory. Such errors will have a specific Torch error message which looks like this: > Exception caught: CUDA out of memory. Tried to allocate 15.12 GiB. GPU 1 has a total capacity of 31.73 GiB of which 14.77 GiB is free. Including non-PyTorch memory, this process has 16.95 GiB memory in use. Of the allocated memory 2.10 GiB is allocated by PyTorch, and 14.46 GiB is reserved by PyTorch but unallocated. If reserved but unallocated memory is large try setting PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True to avoid fragmentation. See documentation for Memory Management (https://pytorch.org/docs/stable/notes/cuda.html#environment-variables)

The key portion here is: `2.10 GiB is allocated by PyTorch, and 14.46 GiB is reserved by PyTorch but unallocated.`, which means that almost all non-free memory is actually unused.

In this case, follow the suggestion from the error message, and it should resolve the issue.

Example:
         
         PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True dorado variant aligned_reads.bam reference.fasta > variants.vcf
         

### "[error] Input BAM file was not aligned using Dorado."

Dorado `variant` accepts only BAMs aligned with Dorado `aligner`. Aligners other than Dorado `aligner` are not supported.

Example usage:
    
    
    dorado aligner <draft.fasta> <reads.bam> | samtools sort --threads <num_threads> > aln.bam
    samtools index aln.bam
    

### "[error] Input BAM file has no basecaller models listed in the header."

Please refer to this [section](../polish/#error-input-bam-file-has-no-basecaller-models-listed-in-the-header).

### "[error] Duplex basecalling models are not supported."

Dorado `variant` currently supports data generated using only the simplex basecallers.

### Does Dorado Variant phase variants?

At this early stage, Dorado `variant` does not yet produce phased VCF variants. This is work in progress.

Back to top 

## 文档章节: Barcode Classification - Dorado Documentation

# Barcode Classification

Dorado supports barcode classification for existing basecalls as well as producing barcode classified basecalls directly.

The default heuristic for double-ended barcodes is to look for them on **either** end of the read. This results in a higher classification rate but can also result in a higher false positive count. To address this, Dorado `basecaller` also provides a `--barcode-both-ends` option to force double-ended barcodes to be detected on both ends before classification. This will reduce false positives dramatically, but also lower overall classification rates.

## In-line with basecalling

In this mode, reads are classified into their barcode groups **during** basecalling as part of the same command. To enable this, run:
    
    
    dorado basecaller <model> <reads> --kit-name <barcode-kit-name> > calls.bam
    

This will result in a single output stream with classified reads. The classification will be reflected in the read group name as well as in the `BC` tag of the output record.

The output from Dorado `basecaller` can then be demultiplexed into per-barcode BAMs using Dorado `demux`.

If the barcoded reads are already classified when in-line barcoding, ensure the `--no-classify` argument is set, otherwise `demux` will search for barcodes again causing issues if reads are [trimmed](../../basecaller/read_trimming/).
    
    
    dorado demux --output-dir <output-dir> --no-classify <input-bam>
    

This will output a BAM file per barcode in the `output-dir`.

As the barcode information is also stored in the BAM `RG` header, demultiplexing is possible using `samtools split`.
    
    
    samtools split -u <output-dir>/unclassified.bam -f "<output-dir>/<prefix>_%!.bam" <input-bam>
    

However, `samtools split` uses the full `RG` string as the filename suffix, which can result in very long file names. We recommend using Dorado `demux` to split barcoded BAMs.

## Classifying existing datasets

Warning

Ensure `--no-trim` was set during basecalling otherwise `demux`` will fail to classify reads as they have had their barcodes removed.

Existing basecalled datasets **which have not been trimmed** can be classified and demultiplexed into per-barcode BAMs using the `demux` subcommand.
    
    
    dorado demux --kit-name <kit-name> --output-dir <output-dir-for-demuxed-bams> <reads>
    

`<reads>` can either be a folder or a single file in an HTS format (e.g. FASTQ, BAM, etc.) or a stream of an HTS format (e.g. the output of Dorado `basecaller`).
    
    
    dorado basecaller <model> <reads> --no-trim ... | dorado demux --kit-name <kit-name> --output-dir <output-dir> ...
    

This results in multiple BAM files being generated in the output folder, one per barcode (formatted as `KITNAME_BARCODEXX.bam`) and one for all unclassified reads. As with the in-line mode, `--no-trim` and `--barcode-both-ends` are also available as additional options.

If the input file is aligned/sorted and `--no-trim` is chosen, each of the output barcode-specific BAM files will also be sorted and indexed. However, if trimming is enabled (which is the default), the alignment information is removed and the output BAMs are unaligned. This is done because the alignment tags and positions are invalidated once a sequence is altered.

Here is an example output folder
    
    
    $ dorado demux --kit-name SQK-RPB004 --output-dir /tmp/demux reads.fastq
    
    $ ls -1 /tmp/demux
    SQK-RPB004_barcode01.bam
    SQK-RPB004_barcode02.bam
    SQK-RPB004_barcode03.bam
    ...
    unclassified.bam
    

A summary file listing each read and its classified barcode can be generated with the `--emit-summary` option in Dorado `demux`. The file will be saved in the `--output-dir` folder.

## Demultiplexing mapped reads

If the input data files contain mapping data, this information can be preserved in the output files. To do this, you must use the `--no-trim` option. Trimming the barcodes will invalidate any mapping information that may be contained in the input files, and therefore the application will exclude any mapping information if `--no-trim` is not specified.

It is also possible to get Dorado `demux` to sort and index any output bam files that contain mapped reads. To enable this, use the `--sort-bam` option. If you use this option then you must also use the `--no-trim` option, as trimming will prevent any mapping information from being included in the output files. Index files (.bai extension) will only be created for BAM files that contain mapped reads and were sorted. Note that for large datasets sorting the output files may take a few minutes.

### Using a sample sheet

Dorado is able to use a sample sheet to restrict the barcode classifications to only those present, and to apply aliases to the detected classifications. This is enabled by passing the path to a sample sheet to the `--sample-sheet` argument when using the `basecaller` or `demux` commands. See [here](../sample_sheet/) for more information.

### Custom barcodes

In addition to supporting the standard barcode kits from Oxford Nanopore, Dorado also supports specifying custom barcode kit arrangements and sequences. This is done by passing a barcode arrangement file via the `--barcode-arrangement` argument (either to Dorado `demux` or Dorado `basecaller`). Custom barcode sequences can optionally be specified via the `--barcode-sequences` option. See [here](../custom_barcodes/) for more details.

## CLI reference

Here's a slightly re-formatted output from the Dorado `demux` subcommand for reference.

Info

Please check the `--help` output of your own installation of dorado as this page may be outdated and argument defaults have been omitted as they are platform specific.
    
    
    â¯ dorado demux --help
    
    Barcode demultiplexing tool. Users need to specify the kit name(s).
    
    Positional arguments:
      reads                       An input file or the folder containing input file(s) (any HTS format).
    
    Optional arguments:
      -h, --help                  shows help message and exits
      -v, --verbose               [may be repeated]
    
    Input data arguments:
      -r, --recursive             If the 'reads' positional argument is a folder any subfolders will also
                                   be searched for input files.
      -n, --max-reads             Maximum number of reads to process. Mainly for debugging. Process all reads by default.
      -l, --read-ids              A file with a newline-delimited list of reads to demux.
    
    Output arguments:
      --emit-fastq                Output in fastq format.
      --emit-sam                  Output in SAM format.
      --emit-cram                 Output in CRAM format.
      --emit-summary              If specified, a summary file containing the details of the primary alignments
                                   for each read will be emitted to the root of the --output-dir folder.
      -o, --output-dir            Output folder which becomes the root of the nested output folder structure.
      --sort-bam                  Sort any BAM output files that contain mapped reads. Using this option requires
                                   that the --no-trim option is also set.
    
    Barcoding arguments:
      --no-classify               Skip barcode classification. Only demux based on existing classification in reads. Cannot be used with --kit-name or --sample-sheet.
      --kit-name                  Barcoding kit name. Cannot be used with --no-classify. Choose from:
                                   EXP-NBD103 EXP-NBD104 EXP-NBD114 EXP-NBD114-24 EXP-NBD196 EXP-PBC001
                                   EXP-PBC096 SQK-16S024 SQK-16S114-24 SQK-DRB004-24 SQK-HTB114-96 SQK-LWB001
                                   SQK-MAB114-24 SQK-MLK111-96-XL SQK-MLK114-96-XL SQK-NBD111-24 SQK-NBD111-96
                                   SQK-NBD114-24 SQK-NBD114-96 SQK-PBK004 SQK-PCB109 SQK-PCB110 SQK-PCB111-24
                                   SQK-PCB114-24 SQK-RAB201 SQK-RAB204 SQK-RBK001 SQK-RBK004 SQK-RBK110-96
                                   SQK-RBK111-24 SQK-RBK111-96 SQK-RBK114-24 SQK-RBK114-96 SQK-RLB001 SQK-RPB004
                                   SQK-RPB114-24 TWIST-16-UDI TWIST-96A-UDI VSK-PTC001 VSK-VMK001 VSK-VMK004 VSK-VPS001.
      --sample-sheet              Path to the sample sheet to use.
      --barcode-both-ends         Require both ends of a read to be barcoded for a double ended barcode.
      --barcode-arrangement       Path to file with custom barcode arrangement.
      --barcode-sequences         Path to file with custom barcode sequences.
    
    Trimming arguments:
      --no-trim                   Skip barcode trimming. If this option is not chosen, trimming is enabled.
                                   Note that you should use this option if your input data is mapped and you want
                                   to preserve the mapping in the output files, as trimming will result in any
                                   mapping information from the input file(s) being discarded.
    
    Advanced arguments:
      -t, --threads               Combined number of threads for barcoding and output generation.
                                   Default uses all available threads.
    

Back to top 

## 文档章节: Custom Barcodes - Dorado Documentation

# Custom Barcode Arrangements

Dorado supports barcode demultiplexing using custom barcode arrangements. These include customizations of existing kits (e.g. using only a subset of the barcodes from a kit) or entirely new kits containing new barcode sequences and layouts.

The format to define a custom arrangement is inspired by the arrangement specification in Guppy, with some adjustments to account for the algorithmic changes in Dorado.

Custom barcode arrangements are defined using a `toml` file, and custom barcode sequences are defined in a `FASTA` file.

## Barcode reference diagram

A double-ended barcode with different flanks and barcode sequences for front and rear barcodes is described here.
    
    
     5' --- ADAPTER/PRIMER
    ... --- LEADING_FLANK_1 --- BARCODE_1 --- TRAILING_FLANK_1
    ... --- READ
    ... --- RC(TRAILING_FLANK_2) --- RC(BARCODE_2) --- RC(LEADING_FLANK_2)
    ... --- 3'
    

  * For single-ended barcodes, there is no barcode sequence at the rear of the read.
  * For double-ended barcodes which are symmetric, the flank and barcode sequences for front
  * and rear windows are same.

For single-ended barcodes with the `rear_only_barcodes` flag set (see below), e.g. RNA kits, the sequence description would look like this:
    
    
     5' ---READ
    ... ---LEADING_FLANK_1 ---BARCODE_1 ---TRAILING_FLANK_1
    ... ---ADAPTER/PRIMER --- 3'
    

## Arrangement file

The following are all the options that can be defined in the arrangement file.
    
    
    [arrangement]
    name = "custom_barcode"
    kit = "BC"
    
    mask1_front = "ATCG"
    mask1_rear = "ATCG"
    mask2_front = "TTAA"
    mask2_rear = "GGCC"
    
    # Barcode sequences
    barcode1_pattern = "BC%02i"
    barcode2_pattern = "BC%02i"
    first_index = 1
    last_index = 96
    rear_only_barcodes = true
    
    ## Scoring options
    [scoring]
    max_barcode_penalty = 11
    barcode_end_proximity = 75
    min_barcode_penalty_dist = 3
    min_separation_only_dist = 6
    flank_left_pad = 5
    flank_right_pad = 10
    front_barcode_window = 175
    rear_barcode_window = 175
    midstrand_flank_score = 0.95
    

### Arrangement options

The table below describes the arrangement options in more detail.

Option | Required | Description  
---|---|---  
name | **Yes** | Name of the barcode arrangement. This name will be used to report the barcode classification.  
kit |  | Which class of barcodes this arrangement belongs to (if any).  
mask1_front | **Yes** | The leading flank for the front barcode. [1,2]  
mask1_rear | **Yes** | The trailing flank for the front barcode. [1,2]  
mask2_front |  | The leading flank for the rear barcode. [1,3]  
mask2_rear |  | The trailing flank for the rear barcode. [1,3]  
barcode1_pattern | **Yes** | An expression capturing the sequences to use for the front barcode. [4]  
barcode2_pattern |  | An expression capturing the sequences to use for the rear barcode. [4]  
first_index | **Yes** | Start index for range of barcode sequences to use in the arrangement. Used in combination with the `last_index`.  
last_index | **Yes** | End index for range of barcode sequences to use in the arrangement. Used in combination with the `first_index`.  
rear_only_barcodes |  | For single ended barcodes, the barcode is at the rear of the read rather than the front (e.g for an RNA kit).  
  
  1. Can be empty string.
  2. Applies to single and double-ended barcodes.
  3. Applies to double-ended barcodes only.
  4. Pattern must match sequences from pre-built kits list in Dorado or in the custom sequences file.

The pre-built barcode sequences in Dorado can be found in the [barcode_kits.cpp file](https://github.com/nanoporetech/dorado//dorado/utils/barcode_kits.cpp) under the `barcodes` map.

### Scoring options

Dorado maintains a default set of parameters for scoring each barcode to determine the best classification. These parameters have been tuned based on barcoding kits from Oxford Nanopore. However, the default parameters may not be optimal for new arrangements and kits.

The classification heuristic applied by Dorado is the following:

  1. Dorado uses the flanking sequences defined in `maskX_front/rear` to find a window in the read where the barcode is situated.

  2. For double-ended barcodes, the **best** window (either from the front or rear of the read) is chosen based on the alignment of the flanking mask sequences.

  3. Each barcode candidate within the arrangement is aligned to the subsequence within the window. The alignment may optionally consider additional bases from the preceding/succeeding flank (as specified in the `flank_left_pad` and `flank_right_pad` parameters).

  4. The edit distance of this alignment is assigned as a penalty to each barcode.

Once barcodes are sorted by barcode penalty, the top candidate is checked against the following rulesets:

  * Ruleset 1:

    * The barcode penalty is less than or equal to `max_barcode_penalty`
    * The distance between top 2 barcode penalties is greater than or equal to `min_barcode_penalty_dist`
    * The flank score is greater than or equal to `min_flank_score`
  * Ruleset 2:

    * The barcode penalty is greater than `max_barcode_penalty`
    * The distance between top 2 barcodes penalties is greater than or equal to `min_separation_only_dist`

If a candidate meets all criteria in either (1) or (2), and the location of the start/end of the barcode construct is within `barcode_end_proximity` bases of the ends of the read, then it is considered a hit.

For double-ended barcode kits, a read may then be declassified if -

  1. The best front or rear barcode is different to the best overall barcode, and has a penalty less than or equal `max_barcode_penalty`
  2. `barcode_both_ends` has been specified, and the best overall barcode does not have both a front and rear barcode penalty less than or equal to `max_barcode_penalty`

Scoring option | Description  
---|---  
max_barcode_penalty | The maximum edit distance allowed for a classified barcode. Considered in conjunction with the `min_barcode_penalty_dist` parameter.  
min_barcode_penalty_dist | The minimum penalty difference between top-2 barcodes required for classification. Used in conjunction with `max_barcode_penalty`.  
min_separation_only_dist | The minimum penalty difference between the top-2 barcodes required for classification when the `max_barcode_penalty` is not met.  
barcode_end_proximity | Proximity of the end of the barcode construct to the ends of the read required for classification.  
flank_left_pad | Number of bases to use from preceding flank during barcode alignment.  
flank_right_pad | Number of bases to use from succeeding flank during barcode alignment.  
front_barcode_window | Number of bases at the front of the read within which to look for barcodes.  
rear_barcode_window | Number of bases at the rear of the read within which to look for barcodes.  
min_flank_score | Minimum score for the flank alignment. Score here is 1.f - (edit distance) / flank_length  
midstrand_flank_score | Minimum score for a flank alignment that is not at read ends to be considered as a mid-strand barcode. Score here is 1.f - (edit distance) / flank_length  
  
For `flank_left_pad` and `flank_right_pad`, something in the range of 5-10 bases is typically good. Note that errors from this padding region are also part of the barcode alignment penalty. Therefore a bigger padding region may require a higher `max_barcode_penalty` for classification.

## Sequences file

In addition to specifying a custom barcode arrangement, new barcode sequences can also be specified in a FASTA format.

There are 2 requirements:

  1. The sequence names must follow the `prefix%\d+i` format (e.g. `BC%02i` for barcodes needing 2 digit indexing, or `NB%04i` for barcodes with 4 digit indexing, etc.).
  2. All barcode sequence lengths must match.

This is an example sequences file.
    
    
    >BC01
    TTTT
    >BC02
    AAAA
    >BC03
    GGGG
    >BC04
    CCCC
    

Back to top 

## 文档章节: Custom Primers - Dorado Documentation

# Custom Adapter and Primer Sequences

Dorado will automatically detect and trim any adapter or primer sequences it finds. The specific sequences it searches for depends on the specified sequencing kit. Dorado `basecaller`, can get this information from read metadata in the input pod5. Dorado `trim` however, requires that the sequencing kit is specified using the command-line option.

In some cases, it may be necessary to find and remove adapter and/or primer sequences that would not normally be associated with the sequencing kit that was used, or you may be working with older data for which the sequencing kit and/or primers being used are no longer directly supported by Dorado (for example, anything prior to kit14). In such cases, you can specify a custom adapter/primer file, using the command-line option `--primer-sequences`. If this option is used, then the sequences encoded in the specified `--primer-sequences` file will be used instead of the default sequences.

## Custom adapter/primer file format

The custom adapter/primer file uses the FASTA file format, where the desired adapter/primer sequences are specified with additional metadata to define how each sequence should be used.

The following is an example adapter sequence:
    
    
    >LSK109_front   et:Z:adapter    sk:Z:SQK-PSK004,SQK-LSK109
    AATGTACTTCGTTCAGTTACGTATTGCT
    

The syntax rules are as follows:

Record Name
    

The record name must be of the form `[id]_front` or `[id]_rear`.

The `id` must be unique other than for the `_front` and `_rear` pair.

Type
    

The HTS-style tag `et:Z:`, with a value of either `adapter` or `primer`.

Kits
    

The HTS-style tag `sk:Z:`, with a value of either `any`, or a list of sequencing kits (e.g., `[kit1],[kit2],[kit3]`).

Note that the HTS-style tags should be tab-delimited.

### How Dorado searches for adapters/primers

The `_front` and `_rear` record name suffixes and the `type` designator defines how Dorado will search for the sequence.

For **adapters** :
    

Dorado will search for `front` sequence near the beginning of the read, and for `rear` sequence near the end of the read.

For **primers** :
    

Dorado will search for the `front` sequence near the beginning of the read, and the reverse-complement of the `rear` sequence near the end of the read. Dorado will also search for the `rear` sequence near the beginning of the read, and for the reverse-complement of the `front` sequence near the end of the read.

The `et:Z:` tag is required to designate whether the sequence is an adapter or a primer sequence, so that dorado knows how it should be used. The `sk:Z:` tag is required to indicate which sequencing kit the adapter or primer sequence may be used with. The sequence will only be searched for if the sequencing-kit information in the read matches one of the kit names in the custom file. If the `sk:Z:` tag has the value `any`, then the sequence will be searched for in all reads, regardless of the kit that was used. Note that the kit names are case-insensitive.

#### Example custom adapter/primer file

The following could be used to detect the `PCR_PSK_rev1` and `PCR_PSK_rev2` primers, along with the `LSK109` adapters, for older data.
    
    
    >LSK109_front   et:Z:adapter    sk:Z:any
    AATGTACTTCGTTCAGTTACGTATTGCT
    
    >LSK109_rear    et:Z:adapter    sk:any
    AGCAATACGTAACTGAACGAAGT
    
    >PCR_PSK_front  et:Z:primer sk:any
    ACTTGCCTGTCGCTCTATCTTCGGCGTCTGCTTGGGTGTTTAACC
    
    >PCR_PSK_rear   et:Z:primer sk:any
    AGGTTAAACACCCAAGCAGACGCCGCAATATCAGCACCAACAGAAA
    

In this case, the above adapters and primers would be searched for in all reads, regardless of the sequencing-kit information encoded in the read file, or in the case of dorado trim, regardless of the sequencing-kit specified on the command-line.

To restrict the search to only primers in reads where `SQK-PSK004` specified as the kit name, and adapters if reads were from either `SQK-PSK004` or `SQK-LSK109`, then the following could be used.
    
    
    >LSK109_front   et:Z:adapter    sk:Z:SQK-PSK004,SQK-LSK109
    AATGTACTTCGTTCAGTTACGTATTGCT
    
    >LSK109_rear    et:Z:adapter    sk:Z:SQK-PSK004,SQK-LSK109
    AGCAATACGTAACTGAACGAAGT
    
    >PCR_PSK_front  et:Z:primer sk:Z:SQK-PSK004
    ACTTGCCTGTCGCTCTATCTTCGGCGTCTGCTTGGGTGTTTAACC
    
    >PCR_PSK_rear   et:Z:primer sk:Z:SQK-PSK004
    AGGTTAAACACCCAAGCAGACGCCGCAATATCAGCACCAACAGAAA
    

Back to top 

## 文档章节: Sample Sheet - Dorado Documentation

# Sample Sheet

Dorado can make use of a MinKNOW-compatible sample sheet containing data used to identify a particular classification of read.

To apply a sample sheet, provide the path to the appropriate CSV file using the `--sample-sheet` argument:
    
    
    dorado basecaller dna_r10.4.1_e8.2_400bps_hac@v4.2.0 reads/ \
        --kit-name SQK-16S114-24 \
        --sample-sheet <path_to_sample_sheet_csv> \
        > calls.bam
    

A sample sheet can also be applied to the `demux` command in the same way:
    
    
    dorado demux calls.bam \
        --output-dir classified_reads \
        --kit-name SQK-16S114-24 \
        --sample-sheet <path_to_sample_sheet_csv>
    

Dorado currently uses the sample sheet only for barcode filtering and aliasing, so a `--kit-name` argument is **required**.

In the case of `demux`, the sample sheet must contain a 1-to-1 mapping of `barcode` identifiers to `flow_cell_id`/`position_id` \- i.e. all entries in the `barcode` column must be unique.

## Specification

### Sample sheet column headers

A sample sheet may only contain the column names below:

Purpose | Column Name | Notes  
---|---|---  
Standard | `experiment_id`[1] | Required[3]  
| `kit` | Required  
| `flow_cell_id`[2] | Optional if `position_id` is set  
| `position_id`[2] | Optional if `flow_cell_id` is set  
| `protocol_run_id` | Optional  
| `sample_id` | Optional[3]  
| `flow_cell_product_code` | Optional  
Barcoding | `alias`[4] | Optional[3]  
| `type` | Optional  
| `barcode`[5] | Optional  
  
  1. All rows in a sample sheet must contain the same `experiment_id`.
  2. At a minimum a sample sheet must contain `kit`, `experiment_id` and one of `position_id` or `flow_cell_id`.
  3. These fields must be a **maximum of 40 characters** , which must be either alphanumeric (`A-Z`, `a-z`, `0-9`), `_` or `-`.
  4. See Barcode aliasing
  5. See Barcode filtering

For a full description of the format of the sample sheet, see [the MinKNOW Sample Sheet documentation](https://community.nanoporetech.com/docs/prepare/library_prep_protocols/experiment-companion-minknow/v/mke_1013_v1_revcy_11apr2016/sample-sheet-upload).

Note

Dorado does not currently support dual barcodes.

## Barcode aliasing

If a sample sheet contains an `alias` column, this will be used to replace the `barcode` identifier for reads matching the `flow_cell_id`/`position_id` and `experiment_id`. This will be reflected in the read group ID `@RG ID` in the file header, and in the `BC` and `RG` tags of the classified reads.

Note

If both `flow_cell_id` and `position_id` are present, both must match the read data for an alias to be applied.

Warning

Values in the `alias` column must not be valid barcode identifiers (e.g. `barcode##` or `unclassified`).

## Barcode filtering

If a sample sheet is present and barcoding is requested, Dorado will only attempt to find matches to the barcode identifiers listed in the `barcode` column (if present).

Back to top 

## 文档章节: Alignment - Dorado Documentation

# Alignment

Dorado uses the [minimap2 aligner](https://github.com/lh3/minimap2) to align basecalled sequences to a reference and supports aligning existing basecalls or producing aligned output directly.

## Aligning existing basecalls

To align existing basecalls, run:
    
    
    dorado aligner <index> <calls> > aligned.bam
    

where index is a reference to align to in (FASTQ/FASTA/.mmi) format and reads is a folder or file in any HTS format.

### Writing to an output directory

When reading from an input folder, Dorado `aligner` also supports writing aligned files to an output directory. The output directory is formatted in the [MinKNOW output structure](https://nanoporetech.github.io/ont-output-specifications/latest/minknow/output_structure/).
    
    
    dorado aligner <index> <calls-dir> --output-dir <output-dir>
    

### Alignment summary

An alignment summary containing alignment statistics for each read can be generated with the `--emit-summary` argument.

Note

The `--emit-summary` argument requires that the `--output-dir <output-dir>` argument is set.

The alignment summary file will be written into `<output-dir>`.

## Alignment during basecalling

Including alignment during basecalling should not have a significant impact on overall basecalling throughput. Although alignment is a CPU intensive operation, basecalling throughput is generally limited by the GPU while the CPU is under-utilised. Dorado can make efficient use of both the GPU for basecalling and the otherwise under-utilised CPU for alignment, performing both concurrently.

To basecall with alignment with Dorado `basecaller` or Dorado `duplex`, add the `--reference` argument:
    
    
    dorado basecaller <model> <reads> --reference <index> > aligned.bam
    dorado duplex     <model> <reads> --reference <index> > aligned.bam
    

## Minimap2 options

Alignment uses `minimap2` and by default uses the `lr:hq` preset. This can be overridden by passing a minimap option string, `--mm2-opts`, using the '-x ' option and/or individual options such as -k and -w to set kmer and window size respectively.
    
    
    dorado aligner <index> <calls> --output-dir <output-dir> --mm2-opts "-x splice --junc-bed <annotations_file>"
    dorado aligner <index> <calls> --output-dir <output-dir> --mm2-opts --help
    
    dorado basecaller <model> <reads> --reference <index> --mm2-opts "-k 15 -w 10" > aligned.bam
    

For a complete list of supported minimap2 options use '--mm2-opts "--help"'. For example:
    
    
    $ dorado aligner <index> <calls> --mm2-opts "--help"
    
    Optional arguments:
      -h, --help   shows help message and exits
      -k           minimap2 k-mer size for alignment (maximum 28).
      -w           minimap2 minimizer window size for alignment.
      -I           minimap2 index batch size.
      --secondary  minimap2 outputs secondary alignments
      -N           minimap2 retains at most INT secondary alignments
      -Y           minimap2 uses soft clipping for supplementary alignments
      -r           minimap2 chaining/alignment bandwidth and optionally long-join bandwidth specified as NUM,[NUM]
      --junc-bed   Optional file with gene annotations in the BED12 format (aka 12-column BED), or intron positions in 5-column BED. With this option, minimap2 prefers splicing in annotations.
      -x           minimap2 preset for indexing and mapping. [default: "lr:hq"]
    

Warning

Not all arguments from `minimap2` are currently available and parameter names are not finalized and may change.

Note that dorado does support split indexes, however the entire index must be able to fit in memory. Aligning to a split index may result in some spurious secondary and/or supplementary alignments, and the mapping score may not be as reliable as for a non-split index. So it is recommended that, if possible, you generate your `mmi` index files using the `-I` option with a large enough value to generate a non-split index. Or, if you are directly using a large fasta reference, pass a large enough value of the `-I` minimap2 option using `--mm2-opts` to insure that the index is not split.

## Counting overlaps

The `--bed-file <bed>` argument is available in the Dorado `basecaller` and Dorado `aligner`. This argument specifies a `.bed` filepath which is used to count the number of overlaps between the bed file regions and the alignments generated.

This number is written to the BAM file output as the `bh` read tag.

## CLI reference

Here's a slightly re-formatted output from the Dorado `aligner` subcommand for reference.

Info

Please check the `--help` output of your own installation of Dorado as this page may be outdated and argument defaults have been omitted as they are platform specific.
    
    
    > dorado aligner --help
    
    Positional arguments:
      index                       reference in (fastq/fasta/mmi).
      reads                       An input file or the folder containing input file(s) (any HTS format).
    
    Optional arguments:
      -h, --help                  shows help message and exits
      -v, --verbose               [may be repeated]
    
    Input data arguments:
      -r, --recursive             If the 'reads' positional argument is a folder any subfolders will also
                                    be searched for input files.
      -n, --max-reads             maximum number of reads to process (for debugging, 0=unlimited).
    
    Alignment arguments:
      --mm2-opts                  Optional minimap2 options string. For multiple arguments surround with double quotes.
      --bed-file                  Optional bed-file. If specified, overlaps between the alignments and bed-file
                                    entries will be counted, and recorded in BAM output using the 'bh' read tag.
    
    Output arguments:
      --no-sort                   Disable sorting of output files.
      --emit-sam                  Output in SAM format.
      --emit-cram                 Output in CRAM format. If set, reference must be FASTA(.gz).
      --emit-summary              If specified, a summary file containing the details of the primary alignments
                                    for each read will be emitted to the root of the --output-dir folder.
      -o, --output-dir            Output folder which becomes the root of the nested output folder structure. Required if the 'reads' positional argument is a folder.
    
    Advanced arguments:
      -t, --threads               number of threads for alignment and BAM writing (0=unlimited).
      --allow-sec-supp            Align secondary and supplementary records from the input BAM if present.
    

Back to top 

## 文档章节: Introduction - Dorado Documentation

# Basecaller

Click [here](https://nanoporetech.com/platform/technology/basecalling) for an introduction of how nanopore sequencing and basecalling works.

Basecalling quick start instructions can be found [here](../simplex/).

## Basecalling pipeline

Dorado is the Oxford Nanopore basecaller. Basecalling is the process of calling nucleotide bases (ACGT) from a nanopore signal which is recorded from your sequencing device. This signal data is stored in POD5 or .fast5 files, although support for the .fast5 file format has been deprecated.

There are many parts of the basecalling process many of which we will explain in this document.
    
    
    graph LR
      IN[Data Ingest
      ...
      POD5 / .fast5
      ] --> PREP[Read
      Pre-Processing
    ...
      Scaling
      Normalisation
      Filtering
      Signal Trimming
      ...];
      PREP --> ML[Machine Learning
      Algorithm &
      Decoder];
      ML --> EXTRA[Additional
      Processing
      ...
      Alignment
      Barcoding
      Mod Basecalling
      ...]
      EXTRA --> POST["Sequence
      Post-Processing
      ...
      Filtering
      Trimming
      Poly(A) Estimation
      ..."];
    
      POST --> WRITER[Writer
      ...
      Filtering
      ];

* * *

## Data ingest

Support for .fast5 files is deprecated

Reads are sourced from POD5 and .fast5 files.

`-n / --max-reads N` \- Basecall only `N` reads

`-l / --read-ids FILE` \- Basecall only reads in `FILE`. This read ids file should contain newline delimited read ids only.

`-r / --recursive` \- Consider all POD5 **or** FAST5 files in `data` and all subdirectories.

* * *

## Signal pre-processing
    
    
    graph LR
    SRC[Signal In] --> SCALE[Scaling & Normalisation];
    SCALE --> TRIM_ST[Signal Trimming];
    TRIM_ST --> OUT[Signal Out];

The signal chunk pre-processing stage takes raw signal chunks from their source and performs some manipulations to improve basecalling accuracy.

Signal scaling aims to bring raw signal values into a consistent regime to improve the performance of the machine learning algorithm using during basecalling. The scaling strategies used are pico-Ampere (PA) scaling with and without standardisation, quantile scaling and median absolute deviation (medmad) scaling. The scaling strategy used depends on the how the basecalling model was trained and as such the scaling strategy selection is controlled by the model configuration file. Note that scaling is performed on the whole read before trimming.

DNA rapid adapter trimming is disabled

In the trimming stage, RNA adapters and DNA **rapid adapters** * are detected in the signal and their position is recorded.

The very beginning of a nanopore sequencing read often contains samples that are far out of the normal distribution and as such we try to remove these samples in **DNA reads only** by detecting the first samples of useful data.

Finally, if any signal trimming is required, it is actioned.

* * *

## Machine learning algorithm

The machine learning algorithm is at the core of the basecalling process. These highly accurate and efficient models can decode the sequencing signal to produce nucleotide base calls. The machine learning model predicts the probabilities of each base being present throughout the signal. These probabilities are then decoded to determine the most likely sequence of bases which is then emitted as the output of the algorithm.

There have been many versions of basecalling models with improvements to model architecture and training data to enhance basecalling speed and accuracy over time. The basecalling model is set by the user and is normally one of `fast`, `hac` (high-accuracy), and `sup` (super-accurate).

More details can be found in the dedicated [models documentation](../../models/models/).

Advanced basecalling controls

Here are the advanced basecalling parameters available to the user:

Warning

We generally **do not recommend** users set the arguments listed here unless absolutely necessary.

The default values are often good for most users however if you're facing issues please read the [troubleshooting guide](../../troubleshooting/troubleshooting/).

`--batchsize SIZE` \- The batch size controls the number of signal chunks passed the the model at once. This can be thought of as the number of rows in a table. Often, increasing the batch size results in better overall throughput especially on modern GPU hardware. However, this comes at the cost of increases memory usage which is limited. Dorado will use a default batchsize if one is has been computed for the system hardware.

* * *

## Additional processing

### Alignment

Please see [alignment](../alignment/) for details.

### Barcoding

Please see [barcoding](../../barcoding/barcoding/) for details.

### Modified basecalling

Please see [modified basecalling](../mods/) for details.

* * *

## Sequence post-processing

The sequence post-processing stage includes a number of stages depending on the options selected.

### Read trimming

Please see [read trimming](../read_trimming/) for details.

### Read splitting

Please see [read splitting](../read_splitting/) for details.

### Poly(A) estimation

Please see [poly(A) estimation](../polya_estimation/) for details.

* * *

## File writer

See the [Dorado SAM file specification](../sam_spec/) for details on the SAM / BAM / CRAM output generated by Dorado.

BAM is the default file format written by Dorado `basecaller`, however SAM, CRAM, and FASTQ file formats can be selected. The content of the BAM, SAM, and CRAM files will be identical but the metadata content in the FASTQ file will differ and some of the metadata tags are not supported.

By default, the output file is written to `stdout`. This process is summarised in the getting started help for [redirecting output](../../#redirecting-output) but the output can be written directly to files using the `-o / --output-dir` argument.

`--emit-sam` \- This flag sets the output file format to be SAM.

`--emit-cram` \- This flag sets the output file format to be CRAM. Note: If using `--emit-cram` while aligning, the reference must be FASTA(.gz).

`--emit-fastq` \- This flag sets the output file format to be FASTQ.

`--emit-moves` \- This flag will write the [move table](../move_table/) into the SAM / BAM / CRAM outputs.

`--emit-summary` \- This flag will generate a summary file `sequencing_summary.txt`, which follows the [sequencing summary specification](https://nanoporetech.github.io/ont-output-specifications/latest/protocol_formats/sequencing_summary/). The file is located in the specified `-o / --output-dir` directory if set, otherwise it is placed in the current working directory.

`-o / --output-dir DIR` \- This optional argument can be used to specify an output directory which follows the [MinKnow output structure](https://nanoporetech.github.io/ont-output-specifications/latest/minknow/output_structure/).

* * *

Back to top 

## 文档章节: Duplex - Dorado Documentation

# Duplex Basecalling

Duplex basecalling is an extension to the simplex basecalling process where Dorado continues by pairing template and complement strands, combines all the information for both strands including the basecalls, Q-scores and, signal and passes this through a stereo duplex model. The stereo duplex model considers this combined information to improve the basecalling accuracy.

Please watch this video on [YouTube](https://www.youtube.com/embed/8DVMG7FEBys?si=XUHn3DwZCKOPI1k8) for an introduction to Duplex basecalling.

## Quick start

To run Dorado duplex basecalling, using an automatically [downloaded](../../models/downloader/) `hac` model on a directory of POD5 files or a single POD5 file (.fast5 files are supported, but will not be as performant).
    
    
    dorado duplex hac  pod5s/ > calls.duplex.bam
    

Warning

The `fast` model is not recommended for duplex basecalling

To basecall a single file, simply replace the directory `pod5s/` with a path to your data.
    
    
    dorado duplex hac  /path/to/reads.pod5 > calls.duplex.bam
    

To automatically download and use the `sup` (super-accurate) models try the following:
    
    
    dorado duplex sup  pod5s/ > calls.duplex.bam
    

If you have a model that has already been [downloaded](../../models/downloader/) that you want to reuse you can use the model path directly.
    
    
    dorado duplex /path/to/model/ pod5s/ > calls.duplex.bam
    

Dorado will automatically download the required stereo duplex model if it wasn't found following the [model search procedure](../../models/downloader/#model-search-directory-and-temporary-downloads).

## Duplex Sequence Metadata

When using the duplex command, two types of DNA sequence results will be produced: 'simplex' and 'duplex'. Any specific position in the DNA which is in a duplex read is also seen in two simplex strands (the template and complement). So, each DNA position which is duplex sequenced will be covered by a minimum of three separate readings in the output.

Dorado records the this information in the `dx` BAM tag on all reads basecalled using Dorado `duplex`. The `dx` tag can be used to distinguish between simplex and duplex reads as follows:

`dx` | Read Description  
---|---  
`1` | A duplex read.  
`0` | A simplex read which has no duplex offspring.  
`-1` | A simplex read which has duplex offspring.  
  
Dorado will report the duplex rate as the number of nucleotides in the duplex basecalls multiplied by two and divided by the total number of nucleotides in the simplex basecalls. This value is a close approximation for the proportion of nucleotides which participated in a duplex basecall.

## Hemi-methylation duplex basecalling

Duplex basecalling can be performed with modified base detection, producing hemi-methylation calls for duplex reads.
    
    
    dorado duplex hac,5mCG_5hmCG pod5s/ > duplex.bam
    

More information on how hemi-methylation calls are represented can be found the SAM [specification](https://samtools.github.io/hts-specs/SAMtags.pdf) and Modkit [documentation](https://nanoporetech.github.io/modkit/intro_pileup_hemi.html).

## Duplex basecalling performance

Duplex basecalling is an IO-intensive process and can perform poorly if using networked storage or HDD. This can generally be improved by splitting up POD5 files appropriately. Firstly install the POD5 python tools ([documentation](https://pod5-file-format.readthedocs.io/en/latest/docs/tools.html)):
    
    
    pip install pod5
    

Then run `pod5 view` to generate a table containing information to split on specifically, the "channel" information.
    
    
    pod5 view /path/to/your/dataset/ --include "read_id, channel" --output summary.tsv
    

This will create `summary.tsv` file which should look like:
    
    
    read_id channel
    0000173c-bf67-44e7-9a9c-1ad0bc728e74    109
    002fde30-9e23-4125-9eae-d112c18a81a7    463
    ...
    

Now run `pod5 subset` to copy records from your source data into a new output file per-channel. This might take some time depending on the size of your dataset
    
    
    pod5 subset /path/to/your/dataset/ --summary summary.tsv --columns channel --output split_by_channel
    

The command above will create the output directory `split_by_channel` and write into it one POD5 file per unique channel. Duplex basecalling these split reads should now be much faster.

### Distributed duplex basecalling

If running duplex basecalling in a distributed fashion (e.g. on a SLURM or Kubernetes cluster) it is important to split POD5 files as described above. The reason is that duplex basecalling requires aggregation of reads from across a whole sequencing run, which will be distributed over multiple POD5 files.

The splitting strategy described above ensures that all reads which need to be aggregated are in the same POD5 file. Once the split is performed one can execute multiple jobs against smaller subsets of POD5 (e.g one job per 100 channels). This will allow basecalling to be distributed across nodes on a cluster.

This will generate multiple BAMs which can be merged. This approach also offers some resilience as if any job fails it can be restarted without having to re-run basecalling against the entire dataset.

## CLI reference

Here's a slightly re-formatted output from the Dorado `duplex` subcommand for reference.

Info

Please check the `--help` output of your own installation of dorado as this page may be outdated and argument defaults have been omitted as they are platform specific.
    
    
    â¯ dorado duplex --help
    
    Positional arguments:
      model                             Model selection {fast,hac,sup}@v{version} for automatic model selection
                                          including modbases, or path to existing model directory.
      reads                             Reads in POD5 format or BAM/SAM/CRAM format for basespace.
    
    Optional arguments:
      -h, --help                        shows help message and exits
      -v, --verbose                     [may be repeated]
      -x, --device                      Specify CPU or GPU device: 'auto', 'cpu', 'cuda:all' or 'cuda:<device_id>[,<device_id>...]'.
                                          Specifying 'auto' will choose either 'cpu', 'metal' or 'cuda:all'
                                          depending on the presence of a GPU device.
      --models-directory                Optional directory to search for existing models or download new models into.
    
    Input data arguments:
      -r, --recursive                   Recursively scan through directories to load POD5 files.
      -l, --read-ids                    A file with a newline-delimited list of reads to basecall.
                                          If not provided, all reads will be basecalled.
      --pairs                           Space-delimited csv containing read ID pairs. If not provided, pairing
                                          will be performed automatically.
    
    Output arguments:
      --min-qscore                      Discard reads with mean Q-score below this threshold or write them to
                                          output files marked `fail` if `--output-dir` is set.
      --emit-fastq                      Output in fastq format.
      --emit-sam                        Output in SAM format.
      --emit-cram                       Output in CRAM format. If set, reference must be FASTA(.gz).
      -o, --output-dir                  Output folder which becomes the root of the nested output folder structure.
    
    Alignment arguments:
      --reference                       Path to reference for alignment.
      --mm2-opts                        Optional minimap2 options string. For multiple arguments surround
                                          with double quotes.
      --bed-file                        Optional bed-file. If specified, overlaps between the alignments and bed-file entries will be counted, and recorded in BAM output using
                                          the 'bh' read tag.
    
    Modified model arguments:
      --modified-bases                  A space separated list of modified base codes. Choose from:
                                          pseU_2OmeU, pseU, 2OmeG, m6A_DRACH, 4mC_5mC, 5mC_5hmC, 5mCG, m6A, 5mCG_5hmCG, 5mC, inosine_m6A, m5C, 6mA, m5C_2OmeC, inosine_m6A_2OmeA.
      --modified-bases-models           A comma separated list of modified base model names or paths.
      --modified-bases-threshold        The minimum predicted methylation probability for a modified base to
                                          be emitted in an all-context model, [0, 1].
      --modified-bases-batchsize        The modified base models batch size.
    
    Advanced arguments:
      -t, --threads
      -b, --batchsize                   The number of chunks in a batch. If 0 an optimal batchsize will be selected.
    

Back to top 

## 文档章节: Modifications - Dorado Documentation

# Modified Basecalling

## Introduction

A modified nucleotide base is a nucleotide in which the canonical base (ACGTU) has undergone some chemical change. Modified nucleotide bases play crucial roles in various biological processes, including gene expression regulation, DNA repair, and the immune response.

Dorado supports modified basecalling and implements this as an extension to the normal `simplex` and `duplex` basecalling subcommands. In either case it can activated with the addition of a modified basecalling model as shown in the usage guide below.

### Supported modifications

The modifications listed here are **not** necessarily available for all model speeds, and / or versions.

Please check the **[Models List](../../models/list/)** for which modifications are available.

#### DNA modifications

Mod | Name | SAM Code | CHEBI  
---|---|---|---  
**5mC** | 5-Methylcytosine | `C+m` | [CHEBI:27551](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:27551)  
**5hmC** | 5-Hydroxymethylcytosine | `C+h` | [CHEBI:76792](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:76792)  
**4mC** | N(4)-methylcytosine | `C+21839` | [CHEBI:21839](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:21839)  
**6mA** | 6-Methyladenine | `A+a` | [CHEBI:28871](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:28871)  
  
#### RNA modifications

Mod | Name | SAM Code | CHEBI  
---|---|---|---  
**m5C** | 5-Methylcytosine | `C+m` | [CHEBI:27551](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:27551)  
**m6A** | N(6)-Methyladenosine | `A+a` | [CHEBI:21891](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:21891)  
**inosine** | Inosine | `A+17596` | [CHEBI:17596](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:17596)  
**pseU** | Pseudouridine | `T+17802` | [CHEBI:17802](https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:17802)  
  
### Modification context

Modified bases are modifications to one of the canonical bases (ACGTU). For example, `6mA` is a modified base which was originally a "canonical" `A` base.

Modified base models can be described as either being "all-context" or having some specific context known as a "motif".

All-context modified base models will predict the presence of one or more mods at all positions of its canonical base. Motif modified base models (which are not all-context) will only call mods at the positions of their specific motif.

For example, given the two modified base models `5mC` and `5mCG` which both predict the presence of `5-Methylcytosine` on canonical `C` bases, the first is an all-context `C` model and the second is a `CG` motif model.

The `5mC` all-context model will return predictions at all `C` positions while the `5mCG` model returns predictions on only `CG` motifs. Given the sequence `ACGTCA` the `5mC` model predicts at all `C` bases `aCgtCa`. The `5mCG` model returns predictions at the only `CG` motif `aCgtca`.

Multiple modification models must use different canonical bases

When selecting multiple modification models, only one modification model per canonical base may be active at once.

For example, `sup,4mC_5mC,5mC_5hmC` is invalid as **both** modification models operate on the `C` canonical base context.

### SAM tags `MM` / `ML`

The SAM tags [specification](https://samtools.github.io/hts-specs/SAMtags.pdf) has a detailed section on "Base Modifications" which describes in detail how modifications are annotated in the SAM/BAM/CRAM output from Dorado.

### Modified bases threshold

The `--modified-bases-threshold` argument takes a value (float) in the interval `[0, 1]` and controls how the `ML` and `MM` sam tags are written to the output. Specifically, it sets the _probability_ threshold that a modification must exceed to be written to the output. It has no effect on the modification probabilities.

For example, if we were mod basecalling `5mC` and the `--modified-bases-threshold` were set to `0` we could generate
    
    
    MM:Z:C+m?,0,0,0,0,0; ML:B:C,1,63,127,32,255
    

Note that there are no skipped positions (non-zero values) in the `MM` tag.

Setting `--modified-bases-threshold 0.45` would mean that the modified base probabilities below `0.45 * 256 := 115` (converting to int8) are omitted from the output resulting in the following SAM tags:
    
    
    MM:Z:C+m?,2,1; ML:B:C,127,255
    

### Post processing

[Modkit](https://github.com/nanoporetech/modkit) is a tool for working with modified bases. Documentation for Modkit can be found [here](https://nanoporetech.github.io/modkit/).

* * *

## Usage

See here for documentation on [model selection](../../models/selection/) which includes examples of [modified bases model selection](../../models/selection/#selecting-modified-base-models).

Both Dorado `basecaller` (simplex) and `duplex` tools support modified basecalling and they share a common interface for selecting which modifications to call.

The CLI arguments used to control which modified base models run are shown in the [simplex](../simplex/#cli-reference) and [duplex](../duplex/#cli-reference) CLI references and the relevant _and shared_ sections of which has been copied below:
    
    
    Modified model arguments:
      --modified-bases            A **space separated** list of modified base codes. Choose from:
                                    pseU, 5mCG_5hmCG, 5mC, 6mA, 5mCG, m6A_DRACH, m6A, 5mC_5hmC, 4mC_5mC.
                                    // More modified base model may be available
    
      --modified-bases-models     A **comma separated** list of modified base model names or paths
      --modified-bases-threshold  The minimum predicted methylation probability for a modified base
                                    to be emitted in an all-context model, [0, 1].
    

Please see the [models list](../../models/list/) for the complete set of canonical and modified base basecalling models.

Back to top 

## 文档章节: Moves Table - Dorado Documentation

# Move Table

The move table is a record of the model's base emissions in strided signal space and gives a coarse sequence-to-signal mapping. A `1` in the move table indicates the emission of a base at the indexed position in the signal, while a `0` in the move table indicates that section of signal is not associated with the emission of a base. The move table length is equal to the number of strided signal blocks.

The move table is stored in the original signal direction starting after any [trimmed signal `ts`](../read_splitting/). Since the move table is always in signal direction, it is not changed for alignments to reverse-complement references or for 3'->5' reads which have their sequences reversed to the 5'->3' direction at write-time. 

It can be added to SAM/BAM/CRAM outputs by setting the `--emit-moves` flag.

## Move table metadata format

The format of the move table metadata SAM/BAM/CRAM tag is as follows:
    
    
    mv:B:c,[block_stride],[signal_block_move_list]
    

`block_stride`: An `int8_t` containing the number of source signal samples which each element in the `signal_block_move_list` corresponds to. This will be set to the input **stride** of the model.

`signal_block_move_list`: A comma separated list of `int8_t` samples, each one containing a single move table element (unless overflow has occurred, see implementation details below). Each element corresponds to `block_stride` samples of the raw source signal.

The move table entries will be stored in order in successive `int8_t`s of the `signal_block_move_list`.

For example:
    
    
    Stride     : 5
    Move Table : 0,0,1,0,1
    SAM Tag    : mv:B:c,5,0,0,1,0,1
    

Implementation details

As the metadata is signed, each individual element supports values in the range -128 to 127. In order to be able to store values outside this range, if a single element in the metadata has the value -128 or 127, then the next entry in the metadata should be added to the current one, in order to reconstruct the original value.

For example:
    
    
    Stride     : 5
    Move Table : -400,200
    SAM Tag    : mv:B:c,5,0,-128,-128,-128,-16,127,73
    

Note that the exact value -128 or 127 (or multiples thereof) requires a trailing zero for the format to be encoded correctly.

For example:
    
    
    Stride     :5
    Move Table : -128,127,-256,254
    SAM Tag    : mv:B:c,5,0,-128,0,127,0,-128,-128,0,127,127,0
    

### Example

Given the above example move table: `mv:B:c,5,0,0,1,0,1`

The block stride is `5` (the first value) and the remaining values `0,0,1,0,1` state that the emitted bases occurred in the 3rd and 5th strided blocks.

Converting strided blocks into signal space (`[0-4,5-9,10-14,15-19,20-24]`) we can state that these bases were emitted from the 10th-14th and 20th-24th signal samples respectively.

Back to top 

## 文档章节: Poly(A) Estimation - Dorado Documentation

# Poly(A) Estimation

Dorado has initial support for estimating poly(A) tail lengths for cDNA (PCS and PCB kits) and RNA, and can be configured for use with custom primer sequences, interrupted tails, and plasmids.

Poly(A) and Poly(T)

Oxford Nanopore cDNA reads are sequenced in two different orientations and Dorado poly(A) tail length estimation handles both (A and T homopolymers).

This feature can be enabled by setting `--estimate-poly-a` argument which is disabled by default.

The estimated tail length is stored in the `pt:i` tag of the output record. Reads for which the tail length could not be estimated will have a value of -1 for the `pt:i` tag if the primer anchor for the tail was not found, or a value of 0 if the primer anchor was found, but the length could not be estimated.

Dorado **does not** edit the original basecalled sequence using the results of the poly(A/T) estimate.

## Custom poly(A) tail configuration

The default settings for this feature are optimized for non-interrupted poly(A/T) sequences that occur at read ends but these setting can be configured using a configuration file which is passed into Dorado using the `--poly-a-config` argument.

This configuration file can configure parameters for:

  * Custom primer sequence for cDNA tail estimation
  * Clustering of interrupted poly(A/T) tails
  * Estimation of poly(A/T) length in plasmids

## Poly(A/T) reference diagram

cDNA
    
    
     5' --- ADAPTER --- FRONT_PRIMER
    ... --- cDNA
    ... --- poly(A) --- RC(REAR_PRIMER) --- 3'
    
    OR
    
     5' --- ADAPTER --- REAR_PRIMER  --- poly(T)
    ... --- RC(cDNA)
    ... --- RC(FRONT_PRIMER) --- 3'
    

dRNA
    
    
    3' --- ADAPTER --- poly(A) --- RNA --- 5'
    

Plasmid
    
    
     5' --- ADAPTER
    ... --- DNA
    ... --- FRONT_FLANK --- poly(A) --- REAR_FLANK
    ... --- DNA --- 3'
    
    OR
    
     5' --- ADAPTER
    ... --- RC(DNA)
    ... --- RC(REAR_FLANK) --- poly(T) --- RC(FRONT_FLANK)
    ... --- RC(DNA) --- 3'
    

## Configuration format

The poly(A) configuration file uses the `toml` format.

The content of the file depends on the application i.e. cDNA or plasmids.

cDNAPlasmid

polya_config.cdna.toml
    
    
    [anchors]
    front_primer = "ATCG"
    rear_primer = "CGTA"
    primer_window = 150
    
    [threshold]
    flank_threshold = 0.6
    
    [tail]
    tail_interrupt_length = 10
    

polya_config.plasmid.toml
    
    
    [anchors]
    plasmid_front_flank = "CGATCG"
    plasmid_rear_flank = "TGACTGC"
    primer_window = 150
    
    [threshold]
    flank_threshold = 0.6
    
    [tail]
    tail_interrupt_length = 10
    

### Overrides

Configuration options can be overridden for individual barcodes. We generate a default configuration as normal, and then add overrides of specific values for each barcode by adding an `[[overrides]]` section labelled by the barcode name.

polya_config.toml
    
    
    [anchors]
    front_primer = "ATCG"
    rear_primer = "CGTA"
    [threshold]
    flank_threshold = 0.6
    [tail]
    tail_interrupt_length = 5
    
    [[overrides]]
    barcode_id = "Custom-Kit_barcode01"
    [overrides.threshold]
    flank_threshold = 0.5       # overrides 0.6
    
    [[overrides]]
    barcode_id = "Custom-Kit_barcode02"
    [overrides.anchors]
    front_primer = "AACC"       # overrides ATCG
    rear_primer = "GGTT"        # overrides CGTA
    [overrides.tail]
    tail_interrupt_length = 10  # overrides 5
    
    [[overrides]]
    barcode_id = "Custom-Kit_barcode03"
    [overrides.status]
    enabled = false             # disables polyA estimation for barcode03
    

This creates four configurations:

  * a default configuration with custom front and rear primers and an interrupt length of 5
  * a configuration to use for `barcode01` from kit `Custom-Kit` almost identical to the main custom settings (i.e. with the custom front and rear primers and the interrupt length), with an additional change to the `flank_threshold`.
  * a configuration to use for `barcode02` from kit `Custom-Kit` with different primers and an interrupt length of 10, but with no change to the flank threshold.
  * a configuration that skips polyA/T estimation for reads classified as `barcode03` from `Custom-Kit`.

Note that setting `[status] enabled = false` at the top level will disable polyA/T estimation for all reads classified with a barcode that is not explicitly overridden. Overridden barcodes are still enabled by default. 
    
    
    [status]
    enabled = false
    
    [[overrides]]
    barcode_id = "Custom-Kit_barcode02"
    [overrides.anchors]
    front_primer = "AACC"
    rear_primer = "GGTT"
    [overrides.tail]
    tail_interrupt_length = 10
    

This disables polyA/T estimation for all reads _except_ those classified as `barcode02`.

### Configuration options

Config Group | Option | Description  
---|---|---  
anchors | front_primer | Front primer sequence for cDNA[1]  
anchors | rear_primer | Rear primer sequence for cDNA[1]  
anchors | plasmid_front_flank | Front flanking sequence of poly(A) in plasmid[2]  
anchors | plasmid_rear_flank | Rear flanking sequence of poly(A) in plasmid[2]  
anchors | primer_window | Window of bases at the front and rear of the rear within which to look for primer sequences  
anchors | min_primer_separation | Minimum difference in edit distance required between the forward and reverse alignments of the primers in order to proceed with estimation (default: 10)  
threshold | flank_threshold | Threshold to use for detection of the flank/primer sequences. Equates to `(1 - edit distance / flank_sequence)`  
tail | tail_interrupt_length | Combine tails that are within this distance of each other (default is 0, i.e. don't combine any)  
status | enabled | Enables polyA/T estimation for the specific barcode (in the case of `overrides`) or for unspecified barcodes (default: true)  
  
  1. For cDNA only - Values ignored if either `plasmid_front_flank` or `plasmid_rear_flank` are set.
  2. For plasmids only

Back to top 

## 文档章节: Q-score - Dorado Documentation

# Q-scores

Phred Quality Score, often shortened to Q-score, is a metric describing the probability of an incorrect base call in a sequence. The higher the Q-score, the better.

Q-score `Q` is defined below where `P` is the basecalling error probability:
    
    
    Q = -10 * log10(P)
    

Conversely:
    
    
    P = 10 ^ (-Q/10)
    

For example, if the basecalling error probability `P` is `1/1000 := 10^(-3)` then we get Q30.
    
    
    Q = -10 * log10( 1/1000 )
      = -10 * log10( 10^(-3) )
      = -10 * (-3)
      = 30
    

Alternatively, if the basecalling accuracy `A` is 99% we get Q20 as `A = 1 - P`:
    
    
    Q = -10 * log10 ( 1 - (99/100) )
      = -10 * log10 ( 1 - 0.99 )
      = -10 * log10 ( 0.01 )
      = -10 * log10 ( 10^(-2) )
      = -10 * (-2)
      = 20
    

## Q-string

Per-base Q-scores for a given sequence are encoded as [ASCII](https://www.ascii-code.com/) characters which forms a string. This is known as the Q-string. The encoding spans `!` to `~` representing 0 to 93 (inclusive) respectively.

In practice, Dorado reports a maximum Q-score of 50 which is `S` (upper case).
    
    
    !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
    | ------------- Dorado Range [0, 50] ------------ |
    

To calculate the the Q-score from a Q-string character subtract `33` from the ASCII decimal value (`ASCII(33) = !`).

Tip

In Python - use the `ord` built-in to convert a ASCII character to its decimal value.
    
    
    assert ord("S") == 50
    

## Mean Q-score calculation in Dorado

Given a Q-string which is generated by Dorado during basecalling and represents Dorado's confidence in the basecall, the mean Q-score calculation is performed as follows:
    
    
    1.  Trim the leading 60 bases if the sequence is longer than 60 bases.
    2.  Convert the Q-scores into error probabilities
    3.  Calculate the mean of the error probabilities
    4.  Convert the mean error probability into mean Q-score
    

The leading 60 bases are trimmed to account for the higher than normal noise at the beginning of sequencing.

Below is an example Python snippet calculating the mean Q-score from a Q-string.
    
    
    import math
    
    def mean_qscore(qstring: str) -> float:
        """Calculates mean Q-score from a Q-string"""
        # Truncate string if sufficiently long
        qstr = qstring[60:] if len(qstring) > 60 else qstring
        # Convert ASCII to Phred quality scores, then to estimated error
        errors = [10**(-(ord(char) - 33)/10) for char in qstr]
        # Calculate mean error
        mean_error = sum(errors) / len(errors)
        # Convert back to q-score
        mean_qscore = -10 * math.log10(mean_error)
        return mean_qscore
    
    # Example quality string
    qstring = ";;;;;?<<<?GJI>>>>>>=<=<<=>>A@A??@==<8889?>=<<<;<<;;?==<;::;;<SS:::7666444<2+')933;<<=???CA?>=>=>>??51)))+&&(('&&&&''))HELLO;READER;'()))))&%%$"
    print(mean_qscore(qstring))
    # 10.380942270316051
    

Back to top 

## 文档章节: Read Splitting - Dorado Documentation

# Read Splitting

Dorado performs read splitting automatically but it can be disabled with the `--disable-read-splitting` argument.

When a single input read contains multiple concatenated reads, Dorado `basecaller` will split the original input read into separate subreads. This operation is performed by default for both DNA and RNA.

Each subread has a new read id that is assigned by Dorado.

The following tags can be used to associate a subread to its parent:

Tag | Description  
---|---  
`pi:Z` | The parent read id that this subread was generated from.  
`sp:i` | Maps the start of the subread's signal data to the corresponding location in the parent read's signal data.  
`ns:i` | The number of samples corresponding to the subread after splitting.  
`ts:i` | The number samples trimmed from the start of subread's signal after splitting.  
  
Back to top 

## 文档章节: Read Trimming - Dorado Documentation

# Read Trimming

Dorado can trim adapters and/or primer sequences from the beginning and end of DNA and RNA reads during basecalling

For DNA basecalls only, trimming can be done as a separate step after basecalling using the Dorado `trim` subcommand.

RNA trimming

RNA trimming is always done in-line with basecalling and cannot be done afterwards using Dorado `trim`.

Demultiplexing trimmed data

Trimming adapters and primers may result in parts of the barcode flanking regions being removed, which could interfere with demultiplexing.

## Trimming while basecalling

Dorado `basecaller` will attempt to detect any adapter or primer sequences at the beginning and end of reads, and remove them from the output sequence. The sequences searched for will depend on the sequencing-kit used, which is normally embedded as metadata within pod5 files. Note that by default only kit14 sequencing kits are supported, so if an older or non-standard kit was used, no adapter or primer trimming will be performed.

Dorado will also attempt to infer the orientation of the read from any detected primers. If the orientation can be inferred, then the output BAM record for the read will include the `TS:A:[+/-]` tag, with a `+` indicating 5' to 3' orientation, and a `-` indicating 3' to 5' orientation.

In the specific cases of the SQK-PCS114 and SQK-PCB114 sequencing kits, if a UMI tag is present, it will also be detected and trimmed. Additionally, the UMI tag, if found, will be included in the BAM output for the read using the `RX:Z` tag.

This functionality can be controlled using either the `--trim` or `--no-trim` options with Dorado `basecaller`. Note that if primer trimming is not enabled, then no attempt will be made to detect primers, or to classify the orientation of the strand based on them, or to detect UMI tags.

The `--trim` option takes as its argument one of the following values:

Option | Adapters | Primers | Barcodes | Description  
---|---|---|---|---  
`all` |  |  |  | Detected adapters or primers will be trimmed.  
If barcoding is enabled, detected barcodes will be trimmed.  
This is the default option  
`adapters` |  |  |  | Detected adapters will be being trimmed, but primers will **not** be trimmed.  
If barcoding is enabled, detected barcodes will **not** be trimmed.  
`none` |  |  |  | Nothing will be trimmed. Equivalent to `--no-trim`  
  
## Trimming existing datasets

The Dorado `trim` subcommand can be used to trim adapters and/or primer sequences in existing basecalled datasets. To do this, run:
    
    
    dorado trim <calls> --sequencing-kit <kit> > trimmed.bam
    

`<calls>` can either be an HTS format file (e.g. FASTQ, BAM, etc.) or a stream of an HTS format (e.g. the output of Dorado basecalling).

`<kit>` must be provided to specify the sequencing kit used, since this is not encoded in FASTQ or BAM files.
    
    
    dorado basecaller <model> <reads> ... | dorado trim --sequencing-kit <kit> > trimmed.bam
    

The `--no-trim-primers` option can be used to prevent the trimming of primer sequences. In this case only adapter sequences will be trimmed.

If it is also your intention to demultiplex the data, then it is recommended that you demultiplex before trimming any adapters and primers, as trimming adapters and primers first may interfere with correct barcode classification.

The output of Dorado `trim` will always be unaligned records, regardless of whether the input is aligned/sorted or not.

### CLI reference
    
    
    Positional arguments:
      reads               Path to a file with reads to trim. Can be in any HTS format.
    
    Required arguments:
      -k, --sequencing-kit  Sequencing kit name to use for selecting adapters and primers to trim.
    
    Optional arguments:
      -h, --help          shows help message and exits
      -v, --verbose       [may be repeated]
      -t, --threads       Combined number of threads for adapter/primer detection and output generation.
                            Default uses all available threads.
    Input arguments:
      -n, --max-reads     Maximum number of reads to process.
      -l, --read-ids      A file with a newline-delimited list of reads to trim.
    
    Output arguments:
      --emit-fastq        Output in fastq format. Default is BAM.
    
    Main arguments:
      --no-trim-primers   Skip primer detection and trimming. Only adapters will be detected and trimmed.
      --primer-sequences  Path to file with custom primer sequences.
    

## Custom primer trimming

Note

Using the `--primer-sequences` argument will remove the Oxford Nanopore primer sequences from the trimming search.

Dorado automatically searches for primer sequences used in Oxford Nanopore kits. However, you can specify an alternative set of primer sequences to search for when trimming either in-line with basecalling, or in combination with the `--trim` option. In both cases this is accomplished using the `--primer-sequences` command line option. The argument can be either the full path and filename of a FASTA file containing the primer sequences you want to search for, or a string code specifying a supported 3rd-party primer set.

If a FASTA file is specified, then the file must have either the `.fa` or `.fasta` extension and must conform to the [specification](../../barcoding/custom_primers/).

The `--help` option will list the supported 3rd-party primer sets. Currently the only 3rd-party primer set supported is the set of primers used for 10X Genomics sequencing. Support for detecting and trimming these primers can be enabled by using:

`--primer-sequences 10X_Genomics`

In this case, in addition to detecting and trimming the primers, Dorado will extract the section of the read corresponding to the cell-barcodes and UMI tags and place it in the RX:Z BAM tag.

## Effect on demultiplexing

If adapter/primer trimming is done while basecalling in combination with demultiplexing, then Dorado will ensure that the trimming of adapters and primers does not interfere with the demultiplexing process.

For example, trimming will not effect demultiplexing on `kit-name` in the following command:
    
    
    dorado basecaller <model> reads/ --kit-name <kit-name> --trim all
    

However, if you intend to do demultiplexing as a separate step, it is recommended that trimming is disabled when basecalling with the `--no-trim` option, to ensure that barcode sequences remain intact in the calls.
    
    
    dorado basecaller <model> <reads> --no-trim ... > calls.bam
    dorado demux calls.bam --kit-name <kit-name> --output-dir <output-dir> ...
    

Back to top 

## 文档章节: SAM Specification - Dorado Documentation

# SAM specification

## Header
    
    
    @HD  VN:1.6  SO:unknown
    @PG  ID:basecaller PN:dorado VN:0.2.4+3fc2b0f CL:dorado basecaller hac pod5/ DS:gpu:Quadro GV100
    

## Read Group Header

Tag | Description  
---|---  
`ID` | `<runid>_<basecalling_model>_<barcode_arrangement>`  
`PU` | `<flow_cell_id>`  
`PM` | `<device_id>`  
`DT` | `<exp_start_time>`  
`PL` | `ONT`  
`DS` | `runid=<run_id> basecall_model=<basecall_model_name> modbase_models=<modbase_model_names> experiment_id=<experiment_id> acquisition_start_time=<acquisition_start_time> model_stride=<model_stride>`  
`LB` | `<sample_id>`  
`SM` | `<barcode_name>` (only if barcoding, and barcode is not "unclassified")  
`al` | `<barcode_alias>` (only if barcoding, same as `SM` tag if no alias)  
`bk` | `<barcode_kit>` (only if barcoding, and barcode is not "unclassified")  
  
## Read Tags

Tag | Description  
---|---  
`RG:Z:` | `<runid>_<basecalling_model>_<barcode_arrangement>`  
`qs:f:` | mean basecall q-score  
`ts:i:` | the number of samples trimmed from the start of the signal  
`ns:i:` | the basecalled sequence corresponds to the interval `signal[ts : ns]`   
the move table maps to the same interval.   
note that `ns` reflects trimming (if any) from the rear   
of the signal.  
`mx:i:` | read mux  
`ch:i:` | read channel  
`rn:i:` | read number  
`st:Z:` | read start time (in UTC)  
`du:f:` | duration of the read (in seconds)  
`fn:Z:` | file name  
`sm:f:` | scaling midpoint/mean/median (pA to ~0-mean/1-sd)  
`sd:f:` | scaling dispersion (pA to ~0-mean/1-sd)  
`sv:Z:` | scaling version  
`mv:B:c` | sequence to signal move table _(optional)_  
`dx:i:` | bool to signify duplex read _(only in duplex mode)_  
`pi:Z:` | parent read id for a split read  
`sp:i:` | start coordinate of split read in parent read signal  
`bh:i:` | number of detected bedfile hits _(only if alignment was performed with a specified bed-file)_  
`me:I:` | number of minknow_events identified during sequencing  
`po:Z:` | pore type  
`er:Z:` | the reason the read ended  
`bv:Z:` | the variant of the detected barcode arrangement  
`bi:B:f` | an array of barcode info arranged as  
`[score, front_begin_index, front_seq_length, front_score, rear_end_index, rear_seq_length, rear_score]`  
  
### Poly(A/T) Tags

When `dorado` is run with poly(A/T) estimation enabled, additional tags are added to each SAM record as follows:

  * `pt:i` is the estimated poly(A/T) tail length in cDNA and dRNA reads
  * `pa:B:i` is an array of signal positions related to the poly(A/T) estimation, in order:
    * The position in the signal used as the anchor for the poly(A/T) search
    * The start of the poly(A/T) region
    * The end of the poly(A/T) region
    * The the start of a secondary poly(A/T) region in the case of plasmids, (-1 otherwise or if not found)
    * The end of a secondary poly(A/T) region in the case of plasmids, (-1 otherwise or if not found)

Back to top 

## 文档章节: Simplex - Dorado Documentation

# Simplex Basecalling

## Quick start

To run Dorado basecalling, using the [automatically downloaded](../../models/selection/) `hac` model on a directory of POD5 files or a single POD5 file use:
    
    
    dorado basecaller hac pod5s/ > calls.bam
    

To basecall a single file, simply replace the directory `pod5s/` with a path to your data.
    
    
    dorado basecaller hac /path/to/reads.pod5 > calls.bam
    

To automatically download and use the `fast` or `sup` models try the following:
    
    
    dorado basecaller fast pod5s/ > calls.bam
    dorado basecaller sup  pod5s/ > calls.bam
    

If you have a model that has already been [downloaded](../../models/downloader/) you can specify that **simplex** model using a path. For more information on how models are downloaded and how they can be re-used please see the [downloader documentation](../../models/downloader/#downloading-models).
    
    
    dorado basecaller /path/to/simplex_model/ pod5s/ > calls.bam
    

### Adding modified bases

To add modified basecalling extend the [variant model complex](../../models/selection/#model-selection-via-variant) or refer to [modified basecalling model selection](../../models/selection/#selecting-modified-base-models) for more details on the other options available.
    
    
    dorado basecaller hac,5mC     pod5s/ > calls.bam
    dorado basecaller sup,6mA,5mC pod5s/ > calls.bam
    

### Selecting data

To basecall all reads in a nested directory structure [recursively](../basecall_overview/#data-ingest) use `-r / --recursive`:
    
    
    dorado basecaller hac data/ --recursive  > calls.bam
    

To basecall only a limited number reads use the `-n / --max-reads` argument:
    
    
    dorado basecaller hac data/ --max-reads 100  > calls.bam
    

Tip

You can generate a list of read ids using the [`pod5 view` tool](https://pod5-file-format.readthedocs.io/en/latest/docs/tools.html#pod5-view).

To basecall a specific selection of reads use the `-l / --read-ids` argument passing in a file path to a newline-delimited list of read ids. Only these read ids will be basecalled.
    
    
    dorado basecaller hac data/ --read-ids read_ids.txt > calls.bam
    

### Resume basecalling

If basecalling is interrupted, it is possible to resume basecalling from a BAM file. To do so, use the `--resume-from` flag to specify the path to the incomplete BAM file.
    
    
    dorado basecaller hac pod5s/ --resume-from incomplete.bam > calls.bam
    

Warning

Do not reuse the filenames for `--resume-from` and the new output.

If they are the same then the interrupted file will be **deleted** when Dorado is launched and the previous work will be lost.
    
    
    # WARNING: This will overwrite the existing `resume.bam` file before it is used.
    dorado basecaller hac pod5/ --resume-from resume.bam > resume.bam
    

## Read trimming

See [read trimming](../read_trimming/).

## Output Folder Structure

If the `--output-dir <DIR>` argument is set, Dorado `basecaller` will write output files into a nested folder structure following the [MinKnow output structure specifications](https://nanoporetech.github.io/ont-output-specifications/latest/minknow/output_structure/).

The chosen directory `<DIR>` becomes the root of the nested folder structure and replaces `/data/` in the specification examples.

Reads with mean Q-score below the `--min-qscore` threshold are written to the files marked `fail`. If `--min-qscore` is not set, a default threshold of `0` is used and all reads are written to files marked `pass`.

* * *

## CLI reference

Here's a slightly re-formatted output from the Dorado `basecaller` subcommand for reference.

Info

Please check the `--help` output of your own installation of Dorado as this page may be outdated and argument defaults have been omitted as they are platform specific.
    
    
    > dorado basecaller --help
    
    Positional arguments:
      model                             Model selection {fast,hac,sup}@v{version} for automatic model selection including modbases, or path to existing model directory.
      data                              The data directory or POD5 file path.
    
    Optional arguments:
      -h, --help                        shows help message and exits
      -v, --verbose                     [may be repeated]
      -x, --device                      Specify CPU or GPU device: 'auto', 'cpu', 'cuda:all' or 'cuda:<device_id>[,<device_id>...]'.
                                          Specifying 'auto' will choose either 'cpu', 'metal' or 'cuda:all' depending
                                          on the presence of a GPU device.
      --models-directory                Optional directory to search for existing models or download new models into.
    
    Input data arguments:
      -r, --recursive                   Recursively scan through directories to load POD5 files.
      -l, --read-ids                    A file with a newline-delimited list of reads to basecall. If not provided,
                                          all reads will be basecalled.
      -n, --max-reads                   Limit the number of reads to be basecalled.
      --resume-from                     Resume basecalling from the given HTS file. Fully written read records are
                                          not processed again.
      --disable-read-splitting          Disable read splitting
    
    Output arguments:
      --min-qscore                      Discard reads with mean Q-score below this threshold or write them to output files marked `fail` if `--output-dir` is set.
      --emit-moves                      Write the move table to the 'mv' tag.
      --emit-fastq                      Output in fastq format.
      --emit-sam                        Output in SAM format.
      --emit-cram                       Output in CRAM format. If set, reference must be FASTA(.gz).
      --emit-summary                    If specified, a summary file containing the details of the primary alignments for each read will be emitted to the root of the --output-dir folder. If --output-dir is not set, the summary file is placed in the current working directory.
      -o, --output-dir                  Output folder which becomes the root of the nested output folder structure.
    
    Alignment arguments:
      --reference                       Path to reference for alignment.
      --bed-file                        Optional bed-file. If specified, overlaps between the alignments and
                                          bed-file entries will be counted, and recorded in BAM output using
                                          the 'bh' read tag.
      --mm2-opts                        Optional minimap2 options string. For multiple arguments surround with
                                          double quotes.
    
    Modified model arguments:
      --modified-bases                  A space separated list of modified base codes. Choose from:
                                          pseU_2OmeU, pseU, 2OmeG, m6A_DRACH, 4mC_5mC, 5mC_5hmC, 5mCG, m6A, 5mCG_5hmCG, 5mC, inosine_m6A, m5C, 6mA, m5C_2OmeC, inosine_m6A_2OmeA.
    
      --modified-bases-models           A comma separated list of modified base model names or paths.
      --modified-bases-threshold        The minimum predicted methylation probability for a modified base
                                          to be emitted in an all-context model, [0, 1].
      --modified-bases-batchsize        The modified base models batch size.
    
    Barcoding arguments:
      --kit-name                        Enable barcoding with the provided kit name. Choose from:
                                          EXP-NBD103 EXP-NBD104 EXP-NBD114 EXP-NBD114-24 EXP-NBD196 EXP-PBC001
                                          EXP-PBC096 SQK-16S024 SQK-16S114-24 SQK-DRB004-24 SQK-HTB114-96 SQK-LWB001
                                          SQK-MAB114-24 SQK-MLK111-96-XL SQK-MLK114-96-XL SQK-NBD111-24 SQK-NBD111-96
                                          SQK-NBD114-24 SQK-NBD114-96 SQK-PBK004 SQK-PCB109 SQK-PCB110 SQK-PCB111-24
                                          SQK-PCB114-24 SQK-RAB201 SQK-RAB204 SQK-RBK001 SQK-RBK004 SQK-RBK110-96
                                          SQK-RBK111-24 SQK-RBK111-96 SQK-RBK114-24 SQK-RBK114-96 SQK-RLB001 SQK-RPB004
                                          SQK-RPB114-24 TWIST-16-UDI TWIST-96A-UDI VSK-PTC001 VSK-VMK001 VSK-VMK004 VSK-VPS001.
      --sample-sheet                    Path to the sample sheet to use.
      --barcode-both-ends               Require both ends of a read to be barcoded for a double ended barcode.
      --barcode-arrangement             Path to file with custom barcode arrangement. Requires --kit-name.
      --barcode-sequences               Path to file with custom barcode sequences. Requires --kit-name and --barcode-arrangement.
      --primer-sequences                Path to fasta file with custom primer sequences, or the name of a supported 3rd-party primer set. If specifying a supported primer set, choose from: 10X_Genomics.
    
    Trimming arguments:
      --no-trim                         Skip trimming of barcodes, adapters, and primers.
                                          If option is not chosen, trimming of all three is enabled.
      --trim                            Specify what to trim. Options are 'none', 'all', and 'adapters'.
                                          The default behaviour is to trim all detected adapters, primers, and barcodes.
                                          Choose 'adapters' to just trim adapters. The 'none' choice is equivalent to using --no-trim.
                                           Note that this only applies to DNA. RNA adapters are always trimmed.
    
    Poly(A) arguments:
      --estimate-poly-a                 Estimate poly(A)/poly(T) tail lengths (beta feature).
                                          Primarily meant for cDNA and dRNA use cases.
      --poly-a-config                   Configuration file for poly(A) estimation to change default behaviours
    
    Advanced arguments:
      -b, --batchsize                   The number of chunks in a batch. If 0 an optimal batchsize will be selected.
    

Back to top 

## 文档章节: Dorado Documentation

# Getting started

## Installation

### From the web

Dorado 1.4.0 can be installed from pre-built binaries for multiple platforms using the following links:

  * [dorado-1.4.0-linux-x64](https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-x64.tar.gz)
  * [dorado-1.4.0-linux-arm64-cuda12](https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-arm64.tar.gz) \- Orin only
  * [dorado-1.4.0-linux-arm64-cuda13](https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-arm64-cuda-13.0.tar.gz) \- Jetson Thor / DGX Spark
  * [dorado-1.4.0-osx-arm64](https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-osx-arm64.zip)
  * [dorado-1.4.0-win64](https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-win64.zip)

Once the relevant `.tar.gz` or `.zip` archive has been downloaded, extract the archive to your desired location.

### From the command line

Linux x86Linux arm64 (CUDA 12 - Orin only)Linux arm64 (CUDA 13 - Jetson Thor / DGX Spark)MacOS

Navigate to the desired install path and run:
    
    
    curl "https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-x64.tar.gz" -o dorado-1.4.0-linux-x64.tar.gz
    tar -xzf dorado-1.4.0-linux-x64.tar.gz
    dorado-1.4.0-linux-x64/bin/dorado --version
    

Navigate to the desired install path and run:
    
    
    curl "https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-arm64.tar.gz" -o dorado-1.4.0-linux-arm64.tar.gz
    tar -xzf dorado-1.4.0-linux-arm64.tar.gz
    dorado-1.4.0-linux-arm64/bin/dorado --version
    

Navigate to the desired install path and run:
    
    
    curl "https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-linux-arm64-cuda-13.0.tar.gz" -o dorado-1.4.0-linux-arm64-cuda-13.0.tar.gz
    tar -xzf dorado-1.4.0-linux-arm64-cuda-13.0.tar.gz
    dorado-1.4.0-linux-arm64-cuda-13.0/bin/dorado --version
    

Navigate to the desired install path and run:
    
    
    curl "https://cdn.oxfordnanoportal.com/software/analysis/dorado-1.4.0-osx-arm64.zip" -o dorado-1.4.0-osx-arm64.zip
    unzip dorado-1.4.0-osx-arm64.zip
    dorado-1.4.0-osx-arm64/bin/dorado --version
    

### Supported platforms

Dorado has been tested extensively and supported on the following systems:

Platform | GPU/CPU | Minimum Software Requirements  
---|---|---  
Linux x86_64 | (G)V100, A100, H100 | CUDA Driver â¥525.105  
Linux arm64 | Jetson Orin, Jetson Thor, DGX Spark* | Linux for Tegra â¥36.4.3 (JetPack â¥6.2)  
Windows x86_64 | (G)V100, A100, H100 | CUDA Driver â¥529.19  
Apple | Apple Silicon (M series) | macOS â¥13  
  
*_DGX Spark supports all Dorado commands_ _except_ _Dorado`correct`. Support for Dorado `correct` on DGX Spark will be added in a future release._

Linux x86 or Windows systems not listed above but which have Nvidia GPUs with â¥8 GB VRAM and architecture from Pascal onwards (except P100/GP100) have not been widely tested but are expected to work. When basecalling with Apple devices, we recommend systems with â¥16 GB of unified memory.

If you encounter problems with running on your system, please [report an issue](https://github.com/nanoporetech/dorado/issues).

* * *

## Dorado command line interface (CLI) basics

Dorado is a command line tool and `dorado` is the name of the binary executable. If [installed](./#installation) correctly `dorado` will be on your `PATH` or installed into a known directory.

If `dorado` is installed into the `PATH` you should be able to view the top-level help as shown below.
    
    
    dorado --help
    

Alternatively, if `dorado` is in a known path or in the current working directory try:
    
    
    ./dorado --help
    /path/to/dorado --help
    

## Dorado subcommands

Dorado has multiple subcommands which are used to launch specific tools such as the `basecaller`. To view all available subcommands inspect the top-level help:
    
    
    > dorado --help
    Usage: dorado [options] subcommand
    
    Positional arguments:
    aligner
    basecaller
    correct
    demux
    download
    duplex
    summary
    trim
    
    Optional arguments:
    -h --help               shows help message and exits
    -v --version            prints version information and exits
    -vv                     prints verbose version information and exits
    

To launch a Dorado subcommand use the following structure:
    
    
    dorado <subcommand> --help > calls.bam
    

For example, to launch the `basecaller` use:
    
    
    dorado basecaller --help
    

## Redirecting output

There are many resources (see [gnu.org](https://www.gnu.org/software/bash/manual/html_node/Redirections.html)) which explain the details of output re-direction but below are some examples uses of re-direction in Dorado.

Some Dorado subcommands write their business logic output to `stdout` and other runtime information to `stderr`. Examples of business logic output may be basecalls in a BAM file generated during basecalling. To write these outputs to a file we must redirect the `stdout` output to a file.

Below is an example of writing the `stdout` output from Dorado `basecaller` (which by default is a BAM file) using the `>` redirection operator. The `stderr` (runtime information) will be written to the terminal as normal.
    
    
    dorado basecaller ... > calls.bam
    

Tip

To view the `my.log` info in real-time while it is being written by Dorado try:
    
    
    tail -f dorado.log
    

To write the `stderr` runtime information to a log file use the `2>` `stderr` redirection operator.
    
    
    dorado basecaller ... > calls.bam 2> dorado.log
    

Some Dorado subcommands can be "chained" together where the output of one is the input to the other. For example, Dorado `basecaller` can generate a BAM file which is an input to Dorado `demux` which can split this BAM file into files by barcode. This can be done with the `|` pipe operator.
    
    
    dorado basecaller ... | dorado demux --output demuxed
    

## Command line arguments

Dorado subcommands are controlled from the command line using arguments. The available arguments for a specific subcommand can be seen by using the `--help` argument as shown above.

Arguments are either **positional** or **optional**.

### Positional arguments

Positional arguments are arguments which must be specified in a specific position relative to others. The order of positional arguments matters. The dorado subcommand is an example of a positional argument as shown in the above examples.

Using Dorado `basecaller` as another example we can see following part of the `--help` output:
    
    
    Positional arguments:
      model    model selection {fast,hac,sup}@v{version} ...
      data     the data directory or file (POD5/FAST5 format).
    

Tip

We recommend always placing positional arguments **before** optional arguments.

This information is stating that we must place the `model` and `data` arguments in that order as shown:
    
    
    dorado basecaller hac reads/ > calls.bam
    

### Optional arguments

Note

Optional arguments may be **required** by the Dorado subcommand.

Optional arguments are arguments which **may or may not be required** , and may themselves require zero or more values as inputs. Optional arguments requiring no additional values are also know as "flags", "toggles" or "switches".

All optional arguments are prefixed by a double hyphen `--argument`.

Some optional arguments may have a one character abbreviation prefixed by a single hyphen such as `-a`. Throughout this documentation when describing optional arguments they will be shown as `-a / --argument` if an abbreviation exists.

Using Dorado `basecaller` again we can see following part of the `--help` output listing the optional arguments:
    
    
    Optional arguments:
      -h, --help         shows help message and exits
      -v, --verbose      [may be repeated]
      -x, --device       device string in format ...
      -l, --read-ids     A file with a newline-delimited list of reads ...
      ...
    

Here is a complete command with both positional and optional arguments:
    
    
    dorado basecaller hac reads/ --device cuda:0 --min-qscore 10 --reference reference.fasta --no-trim > calls.bam
    

Warning

Optional arguments which take **multiple values** cause issues with positional arguments.

As such they **must be placed after all positional arguments**.
    
    
    # Invalid - sup is consumed by --modified-bases
    dorado basecaller --modified-bases 5mC 6mA sup --device cuda:0 reads/
    
    
    
    # Valid
    dorado basecaller hac reads --modified-bases 5mC 6mA --device cuda:0
    

## Runtime information and verbose output

Dorado and its subcommands will generate some runtime information (logging) which is written to `stderr`. All subcommands have the `-v / --verbose` argument which can be used to increase the amount of information shown in these messages by adding `[debug]` messages to the output. The verbose output can be specified multiple times (e.g. `-vv`) to additionally include `[trace]` messages.

These messages are typically in the format shown below which contains a timestamp, message severity and the message.
    
    
    [2024-01-01 00:00:00.000] [trace] <detailed debug message - not useful in normal use - may affect performance>
    [2024-01-01 00:00:00.000] [debug] <debug message - likely not useful in normal use>
    [2024-01-01 00:00:00.000] [info] <useful information message>
    [2024-01-01 00:00:00.000] [warning] <warning message - there may be an issue>
    [2024-01-01 00:00:00.000] [error] <error message - there is significant issue>
    

It is **not recommended** to set any additional level of logging output (e.g. `-v` or `-vv`) in normal use as it can affect performance. However, if you experience an issue please first include a single `-v` while attempting to investigate the issue as it might yield insightful information which may otherwise be hidden.

If you create a ticket on our [GitHub issues](https://github.com/nanoporetech/dorado/issues) page, please add debugging output if possible.

## Specifying hardware resources

Many of Dorado's subcommands may be able to make use of modern GPU (Graphical Processing Unit) hardware (e.g. Nvidia CUDA GPUs). Dorado subcommands which support GPU acceleration will provide the `-x` / `--device` command line argument.

The valid values for the `-x` / `--device` argument are `auto`, `cpu`, `metal` (macOS) and `cuda:*` (Linux/Windows).

`auto` will attempt to determine the available GPU resources and select these if available (`metal` for macOS, `cuda:all` for Linux/Windows), or fall back to `cpu` if none are present.

The `*` in `cuda:*` can be used to select which specific CUDA devices are used.

Valid examples are:

  * `cuda:0` select the first (best) device - Devices are zero-indexed.
  * `cuda:1,2,3` select the second, third, and fourth device.
  * `cuda:all` and `cuda:auto` select **all** devices

Dorado recognises the environment variable `CUDA_VISIBLE_DEVICES`, which should be given as a comma-separated sequence of GPU identifiers. Identifiers may be either integers or UUIDs, but not both. Only the devices whose identifier is present in the sequence are visible to Dorado, and they are enumerated in the order of the sequence.

Valid examples are:

  * `CUDA_VISIBLE_DEVICES="0,1"` \- makes available GPU ids 0 and 1 as `cuda:0` and `cuda:1`
  * `CUDA_VISIBLE_DEVICES="2"` \- makes available GPU id 2 as `cuda:0`
  * `CUDA_VISIBLE_DEVICES="<UUID>"` \- makes available the GPU with the specified UUID as `cuda:0`

`cuda:all` will select all devices identified in this fashion.

If one of the identifiers is invalid, only the devices whose identifiers precede the invalid value are visible to Dorado. Invalid examples would be:

  * `CUDA_VISIBLE_DEVICES="0,<UUID>"` \- mixed integer index and UUID, only index 0 will be selected
  * `CUDA_VISIBLE_DEVICES="<UUID>,1"` \- mixed integer index and UUID, only UUID will be selected
  * `CUDA_VISIBLE_DEVICES="0,mygpu,1"` \- invalid identifier `mygpu`, only index 0 will be selected
  * `CUDA_VISIBLE_DEVICES="0,1,1"` \- duplicate identifier, no devices will be selected

Back to top 

## 文档章节: Downloading Models - Dorado Documentation

# Downloader

Dorado can download [models](../models/) from the Oxford Nanopore Content Delivery Network (CDN) using the Dorado `download` command.
    
    
    â¯ dorado download --help
    
    Usage: dorado [--help]
        [--model (<model_name>|"all")]
        [--models-directory PATH]
        [--list] [--list-yaml] [--list-structured]
        [--data VAR] [--recursive] [--overwrite] [--verbose]...
    
    Optional arguments:
      -h, --help          shows help message and exits
      --model             the model to download [nargs=0..1] [default: "all"]
      --models-directory  the directory to download the models into [nargs=0..1] [default: "."]
      --list              list the available models for download
      --list-yaml         list the available models for download, as yaml, to stdout
      --list-structured   list the available models in a structured format, as yaml, to stdout
      --data              path to POD5 data used to automatically select models [nargs=0..1] [default: ""]
      -r, --recursive     recursively scan through directories to load POD5 files
      --overwrite         overwrite existing models if they already exist
      -v, --verbose       [may be repeated]
    

## Downloading models

### Download all models

To download all models use:
    
    
    dorado download --model all
    

### Download models for a specific condition

To download models for a specific sequencing condition and model speed, provide a [variant model complex](../selection/#model-selection-via-variant) to the `--model` argument and set the `--data` argument to path to your pod5 input data (.fast5 is not supported).

Dorado will then download the simplex and modified base models matching the condition and model complex selection.
    
    
    dorado download --model hac --data pod5s/
    

### Download specific models

To find and download a specific model use the following command to view a list of all available models. These are also noted in the [Models List](../list/) below.
    
    
    dorado download --list
    

which shows an output like this where model names are printed for each model type
    
    
    > simplex models
     - dna_r10.4.1_e8.2_400bps_hac@v5.2.0
     - dna_r10.4.1_e8.2_400bps_sup@v5.2.0
     ...
    > modification models
     - dna_r10.4.1_e8.2_400bps_hac@v5.2.0_6mA@v1
     ...
    

The models can then be downloaded using their model name as shown below
    
    
    dorado download --model <model_name>
    

### Download models into a specific directory

By default Dorado `download` will download models into the current working directory. Use the `--models-directory` argument to specify a directory to save downloaded models into.

See also [model discovery](../selection/#model-discovery) for details on how previously downloaded models are found or automatically downloaded.
    
    
    dorado download --model <model_name> --models-directory /path/to/models_directory
    

Tip

The `--models-directory` argument is available on many Dorado commands (e.g. `basecaller`) to specify a directory to search for existing models. This can be used to avoid repeatedly downloading models.

Back to top 

## 文档章节: Models List - Dorado Documentation

# Models List

View all available models

To view all available models for your current installation of dorado use:
    
    
    dorado download --list
    

This page contains the list of available simplex and modified basecalling models.

Please read important information on [Understanding Model Names](../models/#understanding-model-names) especially the section on [Model Version Numbers](../models/#model-version-numbers).

The bolded models are for the **latest** released condition.

Deprecated models

The DNA R9.4.1 and RNA002 models were deprecated in Dorado v1.0.0 release.

[Help on basecalling legacy conditions](../../troubleshooting/faq/#how-do-i-basecall-data-from-legacy-sequencing-conditions).

## DNA Models

Basecalling Models | Compatible  
Modifications | Modifications  
Model  
Version | Data  
Sampling  
Frequency  
---|---|---|---  
**dna_r10.4.1_e8.2_400bps_fast@v5.2.0** |  |  | 5 kHz  
**dna_r10.4.1_e8.2_400bps_hac@v5.2.0** | 4mC_5mC  
5mCG_5hmCG  
5mC_5hmC  
6mA  
| v1  
v2  
v2  
v1 | 5 kHz  
**dna_r10.4.1_e8.2_400bps_sup@v5.2.0** | 4mC_5mC  
5mCG_5hmCG  
5mC_5hmC  
6mA  
| v1  
v2  
v2  
v1 | 5 kHz  
dna_r10.4.1_e8.2_400bps_fast@v5.0.0 |  |  | 5 kHz  
dna_r10.4.1_e8.2_400bps_hac@v5.0.0 | 4mC_5mC  
5mCG_5hmCG  
5mC_5hmC  
6mA  
| v3  
v3  
v3  
v3 | 5 kHz  
dna_r10.4.1_e8.2_400bps_sup@v5.0.0 | 4mC_5mC  
5mCG_5hmCG  
5mC_5hmC  
6mA  
| v3  
v3  
v3  
v3 | 5 kHz  
dna_r10.4.1_e8.2_400bps_fast@v4.3.0 |  |  | 5 kHz  
dna_r10.4.1_e8.2_400bps_hac@v4.3.0 | 5mCG_5hmCG  
5mC_5hmC  
6mA  
| v1  
v1  
v2 | 5 kHz  
dna_r10.4.1_e8.2_400bps_sup@v4.3.0 | 5mCG_5hmCG  
5mC_5hmC  
6mA  
| v1  
v1  
v2 | 5 kHz  
dna_r10.4.1_e8.2_400bps_fast@v4.2.0 | 5mCG_5hmCG | v2 | 5 kHz  
dna_r10.4.1_e8.2_400bps_hac@v4.2.0 | 5mCG_5hmCG | v2 | 5 kHz  
dna_r10.4.1_e8.2_400bps_sup@v4.2.0 | 5mCG_5hmCG  
5mC_5hmC  
5mC  
6mA  
| v3.1  
v1  
v2  
v3 | 5 kHz  
  
## RNA Models

Warning

The BAM/CRAM format does not support `U` bases.

Therefore, when Dorado is performing RNA basecalling, the resulting output files will include `T` instead of `U`. This is consistent across output file types.

The same applies to parsing inputs. Any input HTS file (e.g. FASTQ generated by `guppy`/`basecall_server`) with `U` bases is not handled by Dorado.

Basecalling Models | Compatible  
Modifications | Modifications  
Model  
Version | Data  
Sampling  
Frequency  
---|---|---|---  
**rna004_130bps_fast@v5.2.0** |  |  | 4 kHz  
**rna004_130bps_hac@v5.2.0** | m5C  
m6A_DRACH  
inosine_m6A  
pseU | v1  
v1  
v1  
v1 | 4 kHz  
**rna004_130bps_sup@v5.2.0** | m5C_2OmeC  
m6A_DRACH  
inosine_m6A_2OmeA  
pseU_2OmeU  
2OmeG | v1  
v1  
v1  
v1  
v1 | 4 kHz  
rna004_130bps_fast@v5.2.0 |  |  | 4 kHz  
rna004_130bps_hac@v5.2.0 | m5C  
m6A_DRACH  
inosine_m6A  
pseU | v1  
v1  
v1  
v1 | 4 kHz  
rna004_130bps_sup@v5.2.0 | m5C_2OmeC  
m6A_DRACH  
inosine_m6A_2OmeA  
pseU_2OmeU  
2OmeG | v1  
v1  
v1  
v1  
v1 | 4 kHz  
rna004_130bps_fast@v5.1.0 |  |  | 4 kHz  
rna004_130bps_hac@v5.1.0 | m5C  
m6A_DRACH  
inosine_m6A  
pseU | v1  
v1  
v1  
v1 | 4 kHz  
rna004_130bps_sup@v5.1.0 | m5C  
m6A_DRACH  
inosine_m6A  
pseU | v1  
v1  
v1  
v1 | 4 kHz  
rna004_130bps_fast@v5.0.0 |  |  | 4 kHz  
rna004_130bps_hac@v5.0.0 | m6A  
m6A_DRACH  
pseU | v1  
v1  
v1 | 4 kHz  
rna004_130bps_sup@v5.0.0 | m6A  
m6A_DRACH  
pseU | v1  
v1  
v1 | 4 kHz  
rna004_130bps_fast@v3.0.1 |  |  | 4 kHz  
rna004_130bps_hac@v3.0.1 |  |  | 4 kHz  
rna004_130bps_sup@v3.0.1 | m6A_DRACH | v1 | 4 kHz  
  
Back to top 

## 文档章节: Introduction - Dorado Documentation

# Models

Dorado basecalling relies upon machine learning models to decode the raw nanopore sequencing data. The appropriate model for your data will be automatically selected by Dorado `basecaller` using the [model selection complex](../selection/). However, you can also manually select a model using the naming conventions below.

There are a number of factors which define a basecalling model, but the key factors are broadly summarised by the balance of performance and accuracy that models provide, and the data that the model was trained to accurately decode.

## Understanding model names

The names of Dorado models are systematically structured, each segment corresponding to a different aspect of the model, which include both chemistry and run settings (defined here). Below are some examples of simplex basecalling models:
    
    
    dna_r10.4.1_e8.2_400bps_sup@v5.2.0
    rna004_130bps_hac@v5.2.0
    
    
    
    {analyte}_{pore}_{chemistry}_{speed}@version
    

### Sequencing condition

Models are trained on carefully curated datasets for specific nanopore sequencing condition and as such they are each assigned specific names to denote which condition they are paired.

The sequencing condition will typically denote the following features:

Analyte Type - `dna / rna004`
    

This denotes the type of analyte being sequenced. For DNA sequencing, this will be `dna`. If you are using a Direct RNA Sequencing Kit, this will be `rna004`.

Pore Type - `r10.4.1`
    

This section corresponds to the type of flow cell used. For instance, `FLO-MIN114 / FLO-FLG114` is indicated by `r10.4.1`.

Chemistry Type - `e8.2`
    

This represents the chemistry type, which corresponds to the kit used for sequencing. For example, Kit 14 chemistry is denoted by `e8.2`.

Translocation Speed - `130bps / 260bps / 400bps`:
    

This parameter, defines the speed of translocation.

### Speed and Accuracy

Typically for each model generation, 3 models are available and are named `fast`, `hac` (high-accuracy), and `sup` (super-accurate). These are in order of increasing basecalling accuracy where `fast` is the least accurate and `sup` is the most accurate. In general, larger models are more accurate but are more computationally expensive to evaluate.

As such, **we recommend the`hac` model for most users** as it strikes the best balance between accuracy and computational cost.

### Model Version Numbers

Tip

We recommend that users use the **latest** models for the best results.

Basecalling models are frequently updated to improve accuracy and performance. The model version is identified using the following form `v{major}.{minor}.{patch}` for example `v4.3.0`.

Simplex basecalling models are identified by only one version but modification model names contains two version numbers for example: `dna_r10.4.1_e8.2_400bps_hac@v4.3.0_6mA@v1` and follow the format: `{simplex_model@version}_{modification@version}`

This is because **all modification models are paired with a specific simplex model**. The first version identifies the simplex model while the second identifies the version of the modification model. As such, modification model version numbers are reset on each simplex model update.

For example, a `6mA@v1` modification model compatible with the `v4.3.0` simplex model is more recent than a `6mA@v2` modification model compatible with a`v4.2.0` simplex model.

Back to top 

## 文档章节: Model Selection - Dorado Documentation

# Model Selection

The Dorado `model` argument used `basecaller` and `duplex` is used to select basecalling models. There are multiple model selection methods to support most use cases and the _value_ of this field is known as the model complex.

The model complex is interpreted in one of 3 ways depending on its format:

  1. **Path**: Select a model using a directory path.
  2. **Name**: Select a model using a full [model name](../list/).
  3. **Variant**: Select models based on some properties.

The **Name** and **Variant** methods will automatically download models using the model discovery rules.

## Model selection via Path

Existing models can be selected using their directory path.

Use `dorado download` to download models into a directory and then specify the model using the model directory path. For example:
    
    
    # Download a model into a --models-directory
    dorado download --model dna_r10.4.1_e8.2_400bps_hac@v5.2.0 --models-directory ~/models/
    
    # Use the downloaded model
    dorado basecaller ~/models/dna_r10.4.1_e8.2_400bps_hac@v5.2.0 reads/ ... > calls.bam
    

## Model selection via Name

Dorado supports selecting basecaller models by their full name. If the model name is in the [list of available models](../list/) it will be found using the model discovery rules.
    
    
    dorado basecaller dna_r10.4.1_e8.2_400bps_hac@v5.2.0 reads/ ... > calls.bam
    

## Model selection via Variant

Using a variant model complex instructs Dorado to select a basecalling models based on the type of **data** to be basecalled. The example below will download the latest `hac` model for the type of data in `reads/` which could be either DNA or RNA.
    
    
    dorado basecaller hac reads/ ... > calls.bam
    

### Model variant syntax

A model variant must start with the **simplex model speed** and follows this syntax:
    
    
    speed[version][,mod[version]]*
    

  * `[]` \- Enclose an **optional** field.
  * `*` \- The field may be repeated **zero or more times**.
  * `,` \- All items must be **comma-separated**.

#### _speed_

The model speed can be any of `fast`, `hac` or `sup`.

#### _version_

The `version` takes the form of `@vX.Y.Z` **or** `@latest`.

If `@latest` is used, the latest available model version is used. This is the default i.e. `hac -> hac@latest`.

`X`, `Y` and `Z` are major, minor, and patch version numbers (e.g. `@v1.2.3`).

Missing trailing values are assumed to be zero e.g. `@v1.2 -> @v1.2.0`.

Missing _internal_ values `@v0..1` and trailing periods `@v1.` are not permitted.

#### _mod_

Multiple Modification Models

More than one modification model may be selected at once and each must be separated by a comma.

For example: `sup,6mA,5mC@latest`

The `mod` field can be any modification name which is available for the simplex model and can be optionally followed by a `version`.

Examples: `6mA`, `m6A`, `pseU`, `5mC@v2` and `5mCG_5hmCG@v1.0.0`.

Automatically selected **modification** models will always match the base simplex model version and will be the latest compatible version unless a specific version is set by the user.

Multiple modification models must use different canonical bases

When selecting multiple modification models, only one modification model per canonical base may be active at once.

For example, `sup,4mC_5mC,5mC_5hmC` is invalid as **both** modification models operate on the `C` canonical base context.

See the [Model List](../list/) for a list of all available models.

#### Examples of model variants

Model Complex | Description  
---|---  
`fast` | Latest compatible **fast** model  
`hac` | Latest compatible **hac** model  
`sup` | Latest compatible **sup** model  
`hac@latest` | Latest compatible **hac** simplex basecalling model  
`hac@v4.2.0` | Simplex basecalling **hac** model with version `v4.2.0`  
`hac@v3.5` | Simplex basecalling **hac** model with version `v3.5.0`  
`hac,5mCG_5hmCG` | Latest compatible **hac** simplex model and latest **5mCG_5hmCG** modified bases model matching the chosen simplex model  
`hac,5mCG_5hmCG@v3` | Latest compatible **hac** simplex model and compatible **5mCG_5hmCG** modified bases model with version `v3.0.0`  
`sup@v5.2,5mCG_5hmCG,6mA` | Simplex basecalling **sup** model with version `v5.2.0` and latest compatible **5mCG_5hmCG** and **6mA** modification models  
  
Here are some examples of model complexes in use:
    
    
    # Simplex basecalling
    dorado basecaller hac                   reads/ > calls.bam # HAC simplex basecalling
    dorado basecaller hac@v4.1.0            reads/ > calls.bam # HAC simplex with specific version
    
    # Simplex modification basecalling
    dorado basecaller sup,6mA               reads/ > calls.bam # SUP with modifications
    dorado basecaller sup,6mA,5mCG_5hmCG    reads/ > calls.bam # Multiple modification models
    dorado basecaller sup@v4.2.0,6mA@v1     reads/ > calls.bam # Setting versions
    
    # Duplex basecalling
    dorado duplex  sup@v4.1.0  reads/ > calls.bam # SUP duplex basecalling with specific version
    dorado duplex  sup,5mC     reads/ > calls.bam # SUP duplex basecalling with modification model
    

## Selecting modified base models

### Via model Variant

Recommended

Please refer to the model variant section which contains [examples](./#examples-of-model-complexes) of both simplex and modified base model selection using a model variant.

This is the recommended method of selecting both simplex and modified bases models.

The `--modified-bases` and `--modified-bases-models` arguments are not permitted when using the model variant syntax.

### Via modified bases model Name

As an extension to the model selection via Name, a single modified base model can be selected using its name as shown below. If the required simplex model is not found it will also be found using the model discovery rules.
    
    
    dorado basecaller dna_r10.4.1_e8.2_400bps_hac@v5.2.0_5mC_5hmC@v1 reads/ ... > calls.bam
    

The `--modified-bases` and `--modified-bases-models` arguments can be used to select additional modified bases models.

### Via `--modified-bases` CLI argument

Space Separated

Multiple modified base model **codes** must be **space separated**.

Similarly to how the model complex functions, the `--modified-bases` argument takes a **space separated** list of modification codes and automatically resolves which modified base model to use based on your **simplex** basecalling model selection. The modified base model selected will always be the **latest** available as there is no way to specify a version (unlike when using model complex).

Examples:
    
    
    dorado basecaller hac         reads/  --modified-bases pseU      > calls.bam
    dorado basecaller hac         reads/  --modified-bases 6mA 5mC   > calls.bam
    dorado duplex /simplex/model/ reads/  --modified-bases 5mC       > calls.bam
    

### Via `--modified-bases-models` CLI argument

Comma separated

Multiple modified base model **paths** must be **comma separated**.

Similarly to how simplex basecall models can be specified using a model name, or a path, modified base models can be specified via a modified bases model name or path using the `--modified-bases-models` argument.

See also documentation for the [model downloader](../downloader/).

The example below selects a modified bases model by name.
    
    
    # Run the basecaller with --modified-bases-models using a modified bases model name.
    # Models are downloaded automatically
    dorado basecaller rna004_130bps_hac@v5.2.0/ reads/ \
        --modified-bases-models rna004_130bps_hac@v5.2.0_m6A@v1,rna004_130bps_hac@v5.2.0_pseU@v1 \
        > calls.bam
    

The example below selects a modified bases model by path.
    
    
    # Download the models into a models directory
    dorado download --model rna004_130bps_hac@v5.2.0          --models-directory ~/models
    dorado download --model rna004_130bps_hac@v5.2.0_m6A@v1   --models-directory ~/models
    dorado download --model rna004_130bps_hac@v5.2.0_pseU@v1  --models-directory ~/models
    
    # Run the basecaller with modified-bases using a modified bases model path
    dorado basecaller ~/models/rna004_130bps_hac@v5.2.0/ reads/ \
        --modified-bases-models ~/models/rna004_130bps_hac@v5.2.0_m6A@v1,~/models/rna004_130bps_hac@v5.2.0_pseU@v1 \
        > calls.bam
    

## Model discovery

When not using paths to select models Dorado will search for models in the following locations listed in priority order:

  1. The `--models-directory` path set via CLI argument.
  2. The `DORADO_MODELS_DIRECTORY` path set via environment variable.
  3. The current working directory.

### Automatic model download

If `--models-directory` or `DORADO_MODELS_DIRECTORY` environment variable is set, models will be downloaded into the nominated directory. Otherwise models will be downloaded into the current working directory and deleted after Dorado has finished.

To avoid repeatedly downloading models it is recommended that the `--models-directory` argument or `DORADO_MODELS_DIRECTORY` environment variable is set.

The example below shows that without using `--models-directory` automatic model selection will download and clean up models on every use of Dorado.
    
    
    # Model is downloaded into temporary directory and cleaned when Dorado is finished
    dorado basecaller hac pod5s/ > calls.bam
    
    ls *hac*
    # No results
    
    # Model is re-downloaded and cleaned up again
    dorado basecaller hac pod5s/ > calls.bam
    

The example below shows that when using `--models-directory`, automatic model selection will download models that are missing and reuse previously existing models.
    
    
    # Model is downloaded into models/
    dorado basecaller hac pod5s/ --models-directory models/ > calls.bam
    
    ls models/
        dna_r10.4.1_e8.2_400bps_hac@v5.2.0
    
    # Model is re-used
    dorado basecaller hac pod5s/ --models-directory models/ > calls.bam
    

Models can be re-used as shown above but by using the `DORADO_MODELS_DIRECTORY` environment variable. This can be set once in a user configuration file and re-used without needing to set the `--models-directory` argument on the command line.
    
    
    export DORADO_MODELS_DIRECTORY="/path/to/models/"
    

The environment variable can also be set inline with dorado but this is just shown for completeness.
    
    
    DORADO_MODELS_DIRECTORY=/path/to/models/ dorado basecaller hac pod5s/ > calls.bam
    

Back to top 

## 文档章节: FAQ - Dorado Documentation

# Frequently Asked Questions

Below are some of our most frequently asked technical and support questions. Please check back regularly if you have an issue as this will be updated often.

If you have a question that is not answered below please raise a new issue on the [Dorado GitHub issues](https://github.com/nanoporetech/dorado/issues) page providing as much information as possible and the Dorado team will aim to respond promptly.

## Basecaller

### Models

Please check out the [Models Introduction](../../models/models/) and [Models List](../../models/list/).

#### Which model should I use?

Since Dorado 0.5.0, the [automatic model selection](../../models/selection/) algorithm should be able to select the appropriate model for the input data (POD5 only) given a model speed (e.g. `fast, hac, sup`). Dorado will automatically download missing models.

In general, the **latest** basecalling models will be the most performant and most accurate as there are continuous advances in model architecture and training.

#### Which model did I use?

Dorado will write meta data to the BAM read group (`RG`) header as detailed in the [SAM specification](../../basecaller/sam_spec/#read-group-header).

The following command can be used to inspect the header and extract the basecall model or modified bases model.
    
    
    > samtools view -H calls.bam | grep -oE "\S*models?=\S*"
    DS:basecall_model=dna_r10.4.1_e8.2_400bps_hac@v5.2.0
    modbase_models=dna_r10.4.1_e8.2_400bps_hac@v5.2.0_5mC_5hmC@v1
    

#### How do I basecall data from legacy sequencing conditions?

Dorado supports basecalling for the DNA R10.4.1 and RNA004 conditions, but doesn't support basecalling for the legacy RNA002, R9.4.1, R10.3, and R10.4 conditions.

The DNA R9.4.1 and RNA002 conditions were deprecated as of Dorado v1.0.0.

[Dorado v0.9.6](https://github.com/nanoporetech/dorado/releases/tag/v0.9.6) was the last release which supported DNA R9.4.1 and RNA002 conditions.

For R10.4 and R10.3, please use the legacy Guppy basecaller, which is available from the Nanopore Community [Downloads page](https://community.nanoporetech.com/downloads).

* * *

#### Where are the new models?

New Dorado releases incrementally support new models which are generally not backwards compatible with previous versions. If you can see a model in the [Models List](../../models/list/) but you cannot download it please ensure you have the **latest release of Dorado** which you can find instruction on how to download and install it [here](../../#installation)

* * *

### Outputs

#### Why do I have more records than reads?

Dorado reports the number of reads _basecalled_ from your input data, but this number may differ from the number of records in your output because of read splitting. This can happen because a single read recorded to the POD5 file contains more than one molecule and this was not detected and split into separate records during sequencing by MinKNOW.

Dorado annotates split reads by adding the `parent_read_id` which is stored in the bam `pi` tag. The `parent_read_id` is the read id of the original unsplit read. Only reads which are children of unsplit reads have this `pi` tag.

We can count all bam records which are split reads using this command:
    
    
    samtools view <BAM> --expr '[pi] && [dx]!=1' | wc -l
    

Note

Unsplit reads may contain an arbitrary number of reads not just 2 as shown in this example.

Here, we also include `[dx]!=1` for completeness in case the data was duplex basecalled. For more information on the `dx` tag please see the [duplex documentation](../../basecaller/duplex/#duplex-sequence-metadata).

If your output had 1 additional record, the above command would report 2 as an unsplit read will be written as 2 new records with unique `read_id`s and sharing the same `parent_read_id`.

* * *

Back to top 

## 文档章节: Troubleshooting - Dorado Documentation

# Troubleshooting

This page contains Dorado troubleshooting advice to help users resolve issues which are known to appear from time to time.

If you have an issue that cannot be resolved following the advice below please raise a new issue on the [Dorado GitHub issues](https://github.com/nanoporetech/dorado/issues) page providing as much information as possible and the Dorado team will aim to respond promptly.

You can also seek advice from the [Nanopore Community](https://community.nanoporetech.com/docs?from=support).

## Errors and warnings

Dorado will issue warnings and errors to `stderr` during runtime and may terminate if an unrecoverable error occurs. Many errors stem from incorrect configuration of the command line and the following are examples of common [issues](https://github.com/nanoporetech/dorado/issues) reported on GitHub.

### No supported chemistry found
    
    
    [error] No supported chemistry found for flowcell_code: '__UNKNOWN_FLOWCELL__' sequencing_kit: '__UNKNOWN_KIT__' sample_rate: 5000
    [error] This is typically seen when using prototype kits. Please download an appropriate model for your data and select it by model path
    

When using automatic [model selection complex](../../models/selection/) dorado must be able to determine which model to use by inspecting the input data which must be in POD5 format.

If your data doesn't contain a recognised flow cell (e.g. `__UNKNOWN_FLOWCELL__`) or sequencing_kit (e.g. `__UNKNOWN_KIT__`) dorado cannot find a suitable model for your data.

To basecall your data you need to first [download](../../models/downloader/) a basecalling model which is appropriate for your data and specify the model using its **filepath** as shown in the [simplex basecalling quick-start](../../basecaller/simplex/) or in the example below:
    
    
    dorado download --model dna_r10.4.1_e8.2_400bps_fast@v5.2.0
    dorado basecaller dna_r10.4.1_e8.2_400bps_fast@v5.2.0 reads/ > calls.bam
    

For details please check out the [models introduction](../../models/models/) and the [models list](../../models/list/).

### Incompatible modbase models
    
    
    [error] Following are incompatible modbase models.
        Please select only one of them to run: model_A and model_B have overlapping canonical motif: A
    

This error is shown when the user selects two modbase models which share a canonical base which is invalid as detailed [here](../../basecaller/mods/#modification-context).

Common causes of this error are selecting these pairs of modbase models:

  * `5mC_5hmC` \+ `5hmCG_5hmCG`
  * `5mC_5hmC` \+ `4mC_5mC`
  * `m6A_DRACH` \+ `inosine_m6A`

## Runtime issues

### CUDA Out Of Memory

Dorado supports multiple model architectures which can vary significantly in size (`fast, hac, sup`). Multiple models are also used together when using features such as modification basecalling, stereo duplex basecalling and hemi-methylation duplex basecalling. As such there are cases where excessive GPU memory consumption can unexpectedly terminate Dorado.

Unless specified otherwise by the user Dorado will attempt to calculate the optimal batch size using the auto batch size protocol. This algorithm tests multiple batch sizes for the models in use and selects the batch size which gives the best performance. However, many factors could result in this algorithm selecting a batch size which may exceed the available GPU memory especially when combined with modification / stereo duplex models.

These factors include but are not limited to:

  * Other processes using GPU resources (including other instances of Dorado)
  * Display devices
  * GPU with insufficient memory (Dorado does not support GPUs with <8GB of memory)

To resolve CUDA out-of-memory issues inspect the Dorado output from a previous run which should report the batch size used as shown in the example below:
    
    
    dorado basecaller <model> <reads> ... > calls.bam
    [info] > Creating basecall pipeline
    [info]  - set batch size to 480
    

This example shows a batch size of `480`. We can use this as a guide for specifying the batch size manually using the `--batchsize` argument in `basecaller` and `duplex`. Reduce the batchsize by a even values such as `32, 48, 64` starting with approximately 10% of the original auto batchsize estimate `480-48=432` giving:
    
    
    dorado basecaller <model> <reads> --batchsize 432 ... > calls.bam
    

Repeat the above until Dorado completes successfully without running out of GPU memory.

### Low GPU utilization

Low GPU utilization can lead to reduced basecalling speed. This problem can be identified using tools such as `nvidia-smi` and `nvtop`. Low GPU utilization often stems from I/O bottlenecks in basecalling.

Here are a few steps you can take to improve the situation:

  1. Use POD5 instead of .fast5:
     * POD5 has superior I/O performance and will enhance the basecall speed in I/O constrained environments.
  2. Transfer data to the local disk before basecalling:
     * Frequently network disks cannot supply Dorado with adequate I/O speeds. To mitigate this, make sure your data is as close to your host machine as possible.
  3. Choose SSD over HDD:
     * Particularly for duplex basecalling, using a local SSD can offer significant speed advantages. This is due to the duplex basecalling algorithm's reliance on heavy random access of data.

### Library path errors

Dorado comes equipped with the necessary libraries (such as CUDA) for its execution. However, on some operating systems, the system libraries might be chosen over Dorado's. This discrepancy can result in various errors, for instance, `CuBLAS error 8`.

To resolve this issue, you need to set the `LD_LIBRARY_PATH` to point to Dorado's libraries. Use a command like the following to change path as appropriate:

LinuxMacOS
    
    
    $ export LD_LIBRARY_PATH=<PATH_TO_DORADO>/dorado-1.4.0-linux-x64/lib:$LD_LIBRARY_PATH
    
    
    
    $ export DYLD_LIBRARY_PATH=<PATH_TO_DORADO>/dorado-1.4.0-osx-arm64/lib:$DYLD_LIBRARY_PATH
    

### Windows GPU performance

On Windows systems with Nvidia GPUs, open Nvidia Control Panel, navigate into âManage 3D settingsâ and then set âCUDA - Sysmem Fallback Policyâ to âPrefer No Sysmem Fallbackâ. This will provide a significant performance improvement.

### Windows PowerShell encoding

When running in PowerShell on Windows, care must be taken, as the default encoding for application output is typically `UTF-16LE`. This will cause file corruption if standard output is redirected to a file.

It is recommended to use the `--output-dir` argument to emit BAM files if PowerShell must be used.

For example, the following command will create corrupt output which cannot be read by samtools:
    
    
    PS > dorado basecaller <args> > out.bam
    

Instead, use:
    
    
    PS > dorado basecaller <args> --output-dir .
    

Warning

Using `out-file` with `Ascii` encoding will not produce well-formed **BAM** (binary) files.

For text-based output formats (SAM or FASTQ), it is possible to override the encoding on output using the out-file command.

This command will produce a well formed ascii **SAM** file:
    
    
    PS > dorado basecaller <args> --emit-sam | out-file -encoding Ascii out.sam
    

Read more about PowerShell output encoding [here](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_character_encoding?view=powershell-7.4).

Back to top 

# Dorado Documentation

## subcommand
```bash
Usage: dorado [options] subcommand

Positional arguments:
aligner
basecaller
correct
demux
download
duplex
polish
summary
trim

Optional arguments:
-h --help               shows help message and exits
-v --version            prints version information and exits
-vv                     prints verbose version information and exits
```

### dorado aligner
```bash
Usage: dorado aligner [--help] [--recursive] [--output-dir VAR] [--emit-summary] [--bed-file VAR] [--threads VAR] [--max-reads VAR] [--verbose]... [--mm2-opts VAR] index reads

Alignment using minimap2. The outputs are expected to be equivalent to minimap2.
The default parameters use the lr:hq preset.
NOTE: Not all arguments from minimap2 are currently available. Additionally, parameter names are not finalized and may change.

Positional arguments:
  index             reference in (fastq/fasta/mmi). 
  reads             An input file or the folder containing input file(s) (any HTS format). [nargs=0..1] [default: ""]

Optional arguments:
  -h, --help        shows help message and exits 
  -r, --recursive   If the 'reads' positional argument is a folder any subfolders will also be searched for input files. 
  -o, --output-dir  If specified output files will be written to the given folder, otherwise output is to stdout. Required if the 'reads' positional argument is a folder. [nargs=0..1] [default: ""]
  --emit-summary    If specified, a summary file containing the details of the primary alignments for each read will be emitted to the root of the output folder. This option requires that the '--output-dir' option is also set. 
  --bed-file        Optional bed-file. If specified, overlaps between the alignments and bed-file entries will be counted, and recorded in BAM output using the 'bh' read tag. [nargs=0..1] [default: ""]
  -t, --threads     number of threads for alignment and BAM writing (0=unlimited). [nargs=0..1] [default: 0]
  -n, --max-reads   maximum number of reads to process (for debugging, 0=unlimited). [nargs=0..1] [default: 0]
  -v, --verbose     [may be repeated]
  --mm2-opts        Optional minimap2 options string. For multiple arguments surround with double quotes. 
```

### dorado basecaller
```bash
Usage: dorado [--help] [--verbose]... [--device VAR] [--models-directory VAR] [--bed-file VAR] [--recursive] [--read-ids VAR] [--max-reads VAR] [--resume-from VAR] [--min-qscore VAR] [--emit-moves] [--emit-fastq] [--emit-sam] [--output-dir VAR] [--reference VAR] [--mm2-opts VAR] [--modified-bases VAR...] [--modified-bases-models VAR] [--modified-bases-threshold VAR] [--modified-bases-batchsize VAR] [--kit-name VAR] [--sample-sheet VAR] [--barcode-both-ends] [--barcode-arrangement VAR] [--barcode-sequences VAR] [--primer-sequences VAR] [--no-trim] [--trim VAR] [--estimate-poly-a] [--poly-a-config VAR] [--batchsize VAR] [--chunksize VAR] [--overlap VAR] model data

Positional arguments:
  model                       Model selection {fast,hac,sup}@v{version} for automatic model selection including modbases, or path to existing model directory. 
  data                        The data directory or file (POD5/FAST5 format). 

Optional arguments:
  -h, --help                  shows help message and exits 
  -v, --verbose               [may be repeated]
  -x, --device                Specify CPU or GPU device: 'auto', 'cpu', 'cuda:all' or 'cuda:<device_id>[,<device_id>...]'. Specifying 'auto' will choose either 'cpu', 'metal' or 'cuda:all' depending on the presence of a GPU device. [nargs=0..1] [default: "auto"]
  --models-directory          Optional directory to search for existing models or download new models into. [nargs=0..1] [default: "."]
  --bed-file                  Optional bed-file. If specified, overlaps between the alignments and bed-file entries will be counted, and recorded in BAM output using the 'bh' read tag. [nargs=0..1] [default: ""]

Input data arguments (detailed usage):
  -r, --recursive             Recursively scan through directories to load FAST5 and POD5 files. 
  -l, --read-ids              A file with a newline-delimited list of reads to basecall. If not provided, all reads will be basecalled. [nargs=0..1] [default: ""]
  -n, --max-reads             Limit the number of reads to be basecalled. [nargs=0..1] [default: 0]
  --resume-from               Resume basecalling from the given HTS file. Fully written read records are not processed again. [nargs=0..1] [default: ""]

Output arguments (detailed usage):
  --min-qscore                Discard reads with mean Q-score below this threshold. [nargs=0..1] [default: 0]
  --emit-moves                Write the move table to the 'mv' tag. 
  --emit-fastq                Output in fastq format. 
  --emit-sam                  Output in SAM format. 
  -o, --output-dir            Optional output folder, if specified output will be written to a calls file (calls_<timestamp>.sam|.bam|.fastq) in the given folder. 

Alignment arguments (detailed usage):
  --reference                 Path to reference for alignment. [nargs=0..1] [default: ""]
  --mm2-opts                  Optional minimap2 options string. For multiple arguments surround with double quotes. 

Modified model arguments (detailed usage):
  --modified-bases            A space separated list of modified base codes. Choose from: pseU, 4mC_5mC, inosine_m6A, 5mCG, 5mCG_5hmCG, 5mC_5hmC, 5mC, m5C, 6mA, m6A, m6A_DRACH. [nargs: 1 or more] 
  --modified-bases-models     A comma separated list of modified base model paths. [nargs=0..1] [default: ""]
  --modified-bases-threshold  The minimum predicted methylation probability for a modified base to be emitted in an all-context model, [0, 1]. 
  --modified-bases-batchsize  The modified base models batch size. 

Barcoding arguments (detailed usage):
  --kit-name                  Enable barcoding with the provided kit name. Choose from: EXP-NBD103 EXP-NBD104 EXP-NBD114 EXP-NBD114-24 EXP-NBD196 EXP-PBC001 EXP-PBC096 SQK-16S024 SQK-16S114-24 SQK-LWB001 SQK-MAB114-24 SQK-MLK111-96-XL SQK-MLK114-96-XL SQK-NBD111-24 SQK-NBD111-96 SQK-NBD114-24 SQK-NBD114-96 SQK-PBK004 SQK-PCB109 SQK-PCB110 SQK-PCB111-24 SQK-PCB114-24 SQK-RAB201 SQK-RAB204 SQK-RBK001 SQK-RBK004 SQK-RBK110-96 SQK-RBK111-24 SQK-RBK111-96 SQK-RBK114-24 SQK-RBK114-96 SQK-RLB001 SQK-RPB004 SQK-RPB114-24 TWIST-16-UDI TWIST-96A-UDI VSK-PTC001 VSK-VMK001 VSK-VMK004 VSK-VPS001. [nargs=0..1] [default: ""]
  --sample-sheet              Path to the sample sheet to use. [nargs=0..1] [default: ""]
  --barcode-both-ends         Require both ends of a read to be barcoded for a double ended barcode. 
  --barcode-arrangement       Path to file with custom barcode arrangement. Requires --kit-name. 
  --barcode-sequences         Path to file with custom barcode sequences. Requires --kit-name and --barcode-arrangement. 
  --primer-sequences          Path to file with custom primer sequences. 

Trimming arguments (detailed usage):
  --no-trim                   Skip trimming of barcodes, adapters, and primers. If option is not chosen, trimming of all three is enabled. 
  --trim                      Specify what to trim. Options are 'none', 'all', and 'adapters'. The default behaviour is to trim all detected adapters, primers, and barcodes. Choose 'adapters' to just trim adapters. The 'none' choice is equivelent to using --no-trim. Note that this only applies to DNA. RNA adapters are always trimmed. [nargs=0..1] [default: ""]

Poly(A) arguments (detailed usage):
  --estimate-poly-a           Estimate poly(A)/poly(T) tail lengths (beta feature). Primarily meant for cDNA and dRNA use cases. 
  --poly-a-config             Configuration file for poly(A) estimation to change default behaviours [nargs=0..1] [default: ""]

Advanced arguments (detailed usage):
  -b, --batchsize             The number of chunks in a batch. If 0 an optimal batchsize will be selected. [nargs=0..1] [default: 0]
  -c, --chunksize             The number of samples in a chunk. [nargs=0..1] [default: 10000]
  --overlap                   The number of samples overlapping neighbouring chunks. [nargs=0..1] [default: 500]
```

### dorado download
```bash
Usage: dorado [--help] [--model VAR] [--models-directory VAR] [--list] [--list-yaml] [--list-structured] [--data VAR] [--recursive] [--overwrite] [--verbose]...

Optional arguments:
  -h, --help          shows help message and exits 
  --model             the model to download [nargs=0..1] [default: "all"]
  --models-directory  the directory to download the models into [nargs=0..1] [default: "."]
  --list              list the available models for download 
  --list-yaml         list the available models for download, as yaml, to stdout 
  --list-structured   list the available models in a structured format, as yaml, to stdout 
  --data              path to POD5 data used to automatically select models [nargs=0..1] [default: ""]
  -r, --recursive     recursively scan through directories to load POD5 files 
  --overwrite         overwrite existing models if they already exist 
  -v, --verbose       [may be repeated]
```




