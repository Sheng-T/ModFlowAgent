# Samtools Document

# 工具文档: samtools(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools – Utilities for the Sequence Alignment/Map (SAM) format 

## SYNOPSIS

samtools [addreplacerg](samtools-addreplacerg.html) -r 'ID:fish' -r 'LB:1334' -r 'SM:alpha' -o output.bam input.bam 

samtools [ampliconclip](samtools-ampliconclip.html) -b bed.file input.bam 

samtools [ampliconstats](samtools-ampliconstats.html) primers.bed in.bam 

samtools [bedcov](samtools-bedcov.html) aln.sorted.bam 

samtools [calmd](samtools-calmd.html) in.sorted.bam ref.fasta 

samtools [cat](samtools-cat.html) out.bam in1.bam in2.bam in3.bam 

samtools [checksum](samtools-checksum.html) in.bam 

samtools [collate](samtools-collate.html) -o aln.name_collated.bam aln.sorted.bam 

samtools [consensus](samtools-consensus.html) -o out.fasta in.bam 

samtools [coverage](samtools-coverage.html) aln.sorted.bam 

samtools [cram-size](samtools-cram-size.html) -v -o out.size in.cram 

samtools [depad](samtools-depad.html) input.bam 

samtools [depth](samtools-depth.html) aln.sorted.bam 

samtools [dict](samtools-dict.html) -a GRCh38 -s "Homo sapiens" ref.fasta 

samtools [faidx](samtools-faidx.html) ref.fasta 

samtools [fasta](samtools-fasta.html) input.bam > output.fasta 

samtools [fastq](samtools-fastq.html) input.bam > output.fastq 

samtools [fixmate](samtools-fixmate.html) in.namesorted.sam out.bam 

samtools [flags](samtools-flags.html) PAIRED,UNMAP,MUNMAP 

samtools [flagstat](samtools-flagstat.html) aln.sorted.bam 

samtools [fqidx](samtools-fqidx.html) ref.fastq 

samtools [head](samtools-head.html) in.bam 

samtools [idxstats](samtools-idxstats.html) aln.sorted.bam 

samtools [import](samtools-import.html) input.fastq > output.bam 

samtools [index](samtools-index.html) aln.sorted.bam 

samtools [markdup](samtools-markdup.html) in.algnsorted.bam out.bam 

samtools [merge](samtools-merge.html) out.bam in1.bam in2.bam in3.bam 

samtools [mpileup](samtools-mpileup.html) -f ref.fasta -r chr3:1,000-2,000 in1.bam in2.bam 

samtools [phase](samtools-phase.html) input.bam 

samtools [quickcheck](samtools-quickcheck.html) in1.bam in2.cram 

samtools [reference](samtools-reference.html) -o ref.fa in.cram 

samtools [reheader](samtools-reheader.html) in.header.sam in.bam > out.bam 

samtools [reset](samtools-reset.html) -o /tmp/reset.bam processed.bam 

samtools [samples](samtools-samples.html) input.bam 

samtools [sort](samtools-sort.html) -T /tmp/aln.sorted -o aln.sorted.bam aln.bam 

samtools [split](samtools-split.html) merged.bam 

samtools [stats](samtools-stats.html) aln.sorted.bam 

samtools [targetcut](samtools-targetcut.html) input.bam 

samtools [tview](samtools-tview.html) aln.sorted.bam ref.fasta 

samtools [view](samtools-view.html) -bt ref_list.txt -o aln.bam aln.sam.gz 

## DESCRIPTION

Samtools is a set of utilities that manipulate alignments in the SAM (Sequence Alignment/Map), BAM, and CRAM formats. It converts between the formats, does sorting, merging and indexing, and can retrieve reads in any regions swiftly. 

Samtools is designed to work on a stream. It regards an input file `-' as the standard input (stdin) and an output file `-' as the standard output (stdout). Several commands can thus be combined with Unix pipes. Samtools always output warning and error messages to the standard error output (stderr). 

Samtools is also able to open files on remote FTP or HTTP(S) servers if the file name starts with `ftp://', `http://', etc. Samtools checks the current working directory for the index file and will download the index upon absence. Samtools does not retrieve the entire alignment file unless it is asked to do so. 

If an index is needed, samtools looks for the index suffix appended to the filename, and if that isn't found it tries again without the filename suffix (for example **in.bam.bai** followed by **in.bai**). However if an index is in a completely different location or has a different name, both the main data filename and index filename can be pasted together with **##idx##**. For example **/data/in.bam##idx##/indices/in.bam.bai** may be used to explicitly indicate where the data and index files reside. 

## COMMANDS

Each command has its own man page which can be viewed using e.g. **man samtools-view** or with a recent GNU man using **man samtools view**. Below we have a brief summary of syntax and sub-command description. 

Options common to all sub-commands are documented below in the GLOBAL COMMAND OPTIONS section. 

**view**
    

samtools view [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

With no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header by default). 

You may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file. 

Options exist to change the output format from SAM to BAM or CRAM, so this command also acts as a file format conversion utility. 

**tview**
    

samtools tview [**-p** _chr:pos_] [**-s** _STR_] [**-d** _display_] <in.sorted.bam> [ref.fasta] 

Text alignment viewer (based on the ncurses library). In the viewer, press `?' for help and press `g' to check the alignment start from a region in the format like `chr10:10,000,000' or `=10,000,000' when viewing the same reference sequence. 

**quickcheck**
    

samtools quickcheck [_options_] _in.sam_ |_in.bam_ |_in.cram_ [ ... ] 

Quickly check that input files appear to be intact. Checks that beginning of the file contains a valid header (all formats) containing at least one target sequence and then seeks to the end of the file and checks that an end-of-file (EOF) is present and intact (BAM only). 

Data in the middle of the file is not read since that would be much more time consuming, so please note that this command will not detect internal corruption, but is useful for testing that files are not truncated before performing more intensive tasks on them. 

This command will exit with a non-zero exit code if any input files don't have a valid header or are missing an EOF block. Otherwise it will exit successfully (with a zero exit code). 

**checksum**
    

samtools checksum [_options_] _in.sam_ |_in.bam_ |_in.cram_

samtools checksum produces a CRC32 based checksum of data contained within a BAM file. This can either be order and orientation agnostic for purposes of validating all the sequencing data has passed through the entire pipeline from FASTQ through alignment and sorting, or full alignment information and order aware for the purposes of validating format conversions and while file data processing. 

**head**
    

samtools head [_options_] _in.sam_ |_in.bam_ |_in.cram_

Prints the input file's headers and optionally also its first few alignment records. This command always displays the headers as they are in the file, never adding an extra @PG header itself. 

**index**
    

samtools index [**-bc**] [**-m** _INT_] _aln.sam.gz_ |_aln.bam_ |_aln.cram_ [_out.index_] 

Index a coordinate-sorted SAM, BAM or CRAM file for fast random access. Note for SAM this only works if the file has been BGZF compressed first. (Starting from Samtools 1.16, this command can also be given several alignment filenames, which are indexed individually.) 

This index is needed when _region_ arguments are used to limit **samtools view** and similar commands to particular regions of interest. 

If an output filename is given, the index file will be written to _out.index_. Otherwise, for a CRAM file _aln.cram_ , index file _aln.cram_**.crai** will be created; for a BAM or SAM file _aln.bam_ , either _aln.bam_**.bai** or _aln.bam_**.csi** will be created, depending on the index format selected. 

**sort**
    

samtools sort [**-l** _level_] [**-m** _maxMem_] [**-o** _out.bam_] [**-O** _format_] [**-n**] [**-t** _tag_] [**-T** _tmpprefix_] [**-@** _threads_] [_in.sam_ |_in.bam_ |_in.cram_] 

Sort alignments by leftmost coordinates, or by read name when **-n** is used. An appropriate **@HD-SO** sort order header tag will be added or an existing one updated if necessary. 

The sorted output is written to standard output by default, or to the specified file (_out.bam_) when **-o** is used. This command will also create temporary files _tmpprefix_**.**_%d_**.bam** as needed when the entire alignment data cannot fit into memory (as controlled via the **-m** option). 

Consider using **samtools collate** instead if you need name collated data without a full lexicographical sort. 

Note that if the sorted output file is to be indexed with **samtools index** , the default coordinate sort must be used. Thus the **-n** and **-t** options are incompatible with **samtools index**. 

**collate**
    

samtools collate [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_< prefix>_] 

Shuffles and groups reads together by their names. A faster alternative to a full query name sort, **collate** ensures that reads of the same name are grouped together in contiguous groups, but doesn't make any guarantees about the order of read names between groups. 

The output from this command should be suitable for any operation that requires all reads from the same template to be grouped together. 

**cram-size**
    

samtools cram-size [_options_] _in.cram_

Produces a summary of CRAM block Content ID numbers and their associated Data Series stored within them. Optionally a more detailed breakdown of how each data series is encoded per container may also be listed using the **-e** or **\--encodings** option. 

**idxstats**
    

samtools idxstats _in.sam_ |_in.bam_ |_in.cram_

Retrieve and print stats in the index file corresponding to the input file. Before calling idxstats, the input BAM file should be indexed by samtools index. 

If run on a SAM or CRAM file or an unindexed BAM file, this command will still produce the same summary statistics, but does so by reading through the entire file. This is far slower than using the BAM indices. 

The output is TAB-delimited with each line consisting of reference sequence name, sequence length, # mapped reads and # unmapped reads. It is written to stdout. 

**flagstat**
    

samtools flagstat _in.sam_ |_in.bam_ |_in.cram_

Does a full pass through the input file to calculate and print statistics to stdout. 

Provides counts for each of 13 categories based primarily on bit flags in the FLAG field. Each category in the output is broken down into QC pass and QC fail, which is presented as "#PASS + #FAIL" followed by a description of the category. 

**flags**
    

samtools flags _INT_ |_STR_[,...] 

Convert between textual and numeric flag representation. 

**FLAGS:** **0x1**|  PAIRED| paired-end (or multiple-segment) sequencing technology  
---|---|---  
**0x2**|  PROPER_PAIR| each segment properly aligned according to the aligner  
**0x4**|  UNMAP| segment unmapped  
**0x8**|  MUNMAP| next segment in the template unmapped  
**0x10**|  REVERSE| SEQ is reverse complemented  
**0x20**|  MREVERSE| SEQ of the next segment in the template is reverse complemented  
**0x40**|  READ1| the first segment in the template  
**0x80**|  READ2| the last segment in the template  
**0x100**|  SECONDARY| secondary alignment  
**0x200**|  QCFAIL| not passing quality controls  
**0x400**|  DUP| PCR or optical duplicate  
**0x800**|  SUPPLEMENTARY| supplementary alignment  
  
**stats**
    

samtools stats [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

samtools stats collects statistics from BAM files and outputs in a text format. The output can be visualized graphically using plot-bamstats. 

**bedcov**
    

samtools bedcov [_options_] _region.bed_ _in1.sam_ |_in1.bam_ |_in1.cram_[...] 

Reports the total read base count (i.e. the sum of per base read depths) for each genomic region specified in the supplied BED file. The regions are output as they appear in the BED file and are 0-based. Counts for each alignment file supplied are reported in separate columns. 

**depth**
    

samtools depth [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

Computes the read depth at each position or region. 

**ampliconstats**
    

samtools ampliconstats [_options_] _primers.bed_ _in.sam_ |_in.bam_ |_in.cram_[...] 

samtools ampliconstats collects statistics from one or more input alignment files and produces tables in text format. The output can be visualized graphically using plot-ampliconstats. 

The alignment files should have previously been clipped of primer sequence, for example by **samtools ampliconclip** and the sites of these primers should be specified as a bed file in the arguments. 

**mpileup**
    

samtools mpileup [**-EB**] [**-C** _capQcoef_] [**-r** _reg_] [**-f** _in.fa_] [**-l** _list_] [**-Q** _minBaseQ_] [**-q** _minMapQ_] _in.bam_ [_in2.bam_ [_..._]] 

Generate textual pileup for one or multiple BAM files. For VCF and BCF output, please use the **bcftools mpileup** command instead. Alignment records are grouped by sample (SM) identifiers in @RG header lines. If sample identifiers are absent, each input file is regarded as one sample. 

See the samtools-mpileup man page for a description of the pileup format and options. 

**consensus**
    

samtools consensus [**options**] _in.bam_

Generate consensus from a SAM, BAM or CRAM file based on the contents of the alignment records. The consensus is written either as FASTA, FASTQ, or a pileup oriented format. 

The default output for FASTA and FASTQ formats include one base per non-gap consensus. Hence insertions with respect to the aligned reference will be included and deletions removed. This behaviour can be adjusted. 

Two consensus calling algorithms are offered. The default computes a heterozygous consensus in a Bayesian manner, derived from the "Gap5" consensus algorithm. A simpler base frequency counting method is also available. 

**reference**
    

samtools reference [**options**] _in.bam_

Generate a reference from a SAM, BAM or CRAM file based on the contents of the SEQuence field and the MD:Z: auxiliary tags, or from the embedded reference blocks within a CRAM file (provided it was constructed using the **embed_ref=1** option). 

**coverage**
    

samtools coverage [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

Produces a histogram or table of coverage per chromosome. 

**merge**
    

samtools merge [**-nur1f**] [**-h** _inh.sam_] [**-t** _tag_] [**-R** _reg_] [**-b** _list_] _out.bam_ _in1.bam_ [_in2.bam_ _in3.bam_ ... _inN.bam_] 

Merge multiple sorted alignment files, producing a single sorted output file that contains all the input records and maintains the existing sort order. 

If **-h** is specified the @SQ headers of input files will be merged into the specified header, otherwise they will be merged into a composite header created from the input headers. If the @SQ headers differ in order this may require the output file to be re-sorted after merge. 

The ordering of the records in the input files must match the usage of the **-n** and **-t** command-line options. If they do not, the output order will be undefined. See **sort** for information about record ordering. 

**split**
    

samtools split [_options_] _merged.sam_ |_merged.bam_ |_merged.cram_

Splits a file by read group, producing one or more output files matching a common prefix (by default based on the input filename) each containing one read-group. 

**cat**
    

samtools cat [**-b** _list_] [**-h** _header.sam_] [**-o** _out.bam_] _in1.bam_ _in2.bam_ [ ... ] 

Concatenate BAMs or CRAMs. Although this works on either BAM or CRAM, all input files must be the same format as each other. The sequence dictionary of each input file must be identical, although this command does not check this. This command uses a similar trick to **reheader** which enables fast BAM concatenation. 

**import**
    

samtools import [_options_] _in.fastq_ [ ... ] 

Converts one or more FASTQ files to unaligned SAM, BAM or CRAM. These formats offer a richer capability of tracking sample meta-data via the SAM header and per-read meta-data via the auxiliary tags. The **fastq** command may be used to reverse this conversion. 

**fastq/a**
    

samtools fastq [_options_] _in.bam_   
samtools fasta [_options_] _in.bam_

Converts a BAM or CRAM into either FASTQ or FASTA format depending on the command invoked. The files will be automatically compressed if the file names have a .gz, .bgz, or .bgzf extension. 

The input to this program must be collated by name. Use **samtools collate** or **samtools sort -n** to ensure this. 

**faidx**
    

samtools faidx <ref.fasta> [region1 [...]] 

Index reference sequence in the FASTA format or extract subsequence from indexed reference sequence. If no region is specified, **faidx** will index the file and create _< ref.fasta>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTA format. 

The input file can be compressed in the **BGZF** format. 

FASTQ files can be read and indexed by this command. Without using **\--fastq** any extracted subsequence will be in FASTA format. 

**fqidx**
    

samtools fqidx <ref.fastq> [region1 [...]] 

Index reference sequence in the FASTQ format or extract subsequence from indexed reference sequence. If no region is specified, **fqidx** will index the file and create _< ref.fastq>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTQ format. 

The input file can be compressed in the **BGZF** format. 

**samtools fqidx** should only be used on fastq files with a small number of entries. Trying to use it on a file containing millions of short sequencing reads will produce an index that is almost as big as the original file, and searches using the index will be very slow and use a lot of memory. 

**dict**
    

samtools dict _ref.fasta_ |_ref.fasta.gz_

Create a sequence dictionary file from a fasta file. 

**calmd**
    

samtools calmd [**-Eeubr**] [**-C** _capQcoef_] _aln.bam_ _ref.fasta_

Generate the MD tag. If the MD tag is already present, this command will give a warning if the MD tag generated is different from the existing tag. Output SAM by default. 

Calmd can also read and write CRAM files although in most cases it is pointless as CRAM recalculates MD and NM tags on the fly. The one exception to this case is where both input and output CRAM files have been / are being created with the _no_ref_ option. 

**fixmate**
    

samtools fixmate [**-rpcm**] [**-O** _format_] _in.nameSrt.bam out.bam_

Fill in mate coordinates, ISIZE and mate related flags from a name-sorted alignment. 

**markdup**
    

samtools markdup [**-l** _length_] [**-r**] [**-s**] [**-T**] [**-S**] _in.algsort.bam out.bam_

Mark duplicate alignments from a coordinate sorted file that has been run through **samtools fixmate** with the **-m** option. This program relies on the MC and ms tags that fixmate provides. 

**rmdup**
    

samtools rmdup [-sS] <input.srt.bam> <out.bam>

**This command is obsolete. Use markdup instead.**

**addreplacerg**
    

samtools addreplacerg [**-r** _rg-line_ | **-R** _rg-ID_] [**-m** _mode_] [**-l** _level_] [**-o** _out.bam_] _in.bam_

Adds or replaces read group tags in a file. 

**reheader**
    

samtools reheader [**-iP**] _in.header.sam in.bam_

Replace the header in _in.bam_ with the header in _in.header.sam_. This command is much faster than replacing the header with a BAM→SAM→BAM conversion. 

By default this command outputs the BAM or CRAM file to standard output (stdout), but for CRAM format files it has the option to perform an in-place edit, both reading and writing to the same file. No validity checking is performed on the header, nor that it is suitable to use with the sequence data itself. 

**targetcut**
    

samtools targetcut [**-Q** _minBaseQ_] [**-i** _inPenalty_] [**-0** _em0_] [**-1** _em1_] [**-2** _em2_] [**-f** _ref_] _in.bam_

This command identifies target regions by examining the continuity of read depth, computes haploid consensus sequences of targets and outputs a SAM with each sequence corresponding to a target. When option **-f** is in use, BAQ will be applied. This command is **only** designed for cutting fosmid clones from fosmid pool sequencing [Ref. Kitzman et al. (2010)]. 

**phase**
    

samtools phase [**-AF**] [**-k** _len_] [**-b** _prefix_] [**-q** _minLOD_] [**-Q** _minBaseQ_] _in.bam_

Call and phase heterozygous SNPs. 

**depad**
    

samtools depad [**-SsCu1**] [**-T** _ref.fa_] [**-o** _output_] _in.bam_

Converts a BAM aligned against a padded reference to a BAM aligned against the depadded reference. The padded reference may contain verbatim "*" bases in it, but "*" bases are also counted in the reference numbering. This means that a sequence base-call aligned against a reference "*" is considered to be a cigar match ("M" or "X") operator (if the base-call is "A", "C", "G" or "T"). After depadding the reference "*" bases are deleted and such aligned sequence base-calls become insertions. Similarly transformations apply for deletions and padding cigar operations. 

**ampliconclip**
    

samtools ampliconclip [**-o** _out.file_] [**-f** _stat.file_] [**\--soft-clip**] [**\--hard-clip**] [**\--both-ends**] [**\--strand**] [**\--clipped**] [**\--fail**] [**\--no-PG**] **-b** _bed.file in.file_

Clip reads in a SAM compatible file based on data from a BED file. 

**samples**
    

samtools samples [**-o** _out.file_] [**-i**] [**-T** _TAG_] [**-f** _refs.fasta_] [**-F** _refs_list_] [**-X**] 

Prints the samples from alignment files 

**reset**
    

samtools reset [**-o** _FILE_] [**-x** /**\--remove-tag** _tag_list_] [**\--keep-tag** _tag_list_] [**\--reject-PG** _pgid_] [**\--no-RG**] [**\--no-PG**] [...] 

Removes alignment information from records, producing an unaligned SAM, BAM or CRAM file. Flags are reset, header tags are updated or removed as appropriate, and auxiliary tags are removed or retained as specified. Note that the sort order is unchanged. 

## SAMTOOLS OPTIONS

These are options that are passed after the **samtools** command, before any sub-command is specified. 

**help** , **\--help**
    

Display a brief usage message listing the samtools commands available. If the name of a command is also given, e.g., **samtools help view** , the detailed usage message for that particular command is displayed. 

**\--version**
    

Display the version numbers and copyright information for samtools and the important libraries used by samtools. 

**\--version-only**
    

Display the full samtools version number in a machine-readable format. 

## GLOBAL COMMAND OPTIONS

Several long-options are shared between multiple samtools sub-commands: **\--input-fmt** , **\--input-fmt-option** , **\--output-fmt** , **\--output-fmt-option** , **\--reference** , **\--write-index** , and **\--verbosity**. The input format is auto-detected and specifying the format is unnecessary, so this option is rarely offered. Note that not all subcommands have all options. Consult the subcommand help for more details. 

Format strings recognised are "sam", "sam.gz", "bam" and "cram". They may be followed by a comma separated list of options as _key_ or _key_ =_value_. See below for examples. 

The **fmt-option** arguments accept either a single _option_ or _option_ =_value_. Note that some options only work on some file formats and only on read or write streams. If value is unspecified for a boolean option, the value is assumed to be 1. The valid options are as follows. 

**level=**_INT_
    

Output only. Specifies the compression level from 1 to 9, or 0 for uncompressed. If the output format is SAM, this also enables BGZF compression, otherwise SAM defaults to uncompressed. 

**nthreads=**_INT_
    

Specifies the number of threads to use during encoding and/or decoding. For BAM this will be encoding only. In CRAM the threads are dynamically shared between encoder and decoder. 

**filter=**_STRING_
    

Apply filter STRING to all incoming records, rejecting any that do not satisfy the expression. See the FILTER EXPRESSIONS section below for specifics. 

**reference=**_fasta_file_
    

Specifies a FASTA reference file for use in CRAM encoding or decoding. It usually is not required for decoding except in the situation of the MD5 not being obtainable via the REF_PATH or REF_CACHE environment variables. 

**decode_md=**_0|1_
    

CRAM input only; defaults to 1 (on). CRAM does not typically store MD and NM tags, preferring to generate them on the fly. When this option is 0 missing MD, NM tags will not be generated. It can be particularly useful when combined with a file encoded using store_md=1 and store_nm=1. 

**store_md=**_0|1_
    

CRAM output only; defaults to 0 (off). CRAM normally only stores MD tags when the reference is unknown and lets the decoder generate these values on-the-fly (see decode_md). 

**store_nm=**_0|1_
    

CRAM output only; defaults to 0 (off). CRAM normally only stores NM tags when the reference is unknown and lets the decoder generate these values on-the-fly (see decode_md). 

**ignore_md5=**_0|1_
    

CRAM input only; defaults to 0 (off). When enabled, md5 checksum errors on the reference sequence and block checksum errors within CRAM are ignored. Use of this option is strongly discouraged. 

**required_fields=**_bit-field_
    

CRAM input only; specifies which SAM columns need to be populated. By default all fields are used. Limiting the decode to specific columns can have significant performance gains. The bit-field is a numerical value constructed from the following table.  **0x1**|  SAM_QNAME  
---|---  
**0x2**|  SAM_FLAG  
**0x4**|  SAM_RNAME  
**0x8**|  SAM_POS  
**0x10**|  SAM_MAPQ  
**0x20**|  SAM_CIGAR  
**0x40**|  SAM_RNEXT  
**0x80**|  SAM_PNEXT  
**0x100**|  SAM_TLEN  
**0x200**|  SAM_SEQ  
**0x400**|  SAM_QUAL  
**0x800**|  SAM_AUX  
**0x1000**|  SAM_RGAUX  
  
**name_prefix=**_string_
    

CRAM input only; defaults to output filename. Any sequences with auto-generated read names will use _string_ as the name prefix. 

**multi_seq_per_slice=**_0|1_
    

CRAM output only; defaults to 0 (off). By default CRAM generates one container per reference sequence, except in the case of many small references (such as a fragmented assembly). 

**version=**_major.minor_
    

CRAM output only. Specifies the CRAM version number. Acceptable values are "2.1", "3.0", and "3.1". 

**seqs_per_slice=**_INT_
    

CRAM output only; defaults to 10000. 

**slices_per_container=**_INT_
    

CRAM output only; defaults to 1. The effect of having multiple slices per container is to share the compression header block between multiple slices. This is unlikely to have any significant impact unless the number of sequences per slice is reduced. (Together these two options control the granularity of random access.) 

**embed_ref=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, this will store portions of the reference sequence in each slice, permitting decode without having requiring an external copy of the reference sequence. 

**no_ref=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, sequences will be stored verbatim with no reference encoding. This can be useful if no reference is available for the file. 

**use_bzip2=**_0|1_
    

CRAM output only; defaults to 0 (off). Permits use of bzip2 in CRAM block compression. 

**use_lzma=**_0|1_
    

CRAM output only; defaults to 0 (off). Permits use of lzma in CRAM block compression. 

**use_arith=**_0|1_
    

CRAM ≥ 3.1 output only; enables use of arithmetic entropy coding in CRAM block compression. This is off by default, but enabled for archive mode. This is significantly slower but sometimes smaller than the standard rANS entropy encoder. 

**use_fqz=**_0|1_
    

CRAM ≥ 3.1 output only; enables and disables the fqzcomp quality compression method. This is on by default for version 3.1 and above only when the small and archive profiles are in use. 

**use_tok=**_0|1_
    

CRAM ≥ 3.1 output only; enables and disables the name tokeniser compression method. This is on by default for version 3.1 and above. 

**lossy_names=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, templates with all members within the same CRAM slice will have their read names removed. New names will be automatically generated during decoding. Also see the **name_prefix** option. 

**fast, normal, small, archive**
    

CRAM output only. Set the CRAM compression profile. This is a simplified way of setting many output options at once. It changes the following options according to the profile in use. The "normal" profile is the default. 

**Option**| **fast**| **normal**| **small**| **archive**  
---|---|---|---|---  
**level**|  1| 5| 6| 7  
**use_bzip2**|  off| off| on| on  
**use_lzma**|  off| off| off| on if level>7  
**use_tok(*)**|  off| on| on| on  
**use_fqz(*)**|  off| off| on| on  
**use_arith(*)**|  off| off| off| on  
**seqs_per_slice**|  10000| 10000| 25000| 100000  
  
(*) **use_tok** , **use_fqz** and **use_arith** are only enabled for CRAM version 3.1 and above. 

The **level** listed is only the default value, and will not be set if it has been explicitly changed already. Additionally **bases_per_slice** is set to **500*seqs_per_slice** unless previously explicitly set. 

**fastq_name2**
    

FASTQ input only. Indicates that the names are not the first word in the header, but the second. This is a FASTQ variant commonly used in the SRA and ENA archives. 

**fastq_casava**
    

FASTQ input and output only. The Illumina CASAVA identifiers are stored in the second word of the FASTQ header lines and store read meta-data. The CASAVA tag defines the data held in the READ1, READ2 and QCFAIL flags and the barcode auxiliary tag ("BC" by default). This option may be used to both read and write CASAVA identifiers. 

**fastq_barcode=**_TAG_
    

FASTQ input and output only. When the **fastq_casava** option is used, this controls the name of the barcode aux tag to be used. _TAG_ defaults to "BC" if not specified. 

**fastq_aux=**_LIST_
    

FASTQ input and output only. Processes SAM format auxiliary tags following the other fields on the record identifier lines. If no **=**_LIST_ is specified or _LIST_ is "1" then all aux tags listed are copied to/from the SAM record. Otherwise it is a comma separated list of 2-letter tag types and is used to control which tags are processed with any others being omitted. 

Note as commas are used to separate options in the **\--output-fmt** string detailing file format and options combined together, you will need to use the **\--output-fmt-option** option if you want to specify a comma separated list of tag types. 

**fastq_rnum**
    

FASTQ output only. If set, paired reads will have "/1" and "/2" appended to their read names. This has no effect on unpaired reads. When reading FASTQ these suffixes are automatically detected and processed irrespective of the **fastq_rnum** option. 

**fastq_umi=**_TAGLIST_
    

FASTQ input and output only. When reading from a FASTQ file this indicates to extract the UMI tag from the read name and to put it in the TAG specified (which defaults to `RX' if no tag name is given). The UMI is assumed to be the 8th colon-separated element, conforming to Illumina BCL to FASTQ conversion specifications. However see the **fastq_umi_regexp** option for altering this. 

When converting from SAM to FASTQ, _TAGLIST_ is a comma separated list of tags which are checked in turn for their presence. The string from the first tag found is then appended to the end of the read-name. There is no regexp available in this case and the data is always appended to the end of the name, or if hash-number is present (for example `name#49') to just prior to the hash character. The _TAGLIST_ defaults to `OX,RX'. 

**fastq_umi_regex=**_REGEX_
    

FASTQ input only. Specifies the regular expression used for finding UMI strings in a read name. Any text within the single bracketted element will be used as the UMI string. Text matched by that string will be removed from the read name, with anything to the right of it being moved leftwards. This defaults to `^[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:([^:#/]+)'. 

For example: 
    
    
    samtools view --input-fmt-option decode_md=0
        --output-fmt cram,version=3.0 --output-fmt-option embed_ref
        --output-fmt-option seqs_per_slice=2000 -o foo.cram foo.bam
    
    
    
    samtools view -O cram,small -o bar.cram bar.bam
    

The **\--write-index** option enables automatic index creation while writing out BAM, CRAM or bgzf SAM files. Note to get compressed SAM as the output format you need to manually request a compression level, otherwise all SAM files are uncompressed. By default SAM and BAM will use CSI indices while CRAM will use CRAI indices. If you need to create BAI indices note that it is possible to specify the name of the index being written to, and hence the format, by using the **filename##idx##indexname** notation. 

For example: to convert a BAM to a compressed SAM with CSI indexing: 
    
    
    samtools view -h -O sam,level=6 --write-index in.bam -o out.sam.gz
    

To convert a SAM to a compressed BAM using BAI indexing: 
    
    
    samtools view --write-index in.sam -o out.bam##idx##out.bam.bai
    

The **\--verbosity** _INT_ option sets the verbosity level for samtools and HTSlib. The default is 3 (HTS_LOG_WARNING); 2 reduces warning messages and 0 or 1 also reduces some error messages, while values greater than 3 produce increasing numbers of additional warnings and logging messages. 

## FILTER EXPRESSIONS

Filter expressions are used as an on-the-fly checking of incoming SAM, BAM or CRAM records, discarding records that do not match the specified expression. 

The language used is primarily C style, but with a few differences in the precedence rules for bit operators and the inclusion of regular expression matching. 

The operator precedence, from strongest binding to weakest, is: 

Grouping| **(, )**|  E.g. "(1+2)*3"  
---|---|---  
Values:| **literals, vars**|  Numbers, strings and variables  
Unary ops:| **+, -, !, ~**|  E.g. -10 +10, !10 (not), ~5 (bit not)  
Math ops:| ***, /, %**|  Multiply, division and (integer) modulo  
Math ops:| **+, -**|  Addition / subtraction  
Bit-wise:| **&**|  Integer AND  
Bit-wise| **^**|  Integer XOR  
Bit-wise| **|**|  Integer OR  
Conditionals:| **> , >=, <, <=**  
Equality:| **==, !=, =~, !~**|  =~ and !~ match regular expressions  
Boolean:| **& &, ||**| Logical AND / OR  
  
Expressions are computed using floating point mathematics, so "10 / 4" evaluates to 2.5 rather than 2. They may be written as integers in decimal or "0x" plus hexadecimal, and floating point with or without exponents.However operations that require integers first do an implicit type conversion, so "7.9 % 5" is 2 and "7.9 & 4.1" is equivalent to "7 & 4", which is 4. Strings are always specified using double quotes. To get a double quote in a string, use backslash. Similarly a double backslash is used to get a literal backslash. For example **ab\"c\\\d** is the string **ab"c\d**. 

Comparison operators are evaluated as a match being 1 and a mismatch being 0, thus "(2 > 1) + (3 < 5)" evaluates as 2. All comparisons involving undefined (null) values are deemed to be false. 

The variables are where the file format specifics are accessed from the expression. The variables correspond to SAM fields, for example to find paired alignments with high mapping quality and a very large insert size, we may use the expression "**mapq >= 30 && (tlen >= 100000 || tlen <= -100000)**". Valid variable names and their data types are: 

**endpos**|  int| Alignment end position (1-based)  
---|---|---  
**flag**|  int| Combined FLAG field  
**flag.paired**|  int| Single bit, 0 or 1  
**flag.proper_pair**|  int| Single bit, 0 or 2  
**flag.unmap**|  int| Single bit, 0 or 4  
**flag.munmap**|  int| Single bit, 0 or 8  
**flag.reverse**|  int| Single bit, 0 or 16  
**flag.mreverse**|  int| Single bit, 0 or 32  
**flag.read1**|  int| Single bit, 0 or 64  
**flag.read2**|  int| Single bit, 0 or 128  
**flag.secondary**|  int| Single bit, 0 or 256  
**flag.qcfail**|  int| Single bit, 0 or 512  
**flag.dup**|  int| Single bit, 0 or 1024  
**flag.supplementary**|  int| Single bit, 0 or 2048  
**hclen**|  int| Number of hard-clipped bases  
**library**|  string| Library (LB header via RG)  
**mapq**|  int| Mapping quality  
**mpos**|  int| Synonym for pnext  
**mrefid**|  int| Mate reference number (0 based)  
**mrname**|  string| Synonym for rnext  
**ncigar**|  int| Number of cigar operations  
**pnext**|  int| Mate's alignment position (1-based)  
**pos**|  int| Alignment position (1-based)  
**qlen**|  int| Alignment length: no. query bases  
**qname**|  string| Query name  
**qual**|  string| Quality values (raw, 0 based)  
**refid**|  int| Integer reference number (0 based)  
**rlen**|  int| Alignment length: no. reference bases  
**rname**|  string| Reference name  
**rnext**|  string| Mate's reference name  
**sclen**|  int| Number of soft-clipped bases  
**seq**|  string| Sequence  
**tlen**|  int| Template length (insert size)  
**[XX]**|  int / string| XX tag value  
  
Flags are returned either as the whole flag value or by checking for a single bit. Hence the filter expression **flag.dup** is equivalent to **flag & 1024**. 

"qlen" and "rlen" are measured using the CIGAR string to count the number of query (sequence) and reference bases consumed. Note "qlen" may not exactly match the length of the "seq" field if the sequence is "*". 

"sclen" and "hclen" are the number of soft and hard-clipped bases respectively. The formula "qlen-sclen" gives the number of sequence bases used in the alignment, distinguishing between global alignment and local alignment length. 

"endpos" is the (1-based inclusive) position of the rightmost mapped base of the read, as measured using the CIGAR string, and for mapped reads is equivalent to "pos+rlen-1". For unmapped reads, it is the same as "pos". 

Reference names may be matched either by their string forms ("rname" and "mrname") or as the Nth **@SQ** line (counting from zero) as stored in BAM using "tid" and "mtid" respectively. 

Auxiliary tags are described in square brackets and these expand to either integer or string as defined by the tag itself (**XX:Z:**_string_ or **XX:i:**_int_). For example **[NM] >=10** can be used to look for alignments with many mismatches and **[RG]=~"grp[ABC]-"** will match the read-group string. 

If no comparison is used with an auxiliary tag it is taken simply to be a test for the existence of that tag. So **[NM]** will return any record containing an NM tag, even if that tag is zero (**NM:i:0**). In htslib <= 1.15 negating this with **![NM]** gave misleading results as it was true if the tag did not exist or did exist but was zero. Now this is strictly does-not-exist. An explicit **exists([NM])** and **!exists([NM])** function has also been added to make this intention clear. 

Similarly in htslib <= 1.15 using **[NM]!=0** was true both when the tag existed and was not zero as well as when the tag did not exist. From 1.16 onwards all comparison operators are only true for tags that exist, so **[NM]!=0** works as expected. 

Some simple functions are available to operate on strings. These treat the strings as arrays of bytes, permitting their length, minimum, maximum and average values to be computed. These are useful for processing Quality Scores. 

**length(x)**|  Length of the string (excluding nul char)  
---|---  
**min(x)**|  Minimum byte value in the string  
**max(x)**|  Maximum byte value in the string  
**avg(x)**|  Average byte value in the string  
  
Note that "avg" is a floating point value and it may be NAN for empty strings. This means that "avg(qual)" does not produce an error for records that have both seq and qual of "*". NAN values will fail any conditional checks, so e.g. "avg(qual) > 20" works and will not report these records. NAN also fails all equality, < and > comparisons, and returns zero when given as an argument to the **exists** function. It can be negated with **!x** in which case it becomes true. 

Functions that operate on both strings and numerics: 

**exists(x)**|  True if the value exists (or is explicitly true).  
---|---  
**default(x,d)**|  Value **x** if it exists or **d** if not.  
  
Functions that apply only to numeric values: 

**sqrt(x)**|  Square root of **x**  
---|---  
**log(x)**|  Natural logarithm of **x**  
**pow(x, y)**|  Power function, **x** to the power of **y**  
**exp(x)**|  Base-e exponential, equivalent to **pow(e,x)**  
  
## ENVIRONMENT VARIABLES

**HTS_PATH**
    

A colon-separated list of directories in which to search for HTSlib plugins. If $HTS_PATH starts or ends with a colon or contains a double colon (**::**), the built-in list of directories is searched at that point in the search. 

If no HTS_PATH variable is defined, the built-in list of directories specified when HTSlib was built is used, which typically includes **/usr/local/libexec/htslib** and similar directories. 

**REF_PATH**
    

A colon separated (semi-colon on Windows) list of locations in which to look for sequences identified by their MD5sums. This can be either a list of directories or URLs. Note that if a URL is included then the colon in http:// and ftp:// and the optional port number will be treated as part of the URL and not a PATH field separator. Alternatively a double colon may be used to indicate a single colon character. If REF_PATH includes **%**_num_**s** then it is replaced with the next _num_ elements of the md5sum. An implicit **/%s** is also added to each path element if any md5sum digits are unused. For example "REF_PATH=/some/dir/%4s/%s" or "REF_PATH=/some/dir/%4s" will search a directory structure with the first 4 characters of the md5sum as a subdirectory and the remaining 28 as the filename within that directory. 

Version 1.21 and earlier defaulted to using the EBI's CRAM reference server if no REF_PATH was specified. This default has been removed to reduce load on the EBI's service. It is recommended that a site-wide proxy is set up to allow better sharing of downloaded references, for example the _ref-cache_ server provided with HTSlib. The original behaviour can be restored by including **http://www.ebi.ac.uk/ena/cram/md5/%s** in your REF_PATH. If that is done, it is strongly encouraged you also specify a local REF_CACHE directory. 

See <<https://www.htslib.org/doc/reference_seqs.html>> and **REFERENCE SEQUENCES** below for more information. 

**REF_CACHE**
    

This can be defined to a single location housing a local cache of references. When REF_CACHE is set any non-local reference will create a file in the local REF_CACHE named after the sequence md5sum. This cache will be searched prior to REF_PATH. If you wish to search REF_CACHE but not to further populate it, add the directory to the start of REF_PATH instead. 

As per REF_PATH, the percent notation (e.g. "dir/%2s/%2s/%s") may be used to avoid too many files within a single directory. 

To pre-populate the REF_CACHE a script **misc/seq_cache_populate.pl** is provided in the Samtools distribution. This takes a fasta file or a directory of fasta files and generates the MD5sum named files. 

For example if you use **seq_cache_populate -subdirs 2 -root /local/ref_cache** to create 2 nested subdirectories (the default), each consuming 2 characters of the MD5sum, then REF_CACHE must be set to **/local/ref_cache/%2s/%2s/%s**. 

## REFERENCE SEQUENCES

The CRAM format requires use of a reference sequence for both reading and writing. 

When reading a CRAM the **@SQ** headers are interrogated to identify the reference sequence MD5sum (**M5:** tag) and the local reference sequence filename (**UR:** tag). Note that non-local URIs in the UR tag are not used, but _file://_ is supported. This is a change in behaviour, but not documentation, to htslib 1.21. 

To create a CRAM the **@SQ** headers will also be read to identify the reference sequences, but M5: and UR: tags may not be present. In this case the **-T** and **-t** options of samtools view may be used to specify the fasta or fasta.fai filenames respectively (provided the .fasta.fai file is also backed up by a .fasta file). 

The search order to obtain a reference is: 

Use any local file specified by the command line options (eg -T). 

Look for MD5 via REF_CACHE environment variable. 

Look for MD5 in each element of the REF_PATH environment variable. 

Look for a local file listed in the UR: header tag. 

## EXAMPLES

  * Import SAM to BAM when **@SQ** lines are present in the header: 
        
        samtools view -b aln.sam > aln.bam
        

If **@SQ** lines are absent: 
        
        samtools faidx ref.fa
        samtools view -bt ref.fa.fai aln.sam > aln.bam
        

where _ref.fa.fai_ is generated automatically by the **faidx** command. 

  * Convert a BAM file to a CRAM file using a local reference sequence. 
        
        samtools view -C -T ref.fa aln.bam > aln.cram
        

## AUTHOR

Heng Li from the Sanger Institute wrote the original C version of samtools. Bob Handsaker from the Broad Institute implemented the BGZF library. Petr Danecek and Heng Li wrote the VCF/BCF implementation. James Bonfield from the Sanger Institute developed the CRAM implementation. Other large code contributions have been made by John Marshall, Rob Davies, Martin Pollard, Andrew Whitwham, Valeriu Ohan, Vasudeva Sarma (all while primarily at the Sanger Institute), with numerous other smaller but valuable contributions. See the per-command manual pages for further authorship. 

## SEE ALSO

[_samtools-addreplacerg_](samtools-addreplacerg.html) (1), [_samtools-ampliconclip_](samtools-ampliconclip.html) (1), [_samtools-ampliconstats_](samtools-ampliconstats.html) (1), [_samtools-bedcov_](samtools-bedcov.html) (1), [_samtools-calmd_](samtools-calmd.html) (1), [_samtools-cat_](samtools-cat.html) (1), [_samtools-checksum_](samtools-checksum.html) (1), [_samtools-collate_](samtools-collate.html) (1), [_samtools-consensus_](samtools-consensus.html) (1), [_samtools-coverage_](samtools-coverage.html) (1), [_samtools-cram-size_](samtools-cram-size.html) (1), [_samtools-depad_](samtools-depad.html) (1), [_samtools-depth_](samtools-depth.html) (1), [_samtools-dict_](samtools-dict.html) (1), [_samtools-faidx_](samtools-faidx.html) (1), [_samtools-fasta_](samtools-fasta.html) (1), [_samtools-fastq_](samtools-fastq.html) (1), [_samtools-fixmate_](samtools-fixmate.html) (1), [_samtools-flags_](samtools-flags.html) (1), [_samtools-flagstat_](samtools-flagstat.html) (1), [_samtools-fqidx_](samtools-fqidx.html) (1), [_samtools-head_](samtools-head.html) (1), [_samtools-idxstats_](samtools-idxstats.html) (1), [_samtools-import_](samtools-import.html) (1), [_samtools-index_](samtools-index.html) (1), [_samtools-markdup_](samtools-markdup.html) (1), [_samtools-merge_](samtools-merge.html) (1), [_samtools-mpileup_](samtools-mpileup.html) (1), [_samtools-phase_](samtools-phase.html) (1), [_samtools-quickcheck_](samtools-quickcheck.html) (1), [_samtools-reference_](samtools-reference.html) (1), [_samtools-reheader_](samtools-reheader.html) (1), [_samtools-reset_](samtools-reset.html) (1), [_samtools-rmdup_](samtools-rmdup.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_samtools-split_](samtools-split.html) (1), [_samtools-stats_](samtools-stats.html) (1), [_samtools-targetcut_](samtools-targetcut.html) (1), [_samtools-tview_](samtools-tview.html) (1), [_samtools-view_](samtools-view.html) (1), [_bcftools_](bcftools.html) (1), [_sam_](sam.html) (5), [_tabix_](tabix.html) (1) _ref-cache(1)_

Samtools website: <<http://www.htslib.org/>>   
File format specification of SAM/BAM,CRAM,VCF/BCF: <<http://samtools.github.io/hts-specs>>   
Samtools latest source: <<https://github.com/samtools/samtools>>   
HTSlib latest source: <<https://github.com/samtools/htslib>>   
Bcftools website: <<http://samtools.github.io/bcftools>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-addreplacerg(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools addreplacerg – adds or replaces read group tags 

## SYNOPSIS

samtools [addreplacerg](samtools-addreplacerg.html) [**-r** _rg-line_ | **-R** _rg-ID_] [**-m** _mode_] [**-u**] [**-o** _out.bam_] _in.bam_

## DESCRIPTION

Adds or replaces read group tags in a file. Also allows for adding and updating @RG lines in the header. 

## OPTIONS

**-r** _STRING_
    

Allows you to specify a read group line to append to the header and applies it to the reads specified by the -m option. If repeated it automatically adds in tabs between invocations. 

**-R** _STRING_
    

Allows you to specify the read group ID of an existing @RG line and applies it to the reads specified. 

**-m** _MODE_
    

If you choose orphan_only then existing RG tags are not overwritten, if you choose overwrite_all, existing RG tags are overwritten. The default is overwrite_all. 

**-o** _STRING_
    

Write the final output to STRING. The default is to write to stdout. 

By default, samtools tries to select a format based on the output filename extension; if output is to standard output or no format can be deduced, **sam** is selected. 

**-u**
    

Output uncompressed SAM, BAM or CRAM. 

**-w**
    

Overwrite an existing @RG line, if a new one with the same ID value is provided. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## AUTHOR

Written by Martin Pollard from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-split_](samtools-split.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-ampliconclip(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools ampliconclip – clip reads using a BED file 

## SYNOPSIS

samtools [ampliconclip](samtools-ampliconclip.html) [**-o** _out.file_] [**-f** _stat.file_] [**\--soft-clip**] [**\--hard-clip**] [**\--both-ends**] [**\--strand**] [**\--clipped**] [**\--fail**] [**\--filter-len** _INT_] [**\--fail-len** _INT_] [**\--unmap-len** _INT_] [**\--no-excluded**] [**\--rejects-file** _rejects.file_] [**\--original**] [**\--keep-tag**] [**\--tolerance**] [**\--no-PG**] [**-u**] **-b** _bed.file in.file_

## DESCRIPTION

Clips the ends of read alignments if they intersect with regions defined in a BED file. While this tool was originally written for clipping read alignment positions which correspond to amplicon primer locations it can also be used in other contexts. 

BED file entries used are chrom, chromStart, chromEnd and, optionally, strand. Standard BED file format must be used, so if strand is needed then the name and score fields must also be present (even though ampliconclip does not read them). There is a default tolerance of 5 bases when matching chromStart and chromEnd to alignments. 

By default the reads are soft clipped and clip is only done from the 5' end. 

Some things to be aware of. While ordering is not significant, adjustments to the left most mapping position (_POS_) will mean that coordinate sorted files will need resorting. In such cases the sorting order in the header is set to unknown. Clipping of reads results in template length (_TLEN_) being incorrect. This can be corrected by **samtools fixmates**. Any _MD_ and _NM_ aux tags will also be incorrect, which can be fixed by **samtools calmd**. By default _MD_ and _NM_ tags are removed though if the output is in CRAM format these tags will be automatically regenerated. 

## OPTIONS

**-b** _FILE_
    

BED file of regions (e.g. amplicon primers) to be removed. 

**-o** _FILE_
    

Output file name (defaults to stdout). 

**-f** _FILE_
    

File to write stats to (defaults to stderr). 

**-u**
    

Output uncompressed SAM, BAM or CRAM. 

**\--soft-clip**
    

Soft clip reads (default). 

**\--hard-clip**
    

Hard clip reads. 

**\--both-ends**
    

Clip at both the 5' and the 3' ends where regions match. When using this option the **\--strand** option is ignored. 

**\--strand**
    

Use strand entry from the BED file to clip on the matching forward or reverse alignment. 

**\--clipped**
    

Only output clipped reads. Filter all others. 

**\--fail**
    

Mark unclipped reads as QC fail. 

**\--filter-len** _INT_
    

Filter out reads of INT size or shorter. In this case soft clips are not counted toward read length. An INT of 0 will filter out reads with no matching bases. 

**\--fail-len** _INT_
    

As **\--filter-len** but mark as QC fail rather then filter out. 

**\--unmap-len** _INT_
    

As **\--filter-len** but mark as unmapped. Default is 0 (no matching reads). -1 will disable. 

**\--no-excluded**
    

Filter out any reads that are marked as QCFAIL or are unmapped. This works on the state of the reads before clipping takes place. 

**\--rejects-file** _FILE_
    

Write any filtered reads out to a file. 

**\--primer-counts** _FILE_
    

File to write with read counts per bed entry (bedgraph format). 

**\--original**
    

Add an OA tag with the original data for clipped files. 

**\--keep-tag**
    

In clipped reads, keep the possibly invalid NM and MD tags. By default these tags are deleted. 

**\--tolerance** _INT_
    

The amount of latitude given in matching regions to alignments. Default 5 bases. 

**\--no-PG**
    

Do not at a PG line to the header. 

## AUTHOR

Written by Andrew Whitwham and Rob Davies, both from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_samtools-fixmate_](samtools-fixmate.html) (1), [_samtools-calmd_](samtools-calmd.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-ampliconstats(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools ampliconstats – produces statistics from amplicon sequencing alignment file 

## SYNOPSIS

samtools [ampliconstats](samtools-ampliconstats.html) [_options_] _primers.bed_ _in.sam_ |_in.bam_ |_in.cram_... 

## DESCRIPTION

samtools ampliconstats collects statistics from one or more input alignment files and produces tables in text format. The output can be visualized graphically using plot-ampliconstats. 

The alignment files should have previously been clipped of primer sequence, for example by "samtools ampliconclip" and the sites of these primers should be specified as a bed file in the arguments. Each amplicon must be present in the bed file with one or more LEFT primers (direction "+") followed by one or more RIGHT primers. For example: 
    
    
    MN908947.3  1875  1897  nCoV-2019_7_LEFT        60  +
    MN908947.3  1868  1890  nCoV-2019_7_LEFT_alt0   60  +
    MN908947.3  2247  2269  nCoV-2019_7_RIGHT       60  -
    MN908947.3  2242  2264  nCoV-2019_7_RIGHT_alt5  60  -
    MN908947.3  2181  2205  nCoV-2019_8_LEFT        60  +
    MN908947.3  2568  2592  nCoV-2019_8_RIGHT       60  -
    

Ampliconstats will identify which read belongs to which amplicon. For purposes of computing coverage statistics for amplicons with multiple primer choices, only the innermost primer locations are used. 

A summary of output sections is listed below, followed by more detailed descriptions. 

**SS**
    

Amplicon and file counts. Always comes first 

**AMPLICON**
    

Amplicon primer locations 

**FSS**
    

File specific: summary stats 

**FRPERC**
    

File specific: read percentage distribution between amplicons 

**FDEPTH**
    

File specific: average read depth per amplicon 

**FVDEPTH**
    

File specific: average read depth per amplicon, full length only 

**FREADS**
    

File specific: numbers of reads per amplicon 

**FPCOV**
    

File specific: percent coverage per amplicon 

**FTCOORD**
    

File specific: template start,end coordinate frequencies per amplicon 

**FAMP**
    

File specific: amplicon correct / double / treble length counts 

**FDP_ALL**
    

File specific: template depth per reference base, all templates 

**FDP_VALID**
    

File specific: template depth per reference base, valid templates only 

**CSS**
    

Combined summary stats 

**CRPERC**
    

Combined: read percentage distribution between amplicons 

**CDEPTH**
    

Combined: average read depth per amplicon 

**CVDEPTH**
    

Combined: average read depth per amplicon, full length only 

**CREADS**
    

Combined: numbers of reads per amplicon 

**CPCOV**
    

Combined: percent coverage per amplicon 

**CTCOORD**
    

Combined: template coordinates per amplicon 

**CAMP**
    

Combined: amplicon correct / double / treble length counts 

**CDP_ALL**
    

Combined: template depth per reference base, all templates 

**CDP_VALID**
    

Combined: template depth per reference base, valid templates only 

File specific sections start with both the section key and the filename basename (minus directory and .sam, .bam or .cram suffix). 

Note that the file specific sections are interleaved, ordered first by file and secondly by the file specific stats. To collate them together, use "grep" to pull out all data of a specific type. 

The combined sections (C*) follow the same format as the file specific sections, with a different key. For simplicity of parsing they also have a filename column which is filled out with "COMBINED". These rows contain stats aggregated across all input files. 

## SS / AMPLICON

This section is once per file and includes summary information to be utilised for scaling of plots, for example the total number of amplicons and files present, tool version number, and command line arguments. The second column is the filename or "COMBINED". This is followed by the reference name (unless single-ref mode is enabled), and the summary statistic name and value. 

The AMPLICON section is a reformatting of the input BED file. Each line consists of the reference name (unless single-ref mode is enable), the amplicon number and the _start_ -_end_ coordinates of the left and right primers. Where multiple primers are available these are comma separated, for example **10-30,15-40** in the left primer column indicates two primers have been multiplex together covering genome coordinates 10-30 inclusive and 14-40 inclusively. 

## CSS SECTION

This section consists of summary counts for the entire set of input files. These may be useful for automatic scaling of plots. 

**Number of amplicons**|  Total number of amplicons listed in primer.bed  
---|---  
**Number of files**|  Total number of SAM, BAM or CRAM files  
**End of summary**|  Always the last item. Marker for end of CSS block.  
  
## FSS SECTION

This lists summary statistics specific to an individual input file. The values reported are: 

**raw total sequences**|  Total number of sequences found in the file  
---|---  
**filtered sequences**|  Number of sequences filtered with -F option  
**failed primer match**|  Number of sequences that did not correspond to  
****| a known primer location  
**matching sequences**|  Number of sequences allocated to an amplicon  
  
## FREADS / CREADS SECTION

For each amplicon, this simply reports the count of reads that have been assigned to it. A read is assigned to an amplicon if the start and/or end of the read is within a specified number of bases of the primer sites listed in the bed file. This distance is controlled via the -m option. 

## FRPERC / CRPERC SECTION

For each amplicon, this lists what percentage of reads were assigned to this amplicon out of the total number of assigned reads. This may be used to diagnose how uniform this distribution is. 

Note this is a pure read count and has no relation to amplicon size. 

## FDEPTH / CDEPTH / FVDEPTH / CVDEPTH SECTION

Using the reads assigned to each amplicon and their start / end locations on that reference, computed using the POS and CIGAR fields, we compute the total number of bases aligned to this amplicon and corresponding the average depth. The VDEPTH variants are filtered to only include templates with end-to-end coverage across the amplicon. These can be considered to be "valid" or "usable" templates and give an indication of the minimum depth for the amplicon rather than the average depth. 

To compute the depth the length of the amplicon is computed using the innermost set of primers, if multiple choices are listed in the bed file. 

## FPCOV / CPCOV SECTION

Similar to the FDEPTH section, this is a binary status of covered or not covered per position in each amplicon. This is then expressed as a percentage by dividing by the amplicon length, which is computed using the innermost set of primers covering this amplicon. 

The minimum depth necessary to constitute a position as being "covered" is specifiable using the -d option. 

## FTCOORD / CTCOORD / FAMP / CAMP SECTION

It is possible for an amplicon to be produced using incorrect primers, giving rise to extra-long amplicons (typically double or treble length). 

The FTCOORD field holds a distribution of observed template coordinates from the input data. Each row consists of the file name, the amplicon number in question, and tab separated tuples of start, end, frequency and status (0 for OK, 1 for skipping amplicon, 2 for unknown location). Each template is only counted for one amplicon, so if the read-pairs span amplicons the count will show up in the left-most amplicon covered. 

Th COORD data may indicate which primers are being utilised if there are alternates available for a given amplicon. 

For COORD lines amplicon number 0 holds the frequency data for data that reads that have not been assigned to any amplicon. That is, they may lie within an amplicon, but they do not start or end at a known primer location. It is not recorded for BED files containing multiple references. 

The FAMP / CAMP section is a simple count per amplicon of the number of templates coming from this amplicon. Templates are counted once per amplicon, but and like the FTCOORD field if a read-pair spans amplicons it is only counted in the left-most amplicon. Each line consists of the file name, amplicon number and 3 counts for the number of templates with both ends within this amplicon, the number of templates with the rightmost end in another amplicon, and the number of templates where the other end has failed to be assigned to an amplicon. 

Note FAMP / CAMP amplicon number 0 is the summation of data for all amplicons (1 onwards). 

## FDP_ALL / CDP_ALL / FDP_VALID / CDP_VALID section

These are for depth plots per base rather than per amplicon. They distinguish between all reads in all templates, and only reads in templates considered to be "valid". Such templates have both reads (if paired) matching known primer locations from he same amplicon and have full length coverage across the entire amplicon. 

This FDP_VALID can be considered to be the minimum template depth across the amplicon. 

The difference between the VALID and ALL plots represents additional data that for some reason may not be suitable for producing a consensus. For example an amplicon that skips a primer, pairing 10_LEFT with 12_RIGHT, will have coverage for the first half of amplicon 10 and the last half of amplicon 12. Counting the number of reads or bases alone in the amplicon does not reveal the potential for non-uniformity of coverage. 

The lines start with the type keyword, file / sample name, reference name (unless single-ref mode is enabled), followed by a variable number of tab separated tuples consisting of _depth,length_. The length field is a basic form of run-length encoding where all depth values within a specified fraction of each other (e.g. >= (1-fract)*midpoint and <= (1+fract)*midpoint) are combined into a single run. This fraction is controlled via the **-D** option. 

## OPTIONS

**-f, --required-flag** _INT|STR_
    

Only output alignments with all bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0], or in string form by specifying a comma-separated list of keywords as listed by the "samtools flags" subcommand. 

**-F, --filter-flag** _INT|STR_
    

Do not output alignments with any bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0], or in string form by specifying a comma-separated list of keywords as listed by the "samtools flags" subcommand. 

**-a, --max-amplicons** _INT_
    

Specify the maximum number of amplicons permitted. 

**-b, --tcoord-bin** _INT_
    

Bin the template start,end positions into multiples of _NT_ prior to counting their frequency and reporting in the FTCOORD / CTCOORD lines. This may be useful for technologies with higher errors rates where the alignment ends will vary slightly. Defaults to 1, which is equivalent to no binning. 

**-c, --tcoord-min-count** _INT_
    

In the FTCOORD and CTCOORD lines, only record template start,end coordinate combination if they occur at least _INT_ times. 

**-d, --min-depth** _INT_
    

Specifies the minimum base depth to consider a reference position to be covered, for purposes of the FRPERC and CRPERC sections. 

**-D, --depth-bin** _FRACTION_
    

Controls the merging of neighbouring similar depths for the FDP_ALL and FDP_VALID plots. The default FRACTION is 0.01, meaning depths within +/- 1% of a mid point will be aggregated together as a run of the same value. This merging is useful to reduce the file size. Use **-D 0** to record every depth. 

**-l, --max-amplicon-length** _INT_
    

Specifies the maximum length of any individual amplicon. 

**-m, --pos-margin** _INT_
    

Reads are compared against the primer start and end locations specified in the BED file. An aligned sequence should start precisely at these locations, but sequencing errors may cause the primer clipping to be a few bases out or for the alignment to add a few extra bases of soft clip. This option specifies the margin of error permitted when matching a read to an amplicon number. 

**-o FILE**
    

Output stats to FILE. The default is to write to stdout. 

**-s, --use-sample-name**
    

Instead of using the basename component of the input path names, use the SM field from the first @RG header line. 

**-S, --single-ref**
    

Force the output format to match the older single-reference style used in Samtools 1.12 and earlier. This removes the reference names from the SS, AMPLICON, DP_ALL and DP_VALID sections. It cannot be enabled if the input BED file has more than one reference present. Note that plot-ampliconstats can process both output styles. 

**-t, --tlen-adjust** _INT_
    

Adjust the TLEN field by +/- _INT_ to compensate for primer clipping. This defaults to zero, but if the primers have been clipped and the TLEN field has not been updated using samtools fixmate then the template length will be wrong by the sum of the forward and reverse primer lengths. 

This adjustment does not have to be precise as the --pos-margin field permits some leeway. Hence if required, it should be set to approximately double the average primer length. 

**-@**_INT_
    

Number of BAM/CRAM (de)compression threads to use in addition to main thread [0]. 

## EXAMPLE

To run ampliconstats on a directory full of CRAM files and then produce a series of PNG images named "mydata*.png": 
    
    
    samtools ampliconstats V3/nCoV-2019.bed /path/*.cram > astats
    plot-ampliconstats -size 1200,900 mydata astats
    

## AUTHOR

Written by James Bonfield from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-ampliconclip_](samtools-ampliconclip.html) (1) [_samtools-stats_](samtools-stats.html) (1), [_samtools-flags_](samtools-flags.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-bedcov(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools bedcov – reports coverage over regions in a supplied BED file 

## SYNOPSIS

samtools [bedcov](samtools-bedcov.html) [_options_] _region.bed_ _in1.sam_ |_in1.bam_ |_in1.cram_[...] 

## DESCRIPTION

Reports the total read base count (i.e. the sum of per base read depths) for each genomic region specified in the supplied BED file. The regions are output as they appear in the BED file and are 0-based. Columns 1-3 are chrom/start/end as per the input BED file, followed by N columns of coverages (for N input BAMs), then (if given -d), N columns of bases-at-depth-X, then (if given -c) N columns of read counts. 

## OPTIONS

**-Q, --min-MQ** _INT_
    

Only count reads with mapping quality greater than or equal to _INT_

**-g** _FLAGS_
    

By default, reads that have any of the flags UNMAP, SECONDARY, QCFAIL, or DUP set are skipped. To include these reads back in the analysis, use this option together with the desired flag or flag combination. _FLAGS_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. [0] 

For a list of flag names see _samtools-flags_(1). 

**-G** _FLAGS_
    

Discard any read that has any of the flags specified by _FLAGS_ set. FLAGS are specified as for the **-g** option. [UNMAP,SECONDARY,QCFAIL,DUP] 

**-j**
    

Do not include deletions (D) and ref skips (N) in bedcov computation. 

**-d** _INT_
    

Print an additional column, for each file, containing the number of bases having a depth above and including the given threshold. If the option is not used, the extra column is not displayed. The option value must be an integer >= 0. 

**\--max-depth** _INT_
    

Specifies the maximum depth used for the mpileup algorithm. If **-d** is used and is larger then this value will be used instead. Defaults to 2 billion, but smaller values may be used when we do not require an exact count in excessively deep regions and are interested in maximizing speed of results. 

**-c**
    

Print an additional column with the read count for this region. This will be +1 for every read covering the region, not just starting within in. The whole read filtering options **-Q** , **-g** and **-G** options will also have an effect on this count, but **-d** will not. 

**-X**
    

If this option is set, it will allows user to specify customized index file location(s) if the data folder does not contain any index file. Example usage: samtools bedcov [options] -X <in.bed> </data_folder/in1.bam> [...] </index_folder/index1.bai> [...] 

**-H**
    

copied to the output. When it is not available, a header is created with field names matching the fields listed in the GA4GH BED specification. The **-c** and **-d** options can add further per-file columns named _in1.sam_ _count and _in1.sam_ _depth along with _in1.sam_ _count. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-calmd(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools calmd – calculates MD and NM tags 

## SYNOPSIS

samtools [calmd](samtools-calmd.html) [**-Eeubr**] [**-C** _capQcoef_] _aln.bam_ _ref.fasta_

## DESCRIPTION

Generate the MD tag. If the MD tag is already present, this command will give a warning if the MD tag generated is different from the existing tag. Output SAM by default. 

Calmd can also read and write CRAM files although in most cases it is pointless as CRAM recalculates MD and NM tags on the fly. The one exception to this case is where both input and output CRAM files have been / are being created with the _no_ref_ option. 

Note that some aligners do not include sequence or confidence values in secondary and supplementary alignment records. Where this happens in SAM files, a “*” character will be seen in the **SEQ** and **QUAL** columns. These records will be skipped, as it is not possible to recalculate the MD and NM tags without access to the query sequence. **samtools calmd** will emit a warning if any records have been skipped for this reason. 

Calmd works best on position-sorted input files, as with these it can stream through the reference sequence and so doesn't have to store much reference data at any one time. For other orderings, it may have to switch to a caching mode which keeps the reference sequences in memory. This will result in calmd using more memory (up to the full size of the reference) than it would in the position-sorted case. Note also that versions of samtools calmd up to 1.16.1 should only be used on position sorted inputs as they could be very slow when run on other orderings. 

## OPTIONS

**-A**
    

When used jointly with **-r** this option overwrites the original base quality. 

**-e**
    

Convert a the read base to = if it is identical to the aligned reference base. Indel caller does not support the = bases at the moment. 

**-u**
    

Output uncompressed BAM 

**-b**
    

Output compressed BAM 

**-C** _INT_
    

Coefficient to cap mapping quality of poorly mapped reads. See the **mpileup** command for details. [0] 

**-r**
    

Compute the BQ tag (without -A) or cap base quality by BAQ (with -A). 

**-E**
    

Extended BAQ calculation. This option trades specificity for sensitivity, though the effect is minor. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## EXAMPLES

  * Dump BAQ applied alignment for other SNP callers: 
        
        samtools calmd -bAr aln.bam > aln.baq.bam
        

It adds and corrects the **NM** and **MD** tags at the same time. The **calmd** command also comes with the **-C** option, the same as the one in **mpileup**. Apply if it helps. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-mpileup_](samtools-mpileup.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-cat(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools cat – concatenate files together 

## SYNOPSIS

samtools [cat](samtools-cat.html) [**-b** _list_] [**-h** _header.sam_] [**-o** _out.bam_] _in1.bam_ _in2.bam_ [ ... ] 

## DESCRIPTION

Concatenate BAMs or CRAMs. Although this works on either BAM or CRAM, all input files must be the same format as each other. The sequence dictionary of each input file must be identical, although this command does not check this. This command uses a similar trick to **reheader** which enables fast BAM concatenation. 

## OPTIONS

**-b** _FOFN_
    

Read the list of input BAM or CRAM files from _FOFN_. These are concatenated prior to any files specified on the command line. Multiple **-b** _FOFN_ options may be specified to concatenate multiple lists of BAM/CRAM files. 

**-h** _FILE_
    

Uses the SAM header from _FILE_. By default the header is taken from the first file to be concatenated. 

**-o** _FILE_
    

Write the concatenated output to _FILE_. By default this is sent to stdout. 

**-q**
    

[CRAM only] Query the number of containers in the CRAM file. The output is the filename, the number of containers, and the first and last container number as an inclusive range, with one file per line. 

Note this works in conjunction with the **-r** _RANGE_ option, in which case the 3rd and 4th columns become useful for identifying which containers span the requested range. 

**-r** _RANGE_
    

[CRAM only] Filter the CRAM file to a specific _RANGE_. This can be the usual chromosome:start-end syntax, or "*" for unmapped records at the end of alignments. 

If the range is of the form "#:start-end" then the start and end coordinates are interpreted as inclusive CRAM container numbers, starting at 0 and ending 1 less than the number of containers reported by **-q**. For example **-r "#:0-9"** is the first 10 CRAM containers of data. 

All range types filter data in as fast a manner as possible, using operating system read/write loops where appropriate. 

**-p** _A/B_
    

[CRAM only] Filter the CRAM file using a specific fraction. The file is split into B approximately equal parts and returns element A where A is between 1 and B inclusive. If there are more parts specified than CRAM containers then some of the output will be empty CRAMs. 

This can also be combined with the range option above to operate of parts of that range. For example **-r chr2 -p 1/10** returns the first 1/10th of data aligned against chromosome 2. 

**-f**
    

[CRAM only] Enable fast mode. When filtering by chromosome range with **-r** we normally do careful recoding of any containers that overlap the start and end of the range so the record count precisely matches that returned by a **samtools view** equivalent. Fast mode does no filtering, so may return additional alignments in the same container but outside of the requested region. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

## EXAMPLES

  * Extract a specific chromosome from a CRAM file, outputting to a new CRAM. 
        
        samtools cat -o chr10.cram -r chr10 in.cram
        

  * Split a CRAM file up into separate files, each containing at most 123 containers. 
        
        set -- $(samtools cat -q in.cram); nc=$2; s=0
        while [ $s -lt $nc ]
        do
            e=`expr $s + 123`
            if [ $e -ge $nc ]
            then
                e=$nc
            fi
            r="$s-`expr $e - 1`"; echo $r
            fn=/tmp/_part-`printf "%08d" $s`.cram
            samtools cat -o $fn in.cram -r "#:$r"
            s=$e
        done
        

  * Split any unaligned data from a (potentially aligned) CRAM file into 10 approximately equal sized pieces. 
        
        for i in `seq 1 10`
        do
           samtools cat in.cram -r "*" -p $i/10 -o part-`printf "%02d" $i`.cram
        done
        
        
        
        

## AUTHOR

Written by Heng Li from the Sanger Institute. Updated for CRAM by James Bonfield (also Sanger Institute). 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-checksum(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools checksum – produces checksums of SAM / BAM / CRAM content 

## SYNOPSIS

**samtools checksum** [_options_] _in.sam_ |_in.bam_ |_in.cram_ |_in.fastq_ [ ... ]   
**samtools checksum -m** [_options_] _in.checksum_ [ ... ] 

## DESCRIPTION

With no options, this produces an order agnostic checksum of sequence, quality, read-name and barcode related aux data in a SAM, BAM, CRAM or FASTQ file. The CRC32 checksum is used, combined together in a multiplicative prime field of size (2<<31)-1. 

The purpose of this mode is to validate that no data has been lost in data processing through the various steps of alignment, sorting and processing. Only primary alignments are recorded and the checksums computed are order agnostic so the same checksums are produced in name collated or position sorted output files. 

One set of checksums is produced per read-group as well as a combined file, plus a set for records that have no read-group assigned. This allows for validation of merging multiple runs and splitting pools by their read-group. The checksums are also reported for QC-pass only and QC-fail only (indicated by the QCFAIL BAM flag), so checksums of data identified and removed as contamination can also be tracked. 

All of the above are compatible with Biobambam2's bamseqchksum tool, which was the inspiration for this samtools command. The **-B** option further enhances compatibility by using the same output format, although it limits the functionality to the order agnostic checksums and fewer types validated. 

The **-m** or **\--merge** option can be used to merge previously generated checksums. The input filenames are checksum outputs from this tool (via shell redirection or the **-o**) option. The intended use of this is to validate no data is lost or corruption during file merging of read-group specific files, by algorithmically computing the expected checksum output. 

Additionally **checksum** can track other columns including BAM flags, mapping information (MAPQ and CIGAR), pair information (RNEXT, PNEXT and TLEN), as well as a wider list of tags. 

With the **-O** option the checksums become record order specific. Combined together with the **-a** option this can be used to validate SAM, BAM and CRAM format conversions. The CRCs per record are XORed with a record counter for the Nth record per read group. See the detailed description below for single **-O** vs double and the implications on reordering between read-groups. 

When performing such validation, it is also useful to enable data sanitisation first, as CRAM can fix up certain types of inconsistencies including common issues such as MAPQ and CIGAR strings for unaligned data. 

## OUTPUT

The output format consists of a machine readable table of checksums and human readable text starting with a "#" character. 

For compatibility with bamseqchksum the data is CRCed in specific orders before combining together to form a checksum column. The last column reported is then the combination of all checksums in that row, permitting easy comparison by looking at a single value. 

The columns reported are as follows. 

**Group**
    

The read group name. There is always an "all" group which represents all records. This is followed by one checksum set per read-group found in the file. 

**QC**
    

This is either "all" or "pass". "Pass" refers to records that do not have the QCFAIL BAM flag specified. 

**flag+seq**
    

The checksum of SAM FLAG + SEQ fields 

**+name**
    

The checksum of SAM QNAME + FLAG + SEQ fields 

**+qual**
    

The checksum of SAM FLAG + SEQ + QUAL fields 

**+aux**
    

The checksum of SAM FLAG + SEQ + selected auxiliary fields 

**+chr/pos**
    

The checksum of SAM FLAG + SEQ + RNAME (chromosome) + POSition fields 

**+mate**
    

The checksum of SAM FLAG + SEQ + RNEXT + PNEXT + ISIZE fields. 

**combined**
    

The combined checksum of all columns prior to this column. The first row will be for all alignments, so the combined checksum on the first row may be used as a whole file combined checksum. 

An example output can be seen below. 
    
    
    # Checksum for file: NA12892.chrom20.ILLUMINA.bwa.CEU.high_coverage.bam
    # Aux tags:          BC,FI,QT,RT,TC
    # BAM flags:         PAIRED,READ1,READ2
    
    
    
    # Group    QC        count  flag+seq  +name     +qual     +aux      combined
    all        all    42890086  71169bbb  633fd9f7  2a2e693f  71169bbb  09d03ed4
    SRR010946  all      262249  2957df86  3b6dcbc9  66be71f7  2957df86  58e89c25
    SRR002165  all       97846  47ff17e0  6ff8fc7b  58366bf5  47ff17e0  796eecb0
    [...cut...]
    

## OPTIONS

**-@**_COUNT_
    

Uses _COUNT_ compute threads in decoding the file. Typically this does not gain much speed beyond 2 or 3. The default is to use a single thread. 

**-B** , **\--bamseqchksum**
    

Produces a report compatible with biobambam2's bamseqchksum default output. Note this is only expected to work if no other format options have been enabled. Specifically the header line is not updated to reflect additional columns if requested. 

Bamseqchksum has more output modes and many alternative checksums. We only support the default CRC32 method. 

**-F** _FLAG_**, --exclude-flags** _FLAG_
    

Specifies which alignment _FLAGs_ to filter out. This defaults to secondary and supplementary alignments (0x900) as these can be duplicates of the primary alignment. This ensures the same number of records are checksummed in unaligned and aligned files. 

**-f** _FLAG_**, --require-flags** _FLAG_
    

A list of _FLAGs_ that are required. Defaults to zero. An example use of this may be to checksum QCFAIL only. 

**-b** _FLAG_**, --flag-mask** _FLAG_
    

The BAM _FLAG_ is masked first before checksumming. The unaligned flags will contain data about the sequencing run - whether it is paired in sequencing and if so whether this is READ1 or READ2. These flags will not change post-alignment and so everything except these three are masked out. _FLAG_ defaults to PAIRED,READ1,READ2 (0xc1). 

**-c** , **\--no-rev-comp**
    

By default the sequence and quality strings are reverse complemented before checksumming, so unaligned data does not affect the checksums. This option disables this and checksums as-is. 

**-t** _STR_**, --tags** _STR_
    

Specifies a comma-separated list of aux tags to checksum. These are concatenated together in their canonical BAM encoding in the order listed in _STR_ , prior to computing the checksums. 

If _STR_ begins with "*" then all tags are used. This can then be followed by a comma separated list of tags to exclude. For example "*,MD,NM" is all tags except MD and NM. In this mode, the tags are combined in alphanumeric order. 

The default value is "BC,FI,QT,RT,TC". 

**-O** , **\--in-order**
    

By default the CRCs are combined in a multiplicative field that is order agnostic, as multiplication is an associative operation. This option XORs the CRC with the a number indicating the Nth record number for this grouping prior to the multiply step, making the final multiplicative checksum dependent on the order of the input data. 

For the "all" row the count is taken from the Nth record in the read-group associated with this record (or the "-" row for read-group-less data). This ensures that the checksums can be subsequently merged together algorithmically using the **-m** option, but it does mean there is no validation of record swaps between read-groups. Note however due to the way ties are resolved, when running **samtools merge out.bam rg1.bam rg2.bam** we may get different orderings if we merged the two files in the opposite order. This can happen when two read-groups have alignments at the same position with the same BAM flags. Hence if we wish to check a **samtools split** followed by **samtools merge** round trip works then this counter per readgroup is a benefit. 

However, if absolute ordering needs to be validated regardless of read-groups, specifying the **-O** option twice will compute the "all" row by combining the CRC with the Nth record in the file rather than the Nth record in its readgroup. This output can no longer can merged using **checksum -m**. 

**-P** , **\--check-pos**
    

Adds a column to the output with combined chromosome and position checksums. This also incorporates the flag/sequence CRC. 

**-C** , **\--check-cigar**
    

Adds a column to the output with combined mapping quality and CIGAR checksums. This also incorporates the flag/sequence CRC. 

**-M** , **\--check-mate**
    

Adds a column to the output with combined mate reference, mate position and template length checksums. This also incorporates the flag/sequence CRC. 

**-b** _FLAGS_**, --sanitize** _FLAGS_
    

Perform data sanitization prior to checksumming. This is off by default. See samtools view for the _FLAG_ terms accepted. 

**-N** _COUNT_**, --count** _COUNT_
    

Limits the checksumming to the first _COUNT_ records from the file. 

**-a** , **\--all**
    

Checksum all data. This is equivalent to **-PCMOc -b 0xfff -f0 -F0 -z all,cigarx -t *,cF,MD,NM**. It is useful for validating round-trips between file formats, such as BAM to CRAM. 

**-T** , **\--tabs**
    

Use tabs for separating columns instead of aligned spaces. 

**-q** , **\--show-qc**
    

Also show QC pass and fail rows per read-group. These are based on the QCFAIL BAM flag. 

**-o** _FILE_**, --output** _FILE_
    

Output checksum report to _FILE_ instead of stdout. 

**-m** _FILE_**, --merge** _FILE_**...**
    

Merge checksum outputs produced by the **-o** option. This can be used to simulate or validate the effect of computing checksum on the output of a **samtools merge** command. 

The columns to report are read from the "# Group" line. The rows to report are still governed by the **-q** , **-v** and **-T** options so this can also be used for reformatting of a single file. 

Note the "all" row merging cannot be done when the two levels of order-specific checksums (**-OO**) has been used. 

**-v** , **\--verbose**
    

Increase verbosity. At level 1 or higher this also shows rows that have zero count values, which can aid machine parsing. 

## EXAMPLES

  * To check that an aligned and position sorted file contains the same data as the pre-alignment FASTQ: 
        
        samtools checksum -q pos-aln.bam
        samtools import -u -1 rg1.fastq.gz -2 rg2.fastq.gz | samtools checksum -q
        

The output for this consists of some human readable comments starting with "#" and a series of checksum lines per read-group and QC status. 
        
        # Checksum for file: SRR554369.P_aeruginosa.cram
        # Aux tags:          BC,FI,QT,RT,TC
        # BAM flags:         PAIRED,READ1,READ2
        
        
        
        # Group    QC        count  flag+seq  +name     +qual     +aux      combined
        all        all     3315742  4a812bf2  22d15cfe  507f0f57  4a812bf2  035e2f5b
        all        pass    3315742  4a812bf2  22d15cfe  507f0f57  4a812bf2  035e2f5b
        

Note as no barcode tags exist, the "+aux" column is the same as the "flag+seq" column it is based upon. 

  * To check round-tripping from BAM to CRAM and back again we can convert the BAM to CRAM and then run the checksum on the CRAM file. This does not need explicitly converting back to BAM as htslib will decode the CRAM and convert it back to the same in-memory representation that is utilised in BAM. 
        
        samtools checksum -a 9827_2#49.1m.bam
        [...cut...]
        samtools view -@8 -C -T $HREF 9827_2#49.1m.bam | samtools checksum -a
        # Checksum for file: -
        # Aux tags:          *,cF,MD,NM
        # BAM flags:         PAIRED,PROPER_PAIR,UNMAP,MUNMAP,REVERSE,MREVERSE,READ1,READ2,SECONDARY,QCFAIL,DUP,SUPPLEMENTARY
        
        
        
        # Group    QC        count  flag+seq  +name     +qual     +aux      +chr/pos  +cigar    +mate     combined
        all        all       99890  066a0706  0805371d  5506e19f  6b0eec58  60e2347c  09a2c3ba  347a3214  66c5e2de
        1#49       all       99890  066a0706  0805371d  5506e19f  6b0eec58  60e2347c  09a2c3ba  347a3214  66c5e2de
        

  * To validate that splitting a file by regroup retains all the data, we can compute checksums on the split BAMs and merge the checksum reports together to compare against the original unsplit file. (Note in the example below diff will report the filename changing, which is expected.) 
        
        samtools split -u /tmp/split/noRG.bam -f '/tmp/split/%!.%.' in.cram
        samtools checksum -a in.cram -o in.chksum
        s=$(for i in /tmp/split/*.bam;do echo "<(samtools checksum -a $i)";done)
        eval samtools checksum -m $s -o split.chksum
        diff in.chksum split.chksum
        

## AUTHOR

Written by James Bonfield from the Sanger Institute.   
Inspired by bamseqchksum, written by David Jackson of Sanger Institute and amended by German Tischler. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-view_](samtools-view.html) (1), 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-collate(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools collate – shuffles and groups reads together by their names 

## SYNOPSIS

samtools [collate](samtools-collate.html) [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_< prefix>_] 

## DESCRIPTION

Shuffles and groups reads together by their names. A faster alternative to a full query name sort, **collate** ensures that reads of the same name are grouped together in contiguous groups, but doesn't make any guarantees about the order of read names between groups. 

The output from this command should be suitable for any operation that requires all reads from the same template to be grouped together. 

Temporary files are written to <prefix>, specified either as the last argument or with the **-T** option. If prefix is unspecified then one will be derived from the output filename (**–o** option). If no output file was given then the **TMPDIR** environment variable will be used, and finally if that is unset then "/tmp" is used. 

Conversely, if prefix is specified but no output filename has been given then the output will be written to <prefix>.<fmt> where <fmt> is appropriate to the file format is use (e.g. "bam" or "cram"). 

Using **-f** for fast mode will output **only** primary alignments that have either the READ1 **or** READ2 flags set (but not both). Any other alignment records will be filtered out. The collation will only work correctly if there are no more than two reads for any given QNAME after filtering. 

Fast mode keeps a buffer of alignments in memory so that it can write out most pairs as soon as they are found instead of storing them in temporary files. This allows collate to avoid some work and so finish more quickly compared to the standard mode. The number of alignments held can be changed using **-r** , storing more alignments uses more memory but increases the number of pairs that can be written early. 

While collate normally randomises the ordering of read pairs, fast mode does not. Position-dependent biases that would normally be broken up can remain in the fast collate output. It is therefore not a good idea to use fast mode when preparing data for programs that expect randomly ordered paired reads. For example using fast collate instead of the standard mode may lead to significantly different results from aligners that estimate library insert sizes on batches of reads. 

## OPTIONS

**-O**
    

Output to stdout. This option cannot be used with **-o**. 

**-o** _FILE_
    

Write output to FILE. This option cannot be used with **-O**. If unspecified and **-O** is not set, the temporary file <prefix> is used, appended by the the appropriate file-format suffix. 

**-T** _PREFIX_
    

Use _PREFIX_ for temporary files. This is the same as specifying _PREFIX_ as the last argument on the command line. This option is included for consistency with **samtools sort**. 

**-u**
    

Write uncompressed BAM output 

**-l** _INT_
    

Compression level. [1] 

**-n** _INT_
    

Number of temporary files to use. [64] 

**-f**
    

Fast mode (primary alignments only). 

**-r** _INT_
    

Number of reads to store in memory (for use with -f). [10000] 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## AUTHOR

Written by Heng Li from the Sanger Institute and extended by Andrew Whitwham. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-sort_](samtools-sort.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-consensus(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools consensus – produces a consensus FASTA/FASTQ/PILEUP 

## SYNOPSIS

samtools [consensus](samtools-consensus.html) [**-saAMq**] [**-r** _region_] [**-f** _format_] [**-l** _line-len_] [**-d** _min-depth_] [**-C** _cutoff_] [**-c** _call-fract_] [**-H** _het-fract_] _in.bam_

## DESCRIPTION

Generate consensus from a SAM, BAM or CRAM file based on the contents of the alignment records. The consensus is written either as FASTA, FASTQ, or a pileup oriented format. This is selected using the **-f** _FORMAT_ option. 

The default output for FASTA and FASTQ formats include one base per non-gap consensus. Hence insertions with respect to the aligned reference will be included and deletions removed. This behaviour can be controlled with the **\--show-ins** and **\--show-del** options. This could be used to compute a new reference from sequences assemblies to realign against. 

The pileup-style format strictly adheres to one row per consensus location, differing from the one row per reference based used in the related "samtools mpileup" command. This means the base quality values for inserted columns are reported. The base quality value of gaps (either within an insertion or otherwise) are determined as the average of the surrounding non-gap bases. The columns shown are the reference name, position, nth base at that position (zero if not an insertion), consensus call, consensus confidence, sequences and quality values. Note even when a reference is supplied, the consensus base is always report (if non-zero depth) in the 5th column. 

Two consensus calling algorithms are offered. The default computes a heterozygous consensus in a Bayesian manner, derived from the "Gap5" consensus algorithm. Quality values are also tweaked to take into account other nearby low quality values. This can also be disabled, using the **\--no-adj-qual** option. 

This method also utilises the mapping qualities, unless the **\--no-use-MQ** option is used. Mapping qualities are also auto-scaled to take into account the local reference variation by processing the MD:Z tag, unless **\--no-adj-MQ** is used. Mapping qualities can be capped between a minimum (**\--low-MQ**) and maximum (**\--high-MQ**), although the defaults are liberal and trust the data to be true. Finally an overall scale on the resulting mapping quality can be supplied (**\--scale-MQ** , defaulting to 1.0). This has the effect of favouring more calls with a higher false positive rate (values greater than 1.0) or being more cautious with higher false negative rates and lower false positive (values less than 1.0). 

The second method is a simple frequency counting algorithm, summing either +1 for each base type or +_qual_ if the **\--use-qual** option is specified. This is enabled with the **\--mode simple** option. 

The summed share of a specific base type is then compared against the total possible and if this is above the **\--call-fract** _fraction_ parameter then the most likely base type is called, or "N" otherwise (or absent if it is a gap). The **\--ambig** option permits generation of ambiguity codes instead of "N", provided the minimum fraction of the second most common base type to the most common is above the **\--het-fract** _fraction_**.**

## OPTIONS

General options that apply to both algorithms: 

**-r** _REG_**, --region** _REG_
    

Limit the query to region _REG_. This requires an index. 

**-f** _FMT_**, --format** _FMT_
    

Produce format _FMT_ , with "fastq", "fasta" and "pileup" as permitted options. 

**-l** _N_**, --line-len** _N_
    

Sets the maximum line length of line-wrapped fasta and fastq formats to _N_. 

**-o** _FILE_**, --output** _FILE_
    

Output consensus to FILE instead of stdout. 

**-m** _STR_**, --mode** _STR_
    

Select the consensus algorithm. Valid modes are "simple" frequency counting and the "bayesian" (Gap5) methods, with Bayesian being the default. (Note case does not matter, so "Bayesian" is accepted too.) There are a variety of bayesian methods. Straight "bayesian" is the best set suitable for the other parameters selected. The choice of internal parameters may change depending on the "--P-indel" score. This method distinguishes between substitution and indel error rates. The old Samtools consensus in version 1.16 did not distinguish types of errors, but for compatibility the "bayesian_116" mode may be selected to replicate this. 

**-a**
    

Outputs all bases, from start to end of reference, even when the aligned data does not extend to the ends. This is most useful for construction of a full length reference sequence. 

**-a -a, -aa**
    

Output absolutely all positions, including references with no data aligned against them. 

**\--rf** , **\--incl-flags** _STR_ |_INT_
    

Only include reads with at least one FLAG bit set. Defaults to zero, which filters no reads. 

**\--ff** , **\--excl-flags** _STR_ |_INT_
    

Exclude reads with any FLAG bit set. Defaults to "UNMAP,SECONDARY,QCFAIL,DUP". 

**\--min-MQ** _INT_
    

Filters out reads with a mapping quality below _INT_. This defaults to zero. 

**\--min-BQ** _INT_
    

Filters out bases with a base quality below _INT_. This defaults to zero. 

**\--show-del** _yes_**/**_no_
    

Whether to show deletions as "*" (yes) or to omit from the output (no). Defaults to no. 

**\--show-ins** _yes_**/**_no_
    

Whether to show insertions in the consensus. Defaults to yes. 

**\--mark-ins**
    

Insertions, when shown, are normally recorded in the consensus with plain 7-bit ASCII (ACGT, or acgt if heterozygous). However this makes it impossible to identify the mapping between consensus coordinates and the original reference coordinates. If fasta output is selected then the option adds an underscore before every inserted base, plus a corresponding character in the quality for fastq format. When used in conjunction with **-a --show-del yes** , this permits an easy derivation of the consensus to reference coordinate mapping. 

**-A** , **\--ambig**
    

Enables IUPAC ambiguity codes in the consensus output. Without this the output will be limited to A, C, G, T, N and *. 

**-d** _D_**, --min-depth** _D_
    

The minimum depth required to make a call. Defaults to 1. Failing this depth check will produce consensus "N", or absent if it is an insertion. Note this check is performed after filtering by flags and mapping/base quality. 

**-T** _ref.fa_**, --reference** _ref.fa_
    

For base positions with zero coverage, use the supplied reference instead of "N". Note this does not replace minimum depth or minimum quality filters as the base is known but considiered low quality so the ambiguity is retained. 

**\--ref-qual** _INT_
    

When **\--reference** is given this specifies the quality value to use for reference-derived bases. This defaults to zero. 

The following options apply only to the simple consensus mode:
    

**-q** , **\--use-qual**
    

For the simple consensus algorithm, this enables use of base quality values. Instead of summing 1 per base called, it sums the base quality instead. These sums are also used in the **\--call-fract** and **\--het-fract** parameters too. Quality values are always used for the "Gap5" consensus method and this option has no effect. Note currently quality values only affect SNPs and not inserted sequences, which still get scores with a fixed +1 per base type occurrence. 

**-H** _H_**, --het-fract** _H_
    

For consensus columns containing multiple base types, if the second most frequent type is at least _H_ fraction of the most common type then a heterozygous base type will be reported in the consensus. Otherwise the most common base is used, provided it meets the _\--call-fract_ parameter (otherwise "N"). The fractions computed may be modified by the use of quality values if the **-q** option is enabled. Note although IUPAC has ambiguity codes for A,C,G,T vs any other A,C,G,T it does not have codes for A,C,G,T vs gap (such as in a heterozygous deletion). Given the lack of any official code, we use lower-case letter to symbolise a half-present base type. 

**-c** _C_**, --call-fract** _C_
    

Only used for the simple consensus algorithm. Require at least _C_ fraction of bases agreeing with the most likely consensus call to emit that base type. This defaults to 0.75. Failing this check will output "N". 

**-@**_NTHREADS_
    

Specify the number of additional threads to use for computing the consensus. Note if no index is present threads will only be used for parallel decompression meaning asking for more than 2 threads is unlikely to speed up processing. With an index the consensus is computed for multiple regions simultaneously, offering near linear speed ups. 

**-Z** _BASE_COUNT_
    

When using multiple threads this specifies the number of bases per threading job. The default is 500,000 bp for fasta/fastq output and 100,000 for pileup output. Larger blocks may yield improved threading performance at a cost of more memory. 

The following options apply only to Bayesian consensus mode enabled
    

(default on). 

**-C** _C_**, --cutoff** _C_
    

Only used for the Gap5 consensus mode, which produces a Phred style score for the final consensus quality. If this is below _C_ then the consensus is called as "N". 

**\--use-MQ** , **\--no-use-MQ**
    

Enable or disable the use of mapping qualities. Defaults to on. 

**\--adj-MQ** , **\--no-adj-MQ**
    

If mapping qualities are used, this controls whether they are scaled by the local number of mismatches to the reference. The reference is unknown by this tool, so this data is obtained from the MD:Z auxiliary tag (or ignored if not present). Defaults to on. 

**\--NM-halo** _INT_
    

Specifies the distance either side of the base call being considered for computing the number of local mismatches. 

**\--low-MQ** _MIN_ , **\--high-MQ** _MAX_
    

Specifies a minimum and maximum value of the mapping quality. These are not filters and instead simply put upper and lower caps on the values. The defaults are 0 and 60. 

**\--scale-MQ** _FLOAT_
    

This is a general multiplicative mapping quality scaling factor. The effect is to globally raise or lower the quality values used in the consensus algorithm. Defaults to 1.0, which leaves the values unchanged. 

**\--P-het** _FLOAT_
    

Controls the likelihood of any position being a heterozygous site. This is used in the priors for the Bayesian calculations, and has little difference on deep data. Defaults to 1e-3. Smaller numbers makes the algorithm more likely to call a pure base type. Note the algorithm will always compute the probability of the base being homozygous vs heterozygous, irrespective of whether the output is reported as ambiguous (it will be "N" if deemed to be heterozygous without **\--ambig** mode enabled). 

**\--P-indel** _FLOAT_
    

Controls the likelihood of small indels. This is used in the priors for the Bayesian calculations, and has little difference on deep data. Defaults to 2e-4. 

**\--het-scale** _FLOAT_
    

This is a multiplicative correction applied per base quality before adding to the heterozygous hypotheses. Reducing it means fewer heterozygous calls are made. This oftens leads a significant reduction in false positive het calls, for some increase in false negatives (mislabelling real heterozygous sites as homozygous). It is usually beneficial to reduce this on instruments where a significant proportion of bases may be aligned in the wrong column due to insertions and deletions leading to alignment errors and reference bias. It can be considered as a het sensitivity tuning parameter. Defaults to 1.0 (nop). 

**-p** , **\--homopoly-fix**
    

Some technologies that call runs of the same base type together always put the lowest quality calls at one end. This can cause problems when reverse complementing and comparing alignments with indels. This option averages the qualities at both ends to avoid orientation biases. Recommended for old 454 or PacBio HiFi data sets. 

**\--homopoly-score** _FLOAT_
    

The **-p** option also reduces confidence values within homopolymers due to an additional likelihood of sequence specific errors. The quality values are multiplied by _FLOAT_. This defaults to 0.5, but is not used if **-p** was not specified. Adjusting this score also automatically enables **-p**. 

**-t** , **\--qual-calibration** _FILE_
    

Loads a quality calibration table from _FILE_. The format of this is a series of lines with the following fields, each starting with the literal text "QUAL": 

**QUAL** _value_ _substitution_ _undercall_ _overcall_

Lines starting with a "#" are ignored. Each line maps a recorded quality value to the Phred equivalent score for substitution, undercall and overcall errors. Quality _value_ s are expected to be sorted in increasing numerical order, but may skip values. This allows the consensus algorithm to know the most likely cause of an error, and whether the instrument is more likely to have indel errors (more common in some long read technologies) or substitution errors (more common in clocked short-read instruments). 

Some pre-defined calibration tables are built in. These are specified with a fake filename starting with a colon. See the **-X** option for more details. 

Note due to the additional heuristics applied by the consensus algorithm, these recalibration tables are not a true reflection of the instrument error rates and are a work in progress. 

**-X** , **\--config** _STR_
    

Specifies predefined sets of configuration parameters. Acceptable values for _STR_ are defined below, along with the list of parameters they are equivalent to. 

**hiseq**
    

\--qual-calibration :hiseq 

**hifi**
    

\--qual-calibration :hifi \--homopoly-fix 0.3 --low-MQ 5 --scale-MQ 1.5 --het-scale 0.37 

**r10.4_sup**
    

\--qual-calibration :r10.4_sup \--homopoly-fix 0.3 --low-MQ 5 --scale-MQ 1.5 --het-scale 0.37 

**r10.4_dup**
    

\--qual-calibration :r10.4_dup \--homopoly-fix 0.3 --low-MQ 5 --scale-MQ 1.5 --het-scale 0.37 

**ultima**
    

\--qual-calibration :ultima \--homopoly-fix 0.3 --low-MQ 10 --scale-MQ 2 --het-scale 0.37 

## EXAMPLES

Create a modified FASTA reference that has a 1:1 coordinate correspondence with the original reference used in alignment. 
    
    
    samtools consensus -a --show-ins no --show-del yes in.bam -o ref.fa
    

Create a FASTQ file for the contigs with aligned data, including insertions. 
    
    
    samtools consensus -f fastq in.bam -o cons.fq
    

## AUTHOR

Written by James Bonfield from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-mpileup_](samtools-mpileup.html) (1), 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-coverage(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools coverage – produces a histogram or table of coverage per chromosome 

## SYNOPSIS

samtools [coverage](samtools-coverage.html) [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

## DESCRIPTION

Computes the coverage at each position or region and draws an ASCII-art histogram or tabulated text. 

Coverage is defined as the percentage of positions within each bin with at least one base aligned against it. 

The tabulated form uses the following headings. 

**rname**|  Reference name / chromosome  
---|---  
**startpos**|  Start position  
**endpos**|  End position (or sequence length)  
**numreads**|  Number reads aligned to the region (after filtering)  
**covbases**|  Number of covered bases with depth >= 1  
**coverage**|  Percentage of covered bases [0..100]  
**meandepth**|  Mean depth of coverage  
**meanbaseq**|  Mean baseQ in covered region  
**meanmapq**|  Mean mapQ of selected reads  
  
## OPTIONS

Input options: 

**-b, --bam-list** _FILE_
    

List of input BAM files, one file per line [null] 

**-l, --min-read-len** _INT_
    

Ignore reads shorter than _INT_ base pairs [0] 

**-q, --min-MQ** _INT_
    

Minimum mapping quality for an alignment to be used [0] 

**-Q, --min-BQ** _INT_
    

Minimum base quality for a base to be considered [0] 

**\--rf, --incl-flags** _STR|INT_
    

Required flags: skip reads with mask bits unset [null] 

**\--ff, --excl-flags** _STR|INT_
    

Filter flags: skip reads with mask bits set [UNMAP,SECONDARY,QCFAIL,DUP] 

**-d, --depth** _INT_
    

Maximum allowed coverage depth [1000000]. If 0, depth is set to the maximum integer value effectively removing any depth limit. 

**\--min-depth** _INT_
    

Minimum coverage depth, below which a position is ignored [1] 

Output options: 

**-m, --histogram**
    

Show histogram instead of tabular output. 

**-D, --plot-depth**
    

As above but displays the depth of coverage instead of the percent of coverage. This option can be used to visualize copy number variations in the terminal. 

**-A, --ascii**
    

Show only ASCII characters in histogram using colon and fullstop for full and half height characters. 

**-o, --output** _FILE_
    

Write output to FILE [stdout]. 

**-H, --no-header**
    

Don't print a header in tabular mode. 

**-w, --n-bins** _INT_
    

Number of bins in histogram. [terminal width - 40] 

**-r, --region** _REG_
    

Show specified region. Format: chr:start-end. 

**-h, --help**
    

Shows command help. 

## EXAMPLES

Running coverage in tabular mode, on a specific region, with tabs shown as spaces for clarity in this man page. 
    
    
    samtools coverage -r chr1:1M-12M input.bam
    
    
    
    #rname  startpos  endpos    numreads  covbases  coverage  meandepth  meanbaseq  meanmapq
    chr1    1000000   12000000  528695    1069995   9.72723   3.50281    34.4       55.8
    

An example of the histogram output is below, with ASCII block characters replaced by "#" for rendering in this man page. 
    
    
    samtools coverage -A -w 32 -r chr1:1M-12M input.bam
    
    
    
    chr1 (249.25Mbp)
    >  24.19% | .                              | Number of reads: 528695
    >  21.50% |::                              |     (132000 filtered)
    >  18.81% |::                              | Covered bases:   1.07Mbp
    >  16.12% |::                           :  | Percent covered: 9.727%
    >  13.44% |::  :  .       ::            : :| Mean coverage:   3.5x
    >  10.75% |:: ::  :       ::          : : :| Mean baseQ:      34.4
    >   8.06% |:::::  :       ::        : : : :| Mean mapQ:       55.8
    >   5.37% |::::: ::      :::      : ::::: :| 
    >   2.69% |::::: :::     :::  ::: :::::::::| Histo bin width: 343.8Kbp
    >   0.00% |:::::::::::. :::::::::::::::::::| Histo max bin:   26.873%
            1.00M     4.44M     7.87M       12.00M 
    
    
    
    samtools coverage  -m -r 'chr1:24500000-25600000' --plot-depth -w 32 -A input.bam
    
    
    
    chr1 (249.25Mbp)
    >    38.8 |            .:::::::            | Number of reads: 283218
    >    34.5 |            ::::::::            |     (3327 filtered)
    >    30.2 |           :::::::::.           | Covered bases:   1.10Mbp
    >    25.9 |.:::::.:.::::::::::::::::::::::.| Percent covered: 99.83%
    >    21.6 |::::::::::::::::::::::::::::::::| Mean coverage:   33.2x
    >    17.2 |::::::::::::::::::::::::::::::::| Mean baseQ:      37.2
    >    12.9 |::::::::::::::::::::::::::::::::| Mean mapQ:       59.3
    >     8.6 |::::::::::::::::::::::::::::::::|
    >     4.3 |::::::::::::::::::::::::::::::::| Histo bin width: 34.5Kbp
    >     0.0 |::::::::::::::::::::::::::::::::| Histo max cov:   43.117
            24.50M    24.84M    25.19M      25.60M
    
    
    
    

## AUTHOR

Written by Florian P Breitwieser. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-depth_](samtools-depth.html) (1), 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-cram-size(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools cram-size – list a break down of data types in a CRAM file 

## SYNOPSIS

samtools [cram-size](samtools-cram-size.html) [**-ve**] [**-o** _file_] _in.bam_

## DESCRIPTION

Produces a summary of CRAM block Content ID numbers and their associated Data Series stored within them. Optionally a more detailed breakdown of how each data series is encoded per container may also be listed using the **-e** or **\--encodings** option. 

CRAM permits mixing multiple Data Series into a single block. In this case it is not possible to tell the relative proportion that the Data Series consume within that block. CRAM also permits different encodings and block Content ID assignment per container, although this would be highly unusual. Htslib will always assign the same Data Series to a block with a consistent Content ID, although the CRAM Encoding may change. 

Each CRAM block has a compression method. These may not be consistent between successive blocks with the same Content ID. Htslib learns which compression methods work, so a single Content ID may have multiple compression methods associated with it. The methods utilised are listed per line with a single character code, although the size breakdown per method and a more verbose description can be shown using the **-v** option. The compression codecs used in CRAM may have a variety of parameters, such as compression levels, inbuilt transformations, and choices of entropy encoding. An attempt is made to distinguish between these different method parameterisations. 

The compression methods and their short and long (verbose) name are below: 

Short| Long| Description  
---|---|---  
_  
g| gzip| Gzip  
_| gzip-min| Gzip -1  
G| gzip-max| Gzip -9  
b| bzip2| Bzip2  
b| bzip2-1 to bzip2-8| Explicit bzip2 compression levels  
B| bzip2-9| Bzip2 -9  
l| lzma| LZMA  
r| r4x8-o0| rANS 4x8 Order-0  
R| r4x8-o1| rANS 4x8 Order-1  
0| r4x16-o0| rANS 4x16 Order-0  
0| r4x16-o0R| rANS 4x16 Order-0 with RLE  
0| r4x16-o0P| rANS 4x16 Order-0 with PACK  
0| r4x16-o0PR| rANS 4x16 Order-0 with PACK and RLE  
1| r4x16-o1| rANS 4x16 Order-1  
1| r4x16-o1R| rANS 4x16 Order-1 with RLE  
1| r4x16-o1P| rANS 4x16 Order-1 with PACK  
1| r4x16-o1PR| rANS 4x16 Order-1 with PACK and RLE  
4| r32x16-o0| rANS 32x16 Order-0  
4| r32x16-o0R| rANS 32x16 Order-0 with RLE  
4| r32x16-o0P| rANS 32x16 Order-0 with PACK  
4| r32x16-o0PR| rANS 32x16 Order-0 with PACK and RLE  
5| r32x16-o1| rANS 32x16 Order-1  
5| r32x16-o1R| rANS 32x16 Order-1 with RLE  
5| r32x16-o1P| rANS 32x16 Order-1 with PACK  
5| r32x16-o1PR| rANS 32x16 Order-1 with PACK and RLE  
8| rNx16-xo0| rANS Nx16 STRIPED mode  
2| rNx16-cat| rANS Nx16 CAT mode  
a| arith-o0| Arithmetic coding Order-0  
a| arith-o0R| Arithmetic coding Order-0 with RLE  
a| arith-o0P| Arithmetic coding Order-0 with PACK  
a| arith-o0PR| Arithmetic coding Order-0 with PACK and RLE  
A| arith-o1| Arithmetic coding Order-1  
A| arith-o1R| Arithmetic coding Order-1 with RLE  
A| arith-o1P| Arithmetic coding Order-1 with PACK  
A| arith-o1PR| Arithmetic coding Order-1 with PACK and RLE  
a| arith-xo0| Arithmetic coding STRIPED mode  
a| arith-cat| Arithmetic coding CAT mode  
f| fqzcomp| FQZComp quality codec  
n| tok3-rans| Name tokeniser with rANS encoding  
n| tok3-arith| Name tokeniser with Arithmetic encoding  
  
## OPTIONS

**-o** _FILE_
    

Output size information to _FILE_. 

**-v**
    

Verbose mode. This shows one line per combination of Content ID and compression method. 

**-e, --encodings**
    

CRAM uses an Encoding, which describes how the data is serialised into a data block. This is distinct from the CRAM compression method, which is then applied to the block post-encoding. The encoding methods are stored per CRAM Container. 

This option list CRAM record encoding map and tag encoding map. This shows the data series, the associated CRAM encoding method, such as HUFFMAN, BETA or EXTERNAL, and any parameters associated with that encoding. The output may be large as this is information per container rather than a single set of summary statistics at the end of processing. 

## EXAMPLES

The basic summary of block Content ID sizes for a CRAM file: 
    
    
    $ samtools cram-size in.cram
    #   Content_ID  Uncomp.size    Comp.size   Ratio Method  Data_series
    BLOCK     CORE            0            0 100.00% .      
    BLOCK       11    394734019     51023626  12.93% g       RN
    BLOCK       12   1504781763     99158495   6.59% R       QS
    BLOCK       13       330065        84195  25.51% _r.g    IN
    BLOCK       14     26625602      6803930  25.55% Rrg     SC
    ...
    

Show the same file above with verbose mode. Here we see the distinct compression methods which have been used per block Content ID. 
    
    
    $ samtools cram-size -v in.cram
    #   Content_ID  Uncomp.size    Comp.size   Ratio Method      Data_series
    BLOCK     CORE            0            0 100.00% raw        
    BLOCK       11    394734019     51023626  12.93% gzip        RN
    BLOCK       12   1504781763     99158495   6.59% r4x8-o1     QS
    BLOCK       13       275033        64343  23.39% gzip-min    IN
    BLOCK       13        43327        15412  35.57% r4x8-o0     IN
    BLOCK       13         2452         2452 100.00% raw         IN
    BLOCK       13         9253         1988  21.49% gzip        IN
    BLOCK       14     23106404      5903351  25.55% r4x8-o1     SC
    BLOCK       14      1951616       513722  26.32% r4x8-o0     SC
    BLOCK       14      1567582       386857  24.68% gzip        SC
    ...
    

List encoding methods per CRAM Data Series. The two letter series are the standard CRAM Data Series and the three letter ones are the optional auxiliary tags with the tag name and type combined. 
    
    
    $ samtools cram-size -e in.cram
    Container encodings
        RN      BYTE_ARRAY_STOP(stop=0,id=11)
        QS      EXTERNAL(id=12)
        IN      BYTE_ARRAY_STOP(stop=0,id=13)
        SC      BYTE_ARRAY_STOP(stop=0,id=14)
        BB      BYTE_ARRAY_LEN(len_codec={EXTERNAL(id=42)}, \
                               val_codec={EXTERNAL(id=37)}
        ...
        XAZ     BYTE_ARRAY_STOP(stop=9,id=5783898)
        MDZ     BYTE_ARRAY_STOP(stop=9,id=5063770)
        ASC     BYTE_ARRAY_LEN(len_codec={HUFFMAN(codes={1},lengths={0})}, \
                               val_codec={EXTERNAL(id=4281155)}
        ...
    

## AUTHOR

Written by James Bonfield from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-depad(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools depad – convert padded BAM to unpadded BAM 

## SYNOPSIS

samtools [depad](samtools-depad.html) [**-SsCu1**] [**-T** _ref.fa_] [**-o** _output_] _in.bam_

## DESCRIPTION

Converts a BAM aligned against a padded reference to a BAM aligned against the depadded reference. The padded reference may contain verbatim "*" bases in it, but "*" bases are also counted in the reference numbering. This means that a sequence base-call aligned against a reference "*" is considered to be a cigar match ("M" or "X") operator (if the base-call is "A", "C", "G" or "T"). After depadding the reference "*" bases are deleted and such aligned sequence base-calls become insertions. Similarly transformations apply for deletions and padding cigar operations. 

## OPTIONS

**-S**
    

Ignored for compatibility with previous samtools versions. Previously this option was required if input was in SAM format, but now the correct format is automatically detected by examining the first few characters of input. 

**-s**
    

Output in SAM format. The default is BAM. 

**-C**
    

Output in CRAM format. The default is BAM. 

**-u**
    

Do not compress the output. Applies to either BAM or CRAM output format. 

**-1**
    

Enable fastest compression level. Only works for BAM or CRAM output. 

**-T** _FILE_
    

Provides the padded reference file. Note that without this the @SQ line lengths will be incorrect, so for most use cases this option will be considered as mandatory. 

**-o** _FILE_
    

Specifies the output filename. By default output is sent to stdout. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

## AUTHOR

Written by Heng Li from the Sanger Institute with extensions by Peter Cock from the James Hutton Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-depth(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools depth – computes the read depth at each position or region 

## SYNOPSIS

samtools [depth](samtools-depth.html) [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

## DESCRIPTION

Computes the depth at each position or region. 

## OPTIONS

**-a**
    

Output all positions (including those with zero depth) 

**-a -a, -aa**
    

Output absolutely all positions, including unused reference sequences. Note that when used in conjunction with a BED file the -a option may sometimes operate as if -aa was specified if the reference sequence has coverage outside of the region specified in the BED file. 

**-b** _FILE_
    

Compute depth at list of positions or regions in specified BED _FILE._ [] 

**-f** _FILE_
    

Use the BAM files specified in the _FILE_ (a file of filenames, one file per line) [] 

**-H**
    

Write a comment line showing column names at the beginning of the output. The names are CHROM, POS, and then the input file name for each depth column. If one of the inputs came from stdin, the name “-” will be used for the corresponding column. 

**-l** _INT_
    

Ignore reads shorter than _INT_. This is the number of bases in the sequence, minus any soft clips. 

**-m, -d** _INT_
    

(Deprecated since 1.13) This option previously limited the depth to a maximum value. It is still accepted as an option, but ignored. 

Note for single files, the behaviour of old **samtools depth -J -q0 -d** _INT FILE_ is identical to **samtools mpileup -A -Q0 -x -d** _INT FILE_ **| cut -f 1,2,4**

**-o** _FILE_
    

Write output to _FILE_. Using “-” for _FILE_ will send the output to stdout (also the default if this option is not used). 

**-q, --min-BQ** _INT_
    

Only count reads with base quality greater than or equal to _INT_

**-Q, --min-MQ** _INT_
    

Only count reads with mapping quality greater than or equal to _INT_

**-r** _CHR_**:**_FROM_**-**_TO_
    

Only report depth in specified region. 

**-X**
    

If this option is set, it will allow the user to specify customized index file location(s) if the data folder does not contain any index file. Example usage: samtools depth [options] -X /data_folder/in1.bam [/data_folder/in2.bam [...]] /index_folder/index1.bai [/index_folder/index2.bai [...]] 

**-g** _FLAGS_
    

By default, reads that have any of the flags UNMAP, SECONDARY, QCFAIL, or DUP set are skipped. To include these reads back in the analysis, use this option together with the desired flag or flag combination. _FLAGS_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. [0] 

For a list of flag names see _samtools-flags_(1). 

**-G** _FLAGS_**, --excl-flags** _FLAGS_
    

Discard reads that have any of the flags specified by _FLAGS_ set. FLAGS are specified as for the **-g** option. [UNMAP,SECONDARY,QCFAIL,DUP] 

**\--incl-flags** _FLAGS_
    

Only include reads with at least one bit set in _FLAGS_ present in the FLAG field. FLAGS are specified as for the **-g** option. [0] 

**\--require-flags** _FLAGS_
    

Only include reads with all bits set in _FLAGS_ present in the FLAG field. FLAGS are specified as for the **-g** option. [0] 

**-J**
    

Include reads with deletions in depth computation. 

**-s**
    

For the overlapping section of a read pair, count only the bases of the first read. Note this algorithm changed in 1.13 so the results may differ slightly to older releases. 

## CAVEATS

It may appear that "samtools depth" is simply "samtools mpileup" with some of the columns removed, and indeed earlier versions of this command were just this. However both then and now there are subtle differences in parameters which make the two not entirely comparable. Differences, other than the obvious speed benefits, include: 

  * Deletions (CIGAR element "D") are ignored by default in "depth". These may be counted by adding the **-J** option. "Mpileup" always counts the deleted bases, and has no option to toggle this. 

  * Beware there are idiosyncrasies in option naming. Specifically **-q** and **-Q** options have their meanings swapped between "depth" and "mpileup". 

  * The removal of overlapping sequences (option **-s**) is on by default in "mpileup" and off by default in "depth". Additionally the overlap removal algorithm differs, giving subtle changes when Ns are present in the sequence. Also any paired read is considered for overlap removal by "depth", rather than only those with the properly-paired flag set ("mpileup"). See above for a more detailed description. 

  * The default minimum quality value is 0 for "depth" and 13 for "mpileup". 

  * Specifying multiple BAMs will produce one depth column per file with "depth", but these are merged in "mpileup". 

  * "Depth" doesn't have a maximum depth limit, while "mpileup" defaults to a maximum of 8000. 

  * If a reference is specified to "mpileup" the BAQ algorithm will be used to adjust quality values, although it can be disabled. "Depth" never uses BAQ. 

## AUTHOR

Written by Heng Li and James Bonfield from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-mpileup_](samtools-mpileup.html) (1), [_samtools-coverage_](samtools-coverage.html) (1), [_samtools-sort_](samtools-sort.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-dict(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools dict – create a sequence dictionary file from a fasta file 

## SYNOPSIS

samtools [dict](samtools-dict.html) _ref.fasta_ |_ref.fasta.gz_

## DESCRIPTION

Create a sequence dictionary file from a fasta file. 

## OPTIONS

**-a, --assembly** _STR_
    

Specify the assembly for the AS tag. 

**-A, --alias, --alternative-name**
    

Add an AN tag with the same value as the SN tag, except that a “chr” prefix is removed if SN has one or added if it does not. For mitochondria (i.e., when SN is “M” or “MT”, with or without a “chr” prefix), also adds the remaining combinations of “chr/M/MT” to the AN tag. 

**-H, --no-header**
    

Do not print the @HD header line. 

**-l, --alt** _FILE_
    

Add an AH tag to each sequence listed in the specified _bwa_(1)-style **.alt** file. These files use SAM records to represent alternate locus sequences (as named in the **QNAME** field) and their mappings to the primary assembly. 

**-o, --output** _FILE_
    

Output to _FILE_ [stdout]. 

**-s, --species** _STR_
    

Specify the species for the SP tag. 

**-u, --uri** _STR_
    

Specify the URI for the UR tag. Defaults to the absolute path of _ref.fasta_ unless reading from stdin. 

## AUTHOR

Written by Shane McCarthy from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_bcftools_](bcftools.html) (1), _bwa_(1), [_sam_](sam.html) (5), [_tabix_](tabix.html) (1) 

Samtools website: <<http://www.htslib.org/>>   
File format specification of SAM/BAM,CRAM,VCF/BCF: <<http://samtools.github.io/hts-specs>>   
Samtools latest source: <<https://github.com/samtools/samtools>>   
HTSlib latest source: <<https://github.com/samtools/htslib>>   
Bcftools website: <<http://samtools.github.io/bcftools>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-faidx(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools faidx – indexes or queries regions from a fasta file 

## SYNOPSIS

samtools [faidx](samtools-faidx.html) _ref.fasta_ [_region1_ [...]] 

## DESCRIPTION

Index reference sequence in the FASTA format or extract subsequence from indexed reference sequence. If no region is specified, **faidx** will index the file and create _< ref.fasta>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTA format. 

The input and output can be files compressed in the **BGZF** format. When output is compressed, the default compression level is 4. 

The sequences in the input file should all have different names. If they do not, indexing will emit a warning about duplicate sequences and retrieval will only produce subsequences from the first sequence with the duplicated name. 

FASTQ files can be read and indexed by this command. Without using **\--fastq** any extracted subsequence will be in FASTA format. 

## OPTIONS

**-o, --output** _FILE_
    

Write FASTA to file rather than to stdout. If _FILE_ ends with .gz, .bgz or .bgzf then it will be **BGZF** compressed. 

**-n, --length** _INT_
    

Length for FASTA sequence line wrapping. If zero, this means do not line wrap. Defaults to the line length in the input file. 

**-c, --continue**
    

Continue working if a non-existent region is requested. 

**-r, --region-file** _FILE_
    

Read regions from a file. Format is chr:from-to, one per line. 

**-f, --fastq**
    

Read FASTQ files and output extracted sequences in FASTQ format. Same as using samtools fqidx. 

**-i, --reverse-complement**
    

Output the sequence as the reverse complement. When this option is used, “/rc” will be appended to the sequence names. To turn this off or change the string appended, use the **\--mark-strand** option. 

**\--mark-strand TYPE**
    

Append strand indicator to sequence name. TYPE can be one of: 

**rc**
    

Append '/rc' when writing the reverse complement. This is the default. 

**no**
    

Do not append anything. 

**sign**
    

Append '(+)' for forward strand or '(-)' for reverse complement. This matches the output of “bedtools getfasta -s”. 

**custom, <pos>,<neg>**
    

Append string <pos> to names when writing the forward strand and <neg> when writing the reverse strand. Spaces are preserved, so it is possible to move the indicator into the comment part of the description line by including a leading space in the strings <pos> and <neg>. 

**\--fai-idx FILE**
    

Read/Write to specified index file. 

**\--gzi-idx FILE**
    

Read/Write to specified compressed file index (used with .gz files). 

**-h, --help**
    

Print help message and exit. 

**\--output-fmt-option** _OPT=VAL_
    

Set the output format options, level=0..9 for compression level 0 to 9. 

**\--write-index**
    

Create index for the output sequence data along with the output, in same path as <output name>.fai, <outputname>.gzi. This option is valid only for file output. 

**-@, --threads** _N_
    

Set the number of extra threads for operations on compressed files. 

## AUTHOR

Written by Heng Li, with modifications by Andrew Whitwham and Robert Davies, all from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-fasta_](samtools-fasta.html) (1), [_samtools-fqidx_](samtools-fqidx.html) (1), [_samtools-fastq_](samtools-fastq.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-fasta(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools-fasta, samtools-fastq – converts a SAM/BAM/CRAM file to FASTA or FASTQ 

## SYNOPSIS

samtools [fastq](samtools-fastq.html) [_options_] _in.bam_   
samtools [fasta](samtools-fasta.html) [_options_] _in.bam_

## DESCRIPTION

Converts a BAM or CRAM into either FASTQ or FASTA format depending on the command invoked. The files will be automatically compressed if the file names have a .gz, .bgz, or .bgzf extension. 

Note this command is attempting to reverse the alignment process, so if the aligner took a single input FASTQ and produced multiple SAM records via supplementary and/or secondary alignments, then converting back to FASTQ again should produce the original single FASTA / FASTQ record. By default it will not attend to records of supplementary and secondary alignments, but see the **-F** option for more details. 

If the input contains read-pairs which are to be interleaved or written to separate files in the same order, then the input should be first collated by name. Use **samtools collate** or **samtools sort -n** to ensure this. 

For each different QNAME, the input records are categorised according to the state of the READ1 and READ2 flag bits. The three categories used are: 

1 : Only READ1 is set. 

2 : Only READ2 is set. 

0 : Either both READ1 and READ2 are set; or neither is set. 

The exact meaning of these categories depends on the sequencing technology used. It is expected that ordinary single and paired-end sequencing reads will be in categories 1 and 2 (in the case of paired-end reads, one read of the pair will be in category 1, the other in category 2). Category 0 is essentially a “catch-all” for reads that do not fit into a simple paired-end sequencing model. 

For each category only one sequence will be written for a given QNAME. If more than one record is available for a given QNAME and category, the first in input file order that has quality values will be used. If none of the candidate records has quality values, then the first in input file order will be used instead. 

Sequences will be written to standard output unless one of the **-1** , **-2** , **-o** , or **-0** options is used, in which case sequences for that category will be written to the specified file. The same filename may be specified with multiple options, in which case the sequences will be multiplexed in order of occurrence. 

If a singleton file is specified using the **-s** option then only paired sequences will be output for categories 1 and 2; paired meaning that for a given QNAME there are sequences for both category 1 **and** 2\. If there is a sequence for only one of categories 1 or 2 then it will be diverted into the specified singletons file. This can be used to prepare fastq files for programs that cannot handle a mixture of paired and singleton reads. 

The **-s** option only affects category 1 and 2 records. The output for category 0 will be the same irrespective of the use of this option. 

The sequence generated will be for the entire sequence recorded in the SAM record (and quality if appropriate). This means if it has soft-clipped CIGAR records then the soft-clipped data will be in the output FASTA/FASTQ. Hard-clipped data is, by definition, absent from the SAM record and hence will be absent in any FASTA/FASTQ produced. 

The filter options order of precedence is -d/-D, -f, -F, --rf and -G. 

## OPTIONS

**-n**
    

By default, either '/1' or '/2' is added to the end of read names where the corresponding READ1 or READ2 FLAG bit is set. Using **-n** causes read names to be left as they are. 

**-N**
    

Always add either '/1' or '/2' to the end of read names even when put into different files. 

**-O**
    

Use quality values from OQ tags in preference to standard quality string if available. (FASTQ only) 

**-v** _INT_
    

Specifies a default quality score to use for sequences that have no quality. Defaults to 1. (FASTQ only) 

**-s** _FILE_
    

Write singleton reads to _FILE_. 

**-t**
    

Copy RG, BC and QT tags to the FASTQ header line, if they exist. 

**-T** _TAGLIST_
    

Specify a comma-separated list of tags to copy to the FASTQ header line, if they exist. _TAGLIST_ can be blank or ***** to indicate all tags should be copied to the output. If using ***** , be careful to quote it to avoid unwanted shell expansion. 

**-1** _FILE_
    

Write reads with the READ1 FLAG set (and READ2 not set) to _FILE_ instead of outputting them. If the **-s** option is used, only paired reads will be written to this file. 

**-2** _FILE_
    

Write reads with the READ2 FLAG set (and READ1 not set) to _FILE_ instead of outputting them. If the **-s** option is used, only paired reads will be written to this file. 

**-o** _FILE_
    

Write reads with either READ1 FLAG or READ2 flag set to _FILE_ instead of outputting them to stdout. This is equivalent to **-1** _FILE_ **-2** _FILE_. 

**-0** _FILE_
    

Write reads where the READ1 and READ2 FLAG bits set are either both set or both unset to _FILE_ instead of outputting them. 

**-c** _[0..9]_
    

set compression level when writing gz or bgzf fastq files. 

**-f** _INT_
    

Only output alignments with all bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0]. 

**-F** _INT_**, --excl-flags** _INT_**, --exclude-flags** _INT_
    

Do not output alignments with any bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0x900]. This defaults to 0x900 representing filtering of secondary and supplementary alignments. 

**\--rf** _INT_**, --incl-flags** _INT_**, --include-flags** _INT_
    

Only output alignments with any bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names [0]. 

**-G** _INT_
    

Only EXCLUDE reads with all of the bits set in _INT_ present in the FLAG field. _INT_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/) or in octal by beginning with `0' (i.e. /^0[0-7]+/) [0]. 

**-d** _TAG_**[:**_VAL_**]**
    

Only output alignments containing an auxiliary tag matching both _TAG_ and _VAL_. If _VAL_ is omitted then any value is accepted. The tag types supported are i, f, Z, A and H. "B" arrays are not supported. This is comparable to the method used in **samtools view -d**. The option may be specified multiple times and is equivalent to using the **-D** option. 

**-D** _TAG:FILE_
    

Only output alignments containing an auxiliary tag matching _TAG_ and having a value listed in _FILE_. The format of the file is one line per value. This is equivalent to specifying **-d** multiple times. 

**-i**
    

add Illumina Casava 1.8 format entry to header (eg 1:N:0:ATCACG) 

**-U, --UMI**
    

Add UMI sequence to the end of read names, if found in the UMI tag list. Non alphabetical characters are converted to the `+' symbol. 

**\--UMI-tag** _TAGLIST_
    

Specifies which aux tags to search for UMI sequence as a comma-separated list. The first tag found is used. The default is `OX,RX'. 

**\--i1** _FILE_
    

write first index reads to _FILE_

**\--i2 FILE**
    

write second index reads to _FILE_

**\--barcode-tag** _TAG_
    

aux tag to find index reads in [default: BC] 

**\--quality-tag** _TAG_
    

aux tag to find index quality in [default: QT]. (FASTQ only) 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

**\--index-format** _STR_
    

string to describe how to parse the barcode and quality tags. For example: 

**i14i8**
    

the first 14 characters are index 1, the next 8 characters are index 2 

**n8i14**
    

ignore the first 8 characters, and use the next 14 characters for index 1 

If the tag contains a separator, then the numeric part can be replaced with '*' to mean 'read until the separator or end of tag', for example: 

**n*i***
    

ignore the left part of the tag until the separator, then use the second part 

**\--no-sc**
    

Remove data corresponding to soft-clips from cigar, bases and quality values of filtered output. The removed data are added as an aux tag, 'Z' type array, with tag 's0', when **\--no-sc-bkp** is absent. The array will contain data in the order of cigar before the removal, bases removed and quality values removed, separated by ':'. With reversed reads, the cigar, bases and quality values are reversed; bases are flipped as well. 

**\--sc-aux** _TAG_
    

Tag with which to backup the removed soft-clip data, default is 's0'. 

**\--no-sc-bkp**
    

Avoids backup of data removed as part of soft-clip removal, **\--no-sc** option. 

## EXAMPLES

Starting from a coordinate sorted file, output paired reads to separate files, discarding singletons, supplementary and secondary reads. The resulting files can be used with, for example, the **bwa** aligner. 
    
    
    samtools collate -u -O in_pos.bam | \
    samtools fastq -1 paired1.fq -2 paired2.fq -0 /dev/null -s /dev/null -n
    

Starting with a name collated file, output paired and singleton reads in a single file, discarding supplementary and secondary reads. To get all of the reads in a single file, it is necessary to redirect the output of samtools fastq. The output file is suitable for use with **bwa mem -p** which understands interleaved files containing a mixture of paired and singleton reads. 
    
    
    samtools fastq -0 /dev/null in_name.bam > all_reads.fq
    

Output paired reads in a single file, discarding supplementary and secondary reads. Save any singletons in a separate file. Append /1 and /2 to read names. This format is suitable for use by **NextGenMap** when using its **-p** and **-q** options. With this aligner, paired reads must be mapped separately to the singletons. 
    
    
    samtools fastq -0 /dev/null -s single.fq -N in_name.bam > paired.fq
    

## BUGS

  * The way of specifying output files is far too complicated and easy to get wrong. 

## AUTHOR

Written by Heng Li, with modifications by Martin Pollard and Jennifer Liddle, all from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-faidx_](samtools-faidx.html) (1), [_samtools-fqidx_](samtools-fqidx.html) (1) [_samtools-import_](samtools-import.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: Redirecting…

## Redirecting…

Please click [here](samtools-fasta.html) if not redirected automatically. 

# 工具文档: samtools-fixmate(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools fixmate – fills in mate coordinates and insert size fields. 

## SYNOPSIS

samtools [fixmate](samtools-fixmate.html) [**-rpcmu**] [**-O** _format_] _in.nameSrt.bam out.bam_

## DESCRIPTION

Fill in mate coordinates, ISIZE and mate related flags from a name-sorted or name-collated alignment. 

## OPTIONS

**-r**
    

Remove secondary and unmapped reads. If one of a pair is removed, the PAIRED flag will not be unset on the remaining read. This is a change from the older behaviour in samtools versions up to 1.20. 

**-p**
    

Disable FR proper pair check. 

**-c**
    

Add template cigar ct tag. 

**-m**
    

Add ms (mate score) tags. These are used by **markdup** to select the best reads to keep. 

**-M**
    

Fix any base modification tags (MM, ML and MN). If we have secondary alignments with hard-clipping and the hard clipped reads do not have an MN tag then we use the base modification tags in the primary alignment to clip the secondary alignment modifications, adding MN tags in the process. 

This also does other sanity checks on the consistency of these tags. 

**-u**
    

Output uncompressed BAM or CRAM. 

**-O** _FORMAT_
    

Write the final output as **sam** , **bam** , or **cram**. 

By default, samtools tries to select a format based on the output filename extension; if output is to standard output or no format can be deduced, **bam** is selected. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

**-z** _FLAGs_**, --sanitize** _FLAGs_
    

Perform basic sanitizing of records. _FLAGs_ is a comma-separated list of keywords, defined in the _samtools-view_(1) man page. By default all FLAGs are enabled. Use **-z off** to disable this. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-markdup_](samtools-markdup.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_samtools-collate_](samtools-collate.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-flags(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools flags – convert between textual and numeric flag representation. 

## SYNOPSIS

samtools [flags](samtools-flags.html) _FLAGS_... 

## DESCRIPTION

Convert between textual and numeric flag representation. 

Each _FLAGS_ argument may be either an integer (in decimal, hexadecimal, or octal) representing a combination of the listed numeric flag values, or a comma-separated string _NAME_**,**...**,**_NAME_ representing a combination of the flag names listed below. 

**FLAGS:** **0x1**|  PAIRED| paired-end (or multiple-segment) sequencing technology  
---|---|---  
**0x2**|  PROPER_PAIR| each segment properly aligned according to the aligner  
**0x4**|  UNMAP| segment unmapped  
**0x8**|  MUNMAP| next segment in the template unmapped  
**0x10**|  REVERSE| SEQ is reverse complemented  
**0x20**|  MREVERSE| SEQ of the next segment in the template is reverse complemented  
**0x40**|  READ1| the first segment in the template  
**0x80**|  READ2| the last segment in the template  
**0x100**|  SECONDARY| secondary alignment  
**0x200**|  QCFAIL| not passing quality controls  
**0x400**|  DUP| PCR or optical duplicate  
**0x800**|  SUPPLEMENTARY| supplementary alignment  
  
## AUTHOR

Written by Petr Danacek from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-flagstat(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools flagstat – counts the number of alignments for each FLAG type 

## SYNOPSIS

samtools [flagstat](samtools-flagstat.html) _in.sam_ |_in.bam_ |_in.cram_

## DESCRIPTION

Does a full pass through the input file to calculate and print statistics to stdout. 

Provides counts for each of 13 categories based primarily on bit flags in the FLAG field. Information on the meaning of the flags is given in the SAM specification document <<https://samtools.github.io/hts-specs/SAMv1.pdf>>. 

Each category in the output is broken down into QC pass and QC fail. In the default output format, these are presented as "#PASS + #FAIL" followed by a description of the category. 

The first row of output gives the total number of reads that are QC pass and fail (according to flag bit 0x200). For example: 

122 + 28 in total (QC-passed reads + QC-failed reads) 

Which would indicate that there are a total of 150 reads in the input file, 122 of which are marked as QC pass and 28 of which are marked as "not passing quality controls" 

Following this, additional categories are given for reads which are: 

primary
    

neither 0x100 (SECONDARY) nor 0x800 (SUPPLEMENTARY) bit set 

secondary
    

0x100 (SECONDARY) bit set 

supplementary
    

0x800 (SUPPLEMENTARY) bit set 

duplicates
    

0x400 (DUP) bit set 

primary duplicates
    

0x400 (DUP) bit set and neither 0x100 (SECONDARY) nor 0x800 (SUPPLEMENTARY) bit set 

mapped
    

0x4 (UNMAP) bit not set 

primary mapped
    

0x4 (UNMAP), 0x100 (SECONDARY) and 0x800 (SUPPLEMENTARY) bits not set 

paired in sequencing
    

0x1 (PAIRED) bit set 

read1
    

both 0x1 (PAIRED) and 0x40 (READ1) bits set 

read2
    

both 0x1 (PAIRED) and 0x80 (READ2) bits set 

properly paired
    

both 0x1 (PAIRED) and 0x2 (PROPER_PAIR) bits set and 0x4 (UNMAP) bit not set 

with itself and mate mapped
    

0x1 (PAIRED) bit set and neither 0x4 (UNMAP) nor 0x8 (MUNMAP) bits set 

singletons
    

both 0x1 (PAIRED) and 0x8 (MUNMAP) bits set and bit 0x4 (UNMAP) not set 

And finally, two rows are given that additionally filter on the reference name (RNAME), mate reference name (MRNM), and mapping quality (MAPQ) fields: 

with mate mapped to a different chr
    

0x1 (PAIRED) bit set and neither 0x4 (UNMAP) nor 0x8 (MUNMAP) bits set and MRNM not equal to RNAME 

with mate mapped to a different chr (mapQ>=5)
    

0x1 (PAIRED) bit set and neither 0x4 (UNMAP) nor 0x8 (MUNMAP) bits set and MRNM not equal to RNAME and MAPQ >= 5 

## ALTERNATIVE OUTPUT FORMATS

The **-O** option can be used to select two alternative formats for the output. 

Using **-O tsv** selects a tab-separated values format that can easily be imported into spreadsheet software. In this format the first column contains the values for QC-passed reads, the second column has the values for QC-failed reads and the third contains the category names. 

Using **-O json** generates an ECMA-404 JSON data interchange format object <<https://www.json.org/>>. The top-level object contains two named objects **QC-passed reads** and **QC-failed reads**. These contain the various categories listed above as names and the corresponding count as value. 

For the default format, **mapped** shows the count as a percentage of the total number of QC-passed or QC-failed reads after the category name. For example: 
    
    
    32 + 0 mapped (94.12% : N/A)
    

The **properly paired** and **singletons** counts work in a similar way but the percentage is against the total number of QC-passed and QC-failed pairs. The **primary mapped** count is a percentage of the total number of QC-passed and QC-failed primary reads. 

In the **tsv** and **json** formats, these percentages are listed in separate categories **mapped %** , **primary mapped %** , **properly paired %** , and **singletons %**. If the percentage cannot be calculated (because the total is zero) then in the **default** and **tsv** formats it will be reported as `N/A'. In the **json** format, it will be reported as a JSON `null' value. 

## OPTIONS

**-@**_INT_
    

Set number of additional threads to use when reading the file. 

**-O** _FORMAT_
    

Set the output format. _FORMAT_ can be set to `default', `json' or `tsv' to select the default, JSON or tab-separated values output format. If this option is not used, the default format will be selected. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-idxstats_](samtools-idxstats.html) (1), [_samtools-stats_](samtools-stats.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-fqidx(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools fqidx – indexes or queries regions from a fastq file 

## SYNOPSIS

samtools [fqidx](samtools-fqidx.html) _ref.fastq_ [_region1_ [...]] 

## DESCRIPTION

Index reference sequence in the FASTQ format or extract subsequence from indexed reference sequence. If no region is specified, **fqidx** will index the file and create _< ref.fastq>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTQ format. 

The input and output can be files compressed in the **BGZF** format. When output is compressed, the default compression level is 4. 

The sequences in the input file should all have different names. If they do not, indexing will emit a warning about duplicate sequences and retrieval will only produce subsequences from the first sequence with the duplicated name. 

**samtools fqidx** should only be used on fastq files with a small number of entries. Trying to use it on a file containing millions of short sequencing reads will produce an index that is almost as big as the original file, and searches using the index will be very slow and use a lot of memory. 

## OPTIONS

**-o, --output** _FILE_
    

Write FASTQ to file rather than to stdout. If _FILE_ ends with .gz, .bgz or .bgzf then it will be **BGZF** compressed. 

**-n, --length** _INT_
    

Length for FASTQ sequence line wrapping. If zero, this means do not line wrap. Defaults to the line length in the input file. 

**-c, --continue**
    

Continue working if a non-existent region is requested. 

**-r, --region-file** _FILE_
    

Read regions from a file. Format is chr:from-to, one per line. 

**-i, --reverse-complement**
    

Output the sequence as the reverse complement. When this option is used, “/rc” will be appended to the sequence names. To turn this off or change the string appended, use the **\--mark-strand** option. 

**\--mark-strand TYPE**
    

Append strand indicator to sequence name. TYPE can be one of: 

**rc**
    

Append '/rc' when writing the reverse complement. This is the default. 

**no**
    

Do not append anything. 

**sign**
    

Append '(+)' for forward strand or '(-)' for reverse complement. This matches the output of “bedtools getfasta -s”. 

**custom, <pos>,<neg>**
    

Append string <pos> to names when writing the forward strand and <neg> when writing the reverse strand. Spaces are preserved, so it is possible to move the indicator into the comment part of the description line by including a leading space in the strings <pos> and <neg>. 

**\--fai-idx FILE**
    

Read/Write to specified index file. 

**\--gzi-idx FILE**
    

Read/Write to specified compressed file index (used with .gz files). 

**-h, --help**
    

Print help message and exit. 

**\--output-fmt-option** _OPT=VAL_
    

Set the output format options, level=0..9 for compression level 0 to 9. 

**\--write-index**
    

Create index for the output sequence data along with the output, in same path as <output name>.fai, <outputname>.gzi. This option is valid only for file output. 

**-@, --threads** _N_
    

Set the number of extra threads for operations on compressed files. 

## AUTHOR

Written by Heng Li, with modifications by Andrew Whitwham and Robert Davies, all from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-faidx_](samtools-faidx.html) (1), [_samtools-fasta_](samtools-fasta.html) (1), [_samtools-fastq_](samtools-fastq.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-head(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools head – view SAM/BAM/CRAM file headers 

## SYNOPSIS

**samtools head** [**-h** _INT_] [**-n** _INT_] [_FILE_] 

## DESCRIPTION

By default, prints all headers from the specified input file to standard output in SAM format. The input alignment file may be in SAM, BAM, or CRAM format; if no _FILE_ is specified, standard input will be read. With appropriate options, only some of the headers and/or additionally some of the alignment records will be printed. 

The **samtools head** command outputs SAM headers exactly as they appear in the input file; in particular, it never adds an @PG header itself. (Other **samtools** commands add such @PG headers to facilitate provenance tracking in analysis pipelines, but because **samtools head** never outputs more than a handful of alignment records it is unsuitable for use in such contexts anyway.) 

## OPTIONS

**-h, --headers** _INT_
    

Display only the first _INT_ header lines. By default, all header lines are displayed. 

**-n, --records** _INT_
    

Also display the first _INT_ alignment records. By default, no alignment records are displayed. 

## AUTHOR

Written by John Marshall from the University of Glasgow. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-view_](samtools-view.html) (1) 

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-idxstats(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools idxstats – reports alignment summary statistics 

## SYNOPSIS

samtools [idxstats](samtools-idxstats.html) _in.sam_ |_in.bam_ |_in.cram_

## DESCRIPTION

Retrieve and print stats in the index file corresponding to the input file. Before calling idxstats, the input BAM file should be indexed by samtools index. 

If run on a SAM or CRAM file or an unindexed BAM file, this command will still produce the same summary statistics, but does so by reading through the entire file. This is far slower than using the BAM indices. 

The output is TAB-delimited with each line consisting of reference sequence name, sequence length, # mapped read-segments and # unmapped read-segments. It is written to stdout. Note this may count reads multiple times if they are mapped more than once or in multiple fragments. 

## OPTIONS

**-X**
    

This option will allow the user to specify a customised index file location. e.g. 

**samtools idxstat [options] -X /data_folder/data.bam /index_folder/index.bai**

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-flagstat_](samtools-flagstat.html) (1), [_samtools-index_](samtools-index.html) (1), [_samtools-stats_](samtools-stats.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-import(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools import – converts FASTQ files to unmapped SAM/BAM/CRAM 

## SYNOPSIS

samtools [import](samtools-import.html) [_options_] [ _fastq_file_ ... ] 

## DESCRIPTION

Reads one or more FASTQ files and converts them to unmapped SAM, BAM or CRAM. The input files may be automatically decompressed if they have a .gz extension. 

The simplest usage in the absence of any other command line options is to provide one or two input files. 

If a single file is given, it will be interpreted as a single-ended sequencing format unless the read names end with /1 and /2 in which case they will be labelled as PAIRED with READ1 or READ2 BAM flags set. If a pair of filenames are given they will be read from alternately to produce an interleaved output file, also setting PAIRED and READ1 / READ2 flags. 

The filenames may be explicitly labelled using **-1** and **-2** for READ1 and READ2 data files, **-s** for an interleaved paired file (or one half of a paired-end run), **-0** for unpaired data and explicit index files specified with **\--i1** and **\--i2**. These correspond to typical output produced by Illumina bcl2fastq and match the output from **samtools fastq**. The index files will set both the **BC** barcode code and it's associated **QT** quality tag. 

The Illumina CASAVA identifiers may also be processed when the **-i** option is given. This tag will be processed for READ1 / READ2, whether or not the read failed processing (QCFAIL flag), and the barcode sequence which will be added to the **BC** tag. This can be an alternative to explicitly specifying the index files, although note that doing so will not fill out the barcode quality tag. 

## OPTIONS

**-s** _FILE_
    

Import paired interleaved data from _FILE_. 

**-0** _FILE_
    

Import single-ended (unpaired) data from _FILE_. 

Operationally there is no difference between the **-s** and **-0** options as given an interleaved file with /1 and /2 read name endings both will correctly set the PAIRED, READ1 and READ2 flags, and given data with no suffixes and no CASAVA identifiers being processed both will leave the data as unpaired. However their inclusion here is for more descriptive command lines and to improve the header comment describing the samtools fastq decode command. 

**-1** _FILE_**, -2** _FILE_
    

Import paired data from a pair of FILEs. The BAM flag PAIRED will be set, but not PROPER_PAIR as it has not been aligned. READ1 and READ2 will be stored in their original, unmapped, orientation. 

**\--i1** _FILE_**, --i2 FILE**
    

Specifies index barcodes associated with the **-1** and **-2** files. These will be appended to READ1 and READ2 records in the barcode (BC) and quality (QT) tags. 

**-i**
    

Specifies that the Illumina CASAVA identifiers should be processed. This may set the READ1, READ2 and QCFAIL flags and add a barcode tag. 

**-U, --UMI**
    

Migrate the UMI sequence from the last read name component to the UMI bar code. 

**\--UMI-tag** _TAG_
    

Specifies which aux tag to place the UMI barcode into. default is `RX'. 

**-N, --name2**
    

Assume the read names are encoded in the SRA and ENA formats where the first word is an automatically generated name with the second field being the original name. This option extracts that second field instead. 

**\--barcode-tag TAG**
    

Changes the auxiliary tag used for barcode sequence. Defaults to BC. 

**\--quality-tag TAG**
    

Changes the auxiliary tag used for barcode quality. Defaults to QT. 

**-o** _FILE_
    

Output to _FILE_. By default output will be written to stdout. 

**\--order** _TAG_
    

When outputting a SAM record, also output an integer tag containing the Nth record number. This may be useful if the data is to be sorted or collated in some manner and we wish this to be reversible. In this case the tag may be used with **samtools sort -t TAG** to regenerate the original input order. 

Note integer tags can only hold up to 2^32 record numbers (approximately 4 billion). Data sets with more records can switch to using a fixed-width string tag instead, with leading 0s to ensure sort works. To do this specify TAG:LENGTH. E.g. **\--order rn:12** will be able to sort up to 1 trillion records. 

**-r** _RG_line_**, --rg-line** _RG_line_
    

A complete **@RG** header line may be specified, with or without the initial "@RG" component. If specified this will also use the ID field from _RG_line_ in each SAM records RG auxiliary tag. 

If specified multiple times this appends to the RG line, automatically adding tabs between invocations. 

**-R** _RG_ID_**, --rg** _RG_ID_
    

This is a shorter form of the option above, equivalent to **\--rg-line ID:**_RG_ID_. If both are specified then this option is ignored. 

**-u**
    

Output BAM or CRAM as uncompressed data. 

**-T** _TAGLIST_
    

This looks for any SAM-format auxiliary tags in the comment field of a fastq read name. These must match the <alpha-num><alpha-num>:<type>:<data> pattern as specified in the SAM specification. _TAGLIST_ can be blank or ***** to indicate all tags should be copied to the output, otherwise it is a comma-separated list of tag types to include with all others being discarded. 

## EXAMPLES

Convert a single-ended fastq file to an unmapped CRAM. Both of these commands perform the same action. 
    
    
    samtools import -0 in.fastq -o out.cram
    samtools import in.fastq > out.cram
    

Convert a pair of Illumina fastqs containing CASAVA identifiers to BAM, adding the barcode information to the BC auxiliary tag. 
    
    
    samtools import -i -1 in_1.fastq -2 in_2.fastq -o out.bam
    samtools import -i in_[12].fastq > out.bam
    

Specify the read group. These commands are equivalent 
    
    
    samtools import -r "$(echo -e 'ID:xyz\tPL:ILLUMINA')" in.fq
    samtools import -r "$(echo -e '@RG\tID:xyz\tPL:ILLUMINA')" in.fq
    samtools import -r ID:xyz -r PL:ILLUMINA in.fq
    

Create an unmapped BAM file from a set of 4 Illumina fastqs from bcf2fastq, consisting of two read and two index tags. The CASAVA identifier is used only for setting QC pass / failure status. 
    
    
    samtools import -i -1 R1.fq -2 R2.fq --i1 I1.fq --i2 I2.fq -o out.bam
    

Convert a pair of CASAVA barcoded fastq files to unmapped CRAM with an incremental record counter, then sort this by minimiser in order to reduce file space. The reversal process is also shown using samtools sort and samtools fastq. 
    
    
    samtools import -i in_1.fq in_2.fq --order ro -O bam,level=0 | \
        samtools sort -@4 -M -o out.srt.cram -
    
    
    
    samtools sort -@4 -O bam -u -t ro out.srt.cram | \
        samtools fastq -1 out_1.fq -2 out_2.fq -i --index-format "i*i*"
    

## AUTHOR

Written by James Bonfield of the Wellcome Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-fastq_](samtools-fastq.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-index(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools index – indexes SAM/BAM/CRAM files 

## SYNOPSIS

**samtools index -M** [**-bc**] [**-m** _INT_] _FILE FILE_ [_FILE_...] 

**samtools index** [**-bc**] [**-m** _INT_] _aln.sam_ |_aln.bam_ |_aln.cram_ [_out.index_] 

## DESCRIPTION

Index coordinate-sorted BGZIP-compressed SAM, BAM or CRAM files for fast random access. Note for SAM this only works if the file has been BGZF compressed first. (The first synopsis with multiple input _FILE_ s is only available with Samtools 1.16 or later.) 

This index is needed when _region_ arguments are used to limit **samtools view** and similar commands to particular regions of interest. 

When only one alignment file is being indexed, the output index filename can be specified via **-o** or as shown in the second synopsis. 

When no output filename is specified, for a CRAM file _aln.cram_ , index file _aln.cram_**.crai** will be created; for a BAM file _aln.bam_ , either _aln.bam_**.bai** or _aln.bam_**.csi** will be created; and for a compressed SAM file _aln.sam.gz_ , either _aln.sam.gz_**.bai** or _aln.sam.gz_**.csi** will be created, depending on the index format selected. 

The BAI index format can handle individual chromosomes up to 512 Mbp (2^29 bases) in length. If your input file might contain reads mapped to positions greater than that, you will need to use a CSI index. 

## OPTIONS

**-b, --bai**
    

Create a BAI index. This is currently the default when no format options are used. 

**-c, --csi**
    

Create a CSI index. By default, the minimum interval size for the index is 2^14, which is the same as the fixed value used by the BAI format. 

**-m, --min-shift** _INT_
    

Create a CSI index, with a minimum interval size of 2^INT. 

**-M**
    

Interpret all filename arguments as alignment files to be indexed individually. (Without **-M** , filename arguments are interpreted solely as per the second synopsis.) 

**-o, --output** _FILE_
    

Write the output index to _FILE_. (Currently may only be used when exactly one alignment file is being indexed.) 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-idxstats_](samtools-idxstats.html) (1), [_samtools-view_](samtools-view.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-markdup(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools markdup – mark duplicate alignments in a coordinate sorted file 

## SYNOPSIS

samtools [markdup](samtools-markdup.html) [**-l** _length_] [**-r**] [**-T**] [**-S**] [**-s**] [**-f** _file_] [**\--json**] [**-d** _distance_] [**-c**] [**-t**] [**\---duplicate-count**] [**-m**] [**\--mode**] [**\--include-fails**] [**\--no-PG**] [**-u**] [**\--no-multi-dup**] [**\--read-coords**] [**\--coords-order**] [**\--barcode-tag**] [**\--barcode-name**] [**\--barcode-rgx**] [**\--use-read-groups**] _in.algsort.bam out.bam_

## DESCRIPTION

Mark duplicate alignments from a coordinate sorted file that has been run through **samtools fixmate** with the **-m** option. This program relies on the MC and ms tags that fixmate provides. 

Duplicates are found by using the alignment data for each read (and its mate for paired reads). Position and orientation (which strand it aligns against and in what direction) are used to to compare the reads against one another. If two (or more) reads have the same values then the one with the highest base qualities is held to be the original and the others are the duplicates. 

It should be noted that **samtools markdup** looks for duplication first and then classifies the type of duplication afterwards. If your process does not care whether duplication is PCR or optical then it is faster if you do not use the optical duplicate option. 

Duplicates are marked by setting the alignment's DUP flag. 

For more details please see: 

<<http://www.htslib.org/algorithms/duplicate.html>>

## OPTIONS

**-l** _INT_
    

Expected maximum read length of _INT_ bases. [300] 

**-r**
    

Remove duplicate reads. 

**-T** _PREFIX_
    

Write temporary files to _PREFIX_**.**_samtools_**.**_nnnn_**.**_mmmm_**.**_tmp_

**-S**
    

Mark supplementary reads of duplicates as duplicates. 

**-s**
    

Print some basic stats. See STATISTICS. 

**-f** _file_
    

Write stats to named file. 

**\--json**
    

Output stats in JSON format. 

**-d** _distance_
    

The optical duplicate distance. Suggested settings of 100 for HiSeq style platforms or about 2500 for NovaSeq ones. Default is 0 to not look for optical duplicates. When set, duplicate reads are tagged with **dt:Z:SQ** for optical duplicates and **dt:Z:LB** otherwise. Calculation of distance depends on coordinate data embedded in the read names produced by the Illumina sequencing machines. Optical duplicate detection will not work on non standard names without the use of **\--read-coords**. 

**-c**
    

Clear previous duplicate settings and tags. 

**-t**
    

Mark duplicates with the name of the original in a **do** tag. 

**\--duplicate-count**
    

Record the original primary read duplication count (including itself) in a **dc** tag. 

**-m, --mode** _TYPE_
    

Duplicate decision method for paired reads. Values are **t** or **s**. Mode **t** measures positions based on template start/end (default). Mode **s** measures positions based on sequence start. While the two methods identify mostly the same reads as duplicates, mode **s** tends to return more results. Unpaired reads are treated identically by both modes. 

**-u**
    

Output uncompressed SAM, BAM or CRAM. 

**\--include-fails**
    

Include quality checked failed reads. 

**\--no-multi-dup**
    

Stop checking duplicates of duplicates for correctness. While still marking reads as duplicates further checks to make sure all optical duplicates are found are not carried out. Also operates on **-t** tagging where reads may tagged with a better quality read but not necessarily the best one. Using this option can speed up duplicate marking when there are a great many duplicates for each original read. 

**\--read-coords** _REGEX_
    

This takes a POSIX regular expression for at least x and y to be used in optical duplicate marking It can also include another part of the read name to test for equality, eg lane:tile elements. Elements wanted are captured with parentheses. Examples below. 

**\--coords-order** _ORDER_
    

The order of the elements captured in the regular expression. Default is txy where t is a part of the read name selected for string comparison and x/y the coordinates used for optical duplicate detection. Valid orders are: txy, tyx, xyt, yxt, xty, ytx, xy and yx. 

**\--barcode-tag** _TAG_
    

Duplicates must now also match the barcode tag. 

**\--barcode-name**
    

Use the UMI/barcode embedded in the read name (eigth colon delimited part). 

**\--barcode-rgx** _REGEX_
    

Regex for barcode in the readname (alternative to --barcode-name). 

**\--use-read-groups**
    

The @RG tags must now also match to be a duplicate. 

**\--no-PG**
    

Do not add a PG line to the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## STATISTICS

Entries are:   
**COMMAND** : the command line.   
**READ** : number of reads read in.   
**WRITTEN** : reads written out.   
**EXCLUDED** : reads ignored. See below.   
**EXAMINED** : reads examined for duplication.   
**PAIRED** : reads that are part of a pair.   
**SINGLE** : reads that are not part of a pair.   
**DUPLICATE PAIR** : reads in a duplicate pair.   
**DUPLICATE SINGLE** : single read duplicates.   
**DUPLICATE PAIR OPTICAL** : optical duplicate paired reads.   
**DUPLICATE SINGLE OPTICAL** : optical duplicate single reads.   
**DUPLICATE NON PRIMARY** : supplementary/secondary duplicate reads.   
**DUPLICATE NON PRIMARY OPTICAL** : supplementary/secondary optical duplicate reads.   
**DUPLICATE PRIMARY TOTAL** : number of primary duplicate reads.   
**DUPLICATE TOTAL** : total number of duplicate reads.   
**ESTIMATED LIBRARY SIZE** : estimate of the number of unique fragments in the sequencing library. 

Estimated library size makes various assumptions e.g. the library consists of unique fragments that are randomly selected (with replacement) with equal probability. This is unlikely to be true in practice. However it can provide a useful guide into how many unique read pairs are likely to be available. In particular it can be used to determine how much more data might be obtained by further sequencing of the library. 

Excluded reads are those marked as secondary, supplementary or unmapped. By default QC failed reads are also excluded but can be included as an option. Excluded reads are not used for calculating duplicates. They can optionally be marked as duplicates if they have a primary that is also a duplicate. 

## EXAMPLES

This first collate command can be omitted if the file is already name ordered or collated: 
    
    
    samtools collate -o namecollate.bam example.bam
    

Add ms and MC tags for markdup to use later: 
    
    
    samtools fixmate -m namecollate.bam fixmate.bam
    

Markdup needs position order: 
    
    
    samtools sort -o positionsort.bam fixmate.bam
    

Finally mark duplicates: 
    
    
    samtools markdup positionsort.bam markdup.bam
    

Typically the fixmate step would be applied immediately after sequence alignment and the markdup step after sorting by chromosome and position. Thus no _additional_ sort steps are normally needed. 

To use the regex to obtain coordinates from reads, two or three values have to be captured. To mimic the normal behaviour and match a read name of the format _machine:run:flowcell:lane:tile:x:y_ use: 
    
    
    --read-coords '([!-9;-?A-~]+:[0-9]+:[0-9]+:[0-9]+:[0-9]+):([0-9]+):([0-9]+)'
    --coords-order txy
    

To match only the coordinates of _x:y:randomstuff_ use: 
    
    
    --read-coords '^([[:digit:]]+):([[:digit:]]+)'
    --coords-order xy
    

To use a barcode from the read name matching the Illumina example of _NDX550136:7:H2MTNBDXX:1:13302:3141:10799:AAGGATG+TCGGAGA_ use: 
    
    
    --barcode-rgx '[0-9A-Za-z]+:[0-9]+:[0-9A-Za-z]+:[0-9]+:[0-9]+:[0-9]+:[0-9]+:([!-?A-~]+)'
    

It is possible that complex regular expressions may slow the running of the program. It would be best to keep them simple. 

## AUTHOR

Written by Andrew Whitwham from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_samtools-collate_](samtools-collate.html) (1), [_samtools-fixmate_](samtools-fixmate.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-merge(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools merge – merges multiple sorted files into a single file 

## SYNOPSIS

**samtools merge** [_options_] **-o** _out.bam_ [_options_] _in1.bam_ ... _inN.bam_

**samtools merge** [_options_] _out.bam_ _in1.bam_ ... _inN.bam_

## DESCRIPTION

Merge multiple sorted alignment files, producing a single sorted output file that contains all the input records and maintains the existing sort order. 

The output file can be specified via **-o** as shown in the first synopsis. Otherwise the first non-option filename argument is taken to be _out.bam_ rather than an input file, as in the second synopsis. There is no default; to write to standard output (or to a pipe), use either “**-o -** ” or the equivalent using “**-** ” as the first filename argument. 

If **-h** is specified the @SQ headers of input files will be merged into the specified header, otherwise they will be merged into a composite header created from the input headers. If in the process of merging @SQ lines for coordinate sorted input files, a conflict arises as to the order (for example input1.bam has @SQ for a,b,c and input2.bam has b,a,c) then the resulting output file will need to be re-sorted back into coordinate order. 

Unless the **-c** or **-p** flags are specified then when merging @RG and @PG records into the output header then any IDs found to be duplicates of existing IDs in the output header will have a suffix appended to them to differentiate them from similar header records from other files and the read records will be updated to reflect this. 

The ordering of the records in the input files must match the usage of the **-n** , **-N** , **-t** and **\--template-coordinate** command-line options. If they do not, the output order will be undefined. Note this also extends to disallowing mixing of "queryname" files with a combination of natural and lexicographical sort orders. See **sort** for information about record ordering. 

Problems may arise when attempting to merge thousands of files together. The operating system may impose a limit on the maximum number of simultaneously open files. See **ulimit -n** for more information. Additionally many files being read from simultaneously may cause a certain amount of "disk thrashing". To partially alleviate this the merge command will load 1MB of data at a time from each file, but this in turn adds to the overall merge program memory usage. Please take this into account when setting memory limits. 

In extreme cases, it may be necessary to reduce the problem to fewer files by successively merging subsets before a second round of merging. 

**-1**
    

Use Deflate compression level 1 to compress the output. 

**-b** _FILE_
    

List of input BAM files, one file per line. 

**-f**
    

Force to overwrite the output file if present. 

**-h** _FILE_
    

Use the lines of _FILE_ as `@' headers to be copied to _out.bam_ , replacing any header lines that would otherwise be copied from _in1.bam_. (_FILE_ is actually in SAM format, though any alignment records it may contain are ignored.) 

**-n**
    

The input alignments are sorted by read names using an alpha-numeric ordering, rather than by chromosomal coordinates. The alpha-numeric or “natural” sort order detects runs of digits in the strings and sorts these numerically. Hence "a7b" appears before "a12b". Note this is not suitable where hexadecimal values are in use. 

**-N**
    

The input alignments are sorted by read names using a lexicographical ordering, rather than by chromosomal coordinates. Unlike **-n** no detection of numeric components is used, instead relying purely on the ASCII value of each character. Hence "x12" comes before "x7" as "1" is before "7" in ASCII. This is a more appropriate name sort order where all digits in names are already zero-padded and/or hexadecimal values are being used. 

**-o** _FILE_
    

Write merged output to _FILE_ , specifying the filename via an option rather than as the first filename argument. When **-o** is used, all non-option filename arguments specify input files to be merged. 

**-t TAG**
    

The input alignments have been sorted by the value of TAG, then by either position or name (if **-n** is given). 

**\--template-coordinate**
    

Input files are sorted by template-coordinate. 

**-R** _STR_
    

Merge files in the specified region indicated by _STR_ [null] 

**-r**
    

Attach an RG tag to each alignment. The tag value is inferred from file names. 

**-u**
    

Uncompressed BAM output 

**-c**
    

When several input files contain @RG headers with the same ID, emit only one of them (namely, the header line from the first file we find that ID in) to the merged output file. Combining these similar headers is usually the right thing to do when the files being merged originated from the same file. 

Without **-c** , all @RG headers appear in the output file, with random suffixes added to their IDs where necessary to differentiate them. 

**-p**
    

Similarly, for each @PG ID in the set of files to merge, use the @PG line of the first file we find that ID in rather than adding a suffix to differentiate similar IDs. 

**-X**
    

If this option is set, it will allows user to specify customized index file location(s) if the data folder does not contain any index file. See **EXAMPLES** section for sample of usage. 

**-L** _FILE_
    

BED file for specifying multiple regions on which the merge will be performed. This option extends the usage of **-R** option and cannot be used concurrently with it. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## EXAMPLES

  * Attach the **RG** tag while merging sorted alignments: 
        
        printf '@RG\tID:ga\tSM:hs\tLB:ga\tPL:ILLUMINA\n@RG\tID:454\tSM:hs\tLB:454\tPL:LS454\n' > rg.txt
        samtools merge -rh rg.txt merged.bam ga.bam 454.bam
        

The value in a **RG** tag is determined by the file name the read is coming from. In this example, in the _merged.bam_ , reads from _ga.bam_ will be attached _RG:Z:ga_ , while reads from _454.bam_ will be attached _RG:Z:454_. 

  * Include customized index file as a part of arguments: 
        
        samtools merge [options] -X <out.bam> </data_folder/in1.bam> [</data_folder/in2.bam> ... </data_folder/inN.bam>] </index_folder/index1.bai> [</index_folder/index2.bai> ... </index_folder/indexN.bai>]
        

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_sam_](sam.html) (5) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-mpileup(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools mpileup – produces "pileup" textual format from an alignment 

## SYNOPSIS

samtools [mpileup](samtools-mpileup.html) [**-EB**] [**-C** _capQcoef_] [**-r** _reg_] [**-f** _in.fa_] [**-l** _list_] [**-Q** _minBaseQ_] [**-q** _minMapQ_] _in.bam_ [_in2.bam_ [_..._]] 

## DESCRIPTION

Generate text pileup output for one or multiple BAM files. Each input file produces a separate group of pileup columns in the output. 

Note that there are two orthogonal ways to specify locations in the input file; via **-r** _region_ and **-l** _file_. The former uses (and requires) an index to do random access while the latter streams through the file contents filtering out the specified regions, requiring no index. The two may be used in conjunction. For example a BED file containing locations of genes in chromosome 20 could be specified using **-r 20 -l chr20.bed** , meaning that the index is used to find chromosome 20 and then it is filtered for the regions listed in the bed file. 

Unmapped reads are not considered and are always discarded. By default secondary alignments, QC failures and duplicate reads will be omitted, along with low quality bases and some reads in high depth regions. See the **\--ff** , **-Q** and **-d** options for changing this. 

### Pileup Format

Pileup format consists of TAB-separated lines, with each line representing the pileup of reads at a single genomic position. 

Several columns contain numeric quality values encoded as individual ASCII characters. Each character can range from “!” to “~” and is decoded by taking its ASCII value and subtracting 33; e.g., “A” encodes the numeric value 32. 

The first three columns give the position and reference: 

  * Chromosome name. 
  * 1-based position on the chromosome. 
  * Reference base at this position (this will be “N” on all lines if **-f** /**\--fasta-ref** has not been used). 

The remaining columns show the pileup data, and are repeated for each input BAM file specified: 

  * Number of reads covering this position. 
  * Read bases. This encodes information on matches, mismatches, indels, strand, mapping quality, and starts and ends of reads. 

For each read covering the position, this column contains: 
    * If this is the first position covered by the read, a “^” character followed by the alignment's mapping quality encoded as an ASCII character. 
    * A single character indicating the read base and the strand to which the read has been mapped:  Forward| Reverse| Meaning  
---|---|---  
**.** dot| **,** comma| Base matches the reference base  
**ACGTN**| **acgtn**|  Base is a mismatch to the reference base  
**>**| **<**|  Reference skip (due to CIGAR “N”)  
*****|  ***** /**#**|  Deletion of the reference base (CIGAR “D”)  
  
Deleted bases are shown as “*” on both strands unless **\--reverse-del** is used, in which case they are shown as “#” on the reverse strand. 

    * If there is an insertion after this read base, text matching “\\+[0-9]+[ACGTNacgtn*#]+”: a “+” character followed by an integer giving the length of the insertion and then the inserted sequence. Pads are shown as “*” unless **\--reverse-del** is used, in which case pads on the reverse strand will be shown as “#”. 
    * If there is a deletion after this read base, text matching “-[0-9]+[ACGTNacgtn]+”: a “-” character followed by the deleted reference bases represented similarly. (Subsequent pileup lines will contain “*” for this read indicating the deleted bases.) 
    * If this is the last position covered by the read, a “$” character. 

  * Base qualities, encoded as ASCII characters. 
  * Alignment mapping qualities, encoded as ASCII characters. (Column only present when **-s** /**\--output-MQ** is used.) 
  * Comma-separated 1-based positions within the alignments, in the orientation shown in the input file. E.g., 5 indicates that it is the fifth base of the corresponding read that is mapped to this genomic position. (Column only present when **-O** /**\--output-BP** is used.) 
  * Additional comma-separated read field columns, as selected via **\--output-extra**. The fields selected appear in the same order as in SAM: **QNAME** , **FLAG** , **RNAME** , **POS** , **MAPQ** (displayed numerically), **RNEXT** , **PNEXT** , followed by **RLEN** for unclipped read length. 
  * Comma-separated 1-based positions within the alignments, in 5' to 3' orientation. E.g., 5 indicates that it is the fifth base of the corresponding read as produced by the sequencing instrument, that is mapped to this genomic position. (Column only present when **\--output-BP-5** is used.) 

  * Additional read tag field columns, as selected via **\--output-extra**. These columns are formatted as determined by **\--output-sep** and **\--output-empty** (comma-separated by default), and appear in the same order as the tags are given in **\--output-extra**. 

Any output column that would be empty, such as a tag which is not present or the filtered sequence depth is zero, is reported as "*". This ensures a consistent number of columns across all reported positions. 

## OPTIONS

**-6, --illumina1.3+**
    

Assume the quality is in the Illumina 1.3+ encoding. 

**-A, --count-orphans**
    

Do not skip anomalous read pairs in variant calling. Anomalous read pairs are those marked in the FLAG field as paired in sequencing but without the properly-paired flag set. 

**-b, --bam-list** _FILE_
    

List of input BAM files, one file per line [null] 

**-B, --no-BAQ**
    

Disable base alignment quality (BAQ) computation. See **BAQ** below. 

**-C, --adjust-MQ** _INT_
    

Coefficient for downgrading mapping quality for reads containing excessive mismatches. Mismatches are counted as a proportion of the number of aligned bases ("M", "X" or "=" CIGAR operations), along with their quality, to derive an upper-bound of the mapping quality. Original mapping qualities lower than this are left intact, while higher ones are capped at the new adjusted score. 

The exact formula is complex and likely tuned to specific instruments and specific alignment tools, so this option is disabled by default (indicated as having a zero value). Variables in the formulae and their meaning are defined below. 

**Variable**| **Meaning / formula**  
---|---  
**M**|  The number of matching CIGAR bases (operation "M", "X" or "=").  
**X**|  The number of substitutions with quality >= 13.  
**SubQ**|  The summed quality of substitution bases included in X, capped at a maximum of quality 33 per mismatching base.  
**ClipQ**|  The summed quality of soft-clipped or hard-clipped bases. This has no minimum or maximum quality threshold per base. For hard-clipped bases the per-base quality is taken as 13.  
**T**|  SubQ - 10 * log10(M^X / X!) + ClipQ/5  
**Cap**|  MAX(0, INT * sqrt((INT - T) / INT))  
  
Some notes on the impact of this. 

  * As the number of mismatches increases, the mapping quality cap reduces, eventually resulting in discarded alignments. 

  * High quality mismatches reduces the cap faster than low quality mismatches. 

  * The starting INT value also acts as a hard cap on mapping quality, even when zero mismatches are observed. 

  * Indels have no impact on the mapping quality. 

The intent of this option is to work around aligners that compute a mapping quality using a local alignment without having any regard to the degree of clipping required or consideration of potential contamination or large scale insertions with respect to the reference. A record may align uniquely and have no close second match, but having a high number of mismatches may still imply that the reference is not the correct site. 

However we do not recommend use of this parameter unless you fully understand the impact of it and have determined that it is appropriate for your sequencing technology. 

**-d, --max-depth** _INT_
    

At a position, read maximally _INT_ reads per input file. Setting this limit reduces the amount of memory and time needed to process regions with very high coverage. Passing zero for this option sets it to the highest possible value, effectively removing the depth limit. [8000] 

Note that up to release 1.8, samtools would enforce a minimum value for this option. This no longer happens and the limit is set exactly as specified. 

**-E, --redo-BAQ**
    

Recalculate BAQ on the fly, ignore existing BQ tags. See **BAQ** below. 

**-f, --fasta-ref** _FILE_
    

The **faidx** -indexed reference file in the FASTA format. The file can be optionally compressed by **bgzip**. [null] 

Supplying a reference file will enable base alignment quality calculation for all reads aligned to a reference in the file. See **BAQ** below. 

**-G, --exclude-RG** _FILE_
    

Exclude reads from read groups listed in FILE (one @RG-ID per line) 

**-l, --positions** _FILE_
    

BED or position list file containing a list of regions or sites where pileup or BCF should be generated. Position list files contain two columns (chromosome and position) and start counting from 1. BED files contain at least 3 columns (chromosome, start and end position) and are 0-based half-open.   
While it is possible to mix both position-list and BED coordinates in the same file, this is strongly ill advised due to the differing coordinate systems. [null] 

**-q, --min-MQ** _INT_
    

Minimum mapping quality for an alignment to be used [0] 

**-Q, --min-BQ** _INT_
    

Minimum base quality for a base to be considered. [13] 

Note base-quality 0 is used as a filtering mechanism for overlap removal which marks bases as having quality zero and lets the base quality filter remove them. Hence using **\--min-BQ 0** will make the overlapping bases reappear, albeit with quality zero. 

**-r, --region** _STR_
    

Only generate pileup in region. Requires the BAM files to be indexed. If used in conjunction with -l then considers the intersection of the two requests. _STR_ [all sites] 

**-R, --ignore-RG**
    

Ignore RG tags. Treat all reads in one BAM as one sample. 

**\--rf, --incl-flags** _STR|INT_
    

Required flags: only include reads with any of the mask bits set [null]. Note this is implemented as a filter-out rule, rejecting reads that have none of the mask bits set. Hence this does not override the **\--excl-flags** option. 

**\--ff, --excl-flags** _STR|INT_
    

Filter flags: skip reads with any of the mask bits set. This defaults to SECONDARY,QCFAIL,DUP. The option is not accumulative, so specifying e.g. **\--ff QCFAIL** will reenable output of secondary and duplicate alignments. Note this does not override the **\--incl-flags** option. 

**-x, --ignore-overlaps-removal, --disable-overlap-removal**
    

Overlap detection and removal is enabled by default. This option turns it off. 

When enabled, where the ends of a read-pair overlap the overlapping region will have one base selected and the duplicate base nullified by setting its phred score to zero. It will then be discarded by the **\--min-BQ** option unless this is zero. 

The quality values of the retained base within an overlap will be the summation of the two bases if they agree, or 0.8 times the higher of the two bases if they disagree, with the base nucleotide also being the higher confident call. 

**-X**
    

Include customized index file as a part of arguments. See **EXAMPLES** section for sample of usage. 

**Output Options:**

**-o, --output** _FILE_
    

Write pileup output to _FILE_ , rather than the default of standard output. 

**-O, --output-BP**
    

Output base positions on reads in orientation listed in the SAM file (left to right). 

**\--output-BP-5**
    

Output base positions on reads in their original 5' to 3' orientation. 

**-s, --output-MQ**
    

Output mapping qualities encoded as ASCII characters. 

**\--output-QNAME**
    

Output an extra column containing comma-separated read names. Equivalent to **\--output-extra QNAME**. 

**\--output-extra** _STR_
    

Output extra columns containing comma-separated values of read fields or read tags. The names of the selected fields have to be provided as they are described in the SAM Specification (pag. 6) and will be output by the mpileup command in the same order as in the document (i.e. **QNAME** , **FLAG** , **RNAME** ,...) The names are case sensitive. Currently, only the following fields are supported: 

**QNAME, FLAG, RNAME, POS, MAPQ, RNEXT, PNEXT, RLEN**

Anything that is not on this list is treated as a potential tag, although only two character tags are accepted. In the mpileup output, tag columns are displayed in the order they were provided by the user in the command line. Field and tag names have to be provided in a comma-separated string to the mpileup command. Tags with type **B** (byte array) type are not supported. An absent or unsupported tag will be listed as "*". E.g. 

**samtools mpileup --output-extra FLAG,QNAME,RG,NM in.bam**

will display four extra columns in the mpileup output, the first being a list of comma-separated read names, followed by a list of flag values, a list of RG tag values and a list of NM tag values. Field values are always displayed before tag values. 

**\--output-sep** _CHAR_
    

Specify a different separator character for tag value lists, when those values might contain one or more commas (**,**), which is the default list separator. This option only affects columns for two-letter tags like NM; standard fields like FLAG or QNAME will always be separated by commas. 

**\--output-empty** _CHAR_
    

Specify a different 'no value' character for tag list entries corresponding to reads that don't have a tag requested with the **\--output-extra** option. The default is *****. 

This option only applies to rows that have at least one read in the pileup, and only to columns for two-letter tags. Columns for empty rows will always be printed as *****. 

**-M, --output-mods**
    

Adds base modification markup into the sequence column. This uses the **Mm** and **Ml** auxiliary tags (or their uppercase equivalents). Any base in the sequence output may be followed by a series of _strand_ _code_ _quality_ strings enclosed within square brackets where strand is "+" or "-", code is a single character (such as "m" or "h") or a ChEBI numeric in parentheses, and quality is an optional numeric quality value. For example a "C" base with possible 5mC and 5hmC base modification may be reported as "C[+m179+h40]". 

Quality values are from 0 to 255 inclusive, representing a linear scale of probability 0.0 to 1.0 in 1/256ths increments. If quality values are absent (no **Ml** tag) these are omitted, giving an example string of "C[+m+h]". 

Note the base modifications may be identified on the reverse strand, either due to the native ability for this detection by the sequencing instrument or by the sequence subsequently being reverse complemented. This can lead to modification codes, such as "m" meaning 5mC, being shown for their complementary bases, such as "G[-m50]". 

When **\--output-mods** is selected base modifications can appear on any base in the sequence output, including during insertions. This may make parsing the string more complex, so also see the **\--no-output-ins-mods** and **\--no-output-ins** options to simplify this process. 

**\--no-output-ins**
    

Do not output the inserted bases in the sequence column. Usually this is reported as "+_length_ _sequence_ ", but with this option it becomes simply "+_length_ ". For example an insertion of AGT in a pileup column changes from "CCC+3AGTGCC" to "CCC+3GCC". 

Specifying this option twice also removes the "+_length_ " portion, changing the example above to "CCCGCC". 

The purpose of this change is to simplify parsing using basic regular expressions, which traditionally cannot perform counting operations. It is particularly beneficial when used in conjunction with **\--output-mods** as the syntax of the inserted sequence is adjusted to also report possible base modifications, but see also **\--no-output-ins-mods** as an alternative. 

**\--no-output-ins-mods**
    

Outputs the inserted bases in the sequence, but excluding any base modifications. This only affects output when **\--output-mods** is also used. 

**\--no-output-del**
    

Do not output deleted reference bases in the sequence column. Normally this is reported as "+_length_ _sequence_ ", but with this option it becomes simply "+_length_ ". For example an deletion of 3 unknown bases (due to no reference being specified) would normally be seen in a column as e.g. "CCC-3NNNGCC", but will be reported as "CCC-3GCC" with this option. 

Specifying this option twice also removes the "-_length_ " portion, changing the example above to "CCCGCC". 

The purpose of this change is to simplify parsing using basic regular expressions, which traditionally cannot perform counting operations. See also **\--no-output-ins**. 

**\--no-output-ends**
    

Removes the “^” (with mapping quality) and “$” markup from the sequence column. 

**\--reverse-del**
    

Mark the deletions on the reverse strand with the character **#** , instead of the usual *****. 

**-a**
    

Output all positions, including those with zero depth. 

**-a -a, -aa**
    

Output absolutely all positions, including unused reference sequences. Note that when used in conjunction with a BED file the -a option may sometimes operate as if -aa was specified if the reference sequence has coverage outside of the region specified in the BED file. 

**BAQ (Base Alignment Quality)**

BAQ is the Phred-scaled probability of a read base being misaligned. It greatly helps to reduce false SNPs caused by misalignments. BAQ is calculated using the probabilistic realignment method described in the paper “Improving SNP discovery by base alignment quality”, Heng Li, Bioinformatics, Volume 27, Issue 8 <<https://doi.org/10.1093/bioinformatics/btr076>>

BAQ is applied to modify quality values before the **-Q** filtering happens and before the choice of which sequence to retain when removing overlaps. 

BAQ is turned on when a reference file is supplied using the **-f** option. To disable it, use the **-B** option. 

It is possible to store precalculated BAQ values in a SAM BQ:Z tag. Samtools mpileup will use the precalculated values if it finds them. The **-E** option can be used to make it ignore the contents of the BQ:Z tag and force it to recalculate the BAQ scores by making a new alignment. 

## EXAMPLES

Using range: With implicit index files in1.bam.<ext> and in2.sam.gz.<ext>, 
    
    
    samtools mpileup in1.bam in2.sam.gz -r chr10:100000-200000
    

With explicit index files, 
    
    
    samtools mpileup in1.bam in2.sam.gz idx/in1.csi idx/in2.csi -X -r chr10:100000-200000
    

With fofn being a file of input file names, and implicit index files present with inputs, 
    
    
    samtools mpileup -b fofn -r chr10:100000-200000
    

Using flags: To get reads with flags READ2 or REVERSE and not having any of SECONDARY,QCFAIL,DUP, 
    
    
    samtools mpileup --rf READ2,REVERSE in.sam
    

or 
    
    
    samtools mpileup --rf 144 in.sam
    

To get reads with flag SECONDARY, 
    
    
    samtools mpileup --rf SECONDARY --ff QCFAIL,DUP in.sam
    

Using all possible alignmentes: To show all possible alignments, either of below two equivalent commands may be used, 
    
    
    samtools mpileup --count-orphans --no-BAQ --max-depth 0 --fasta-ref ref_file.fa \
    --min-BQ 0 --excl-flags 0 --disable-overlap-removal in.sam
    
    
    
    samtools mpileup -A -B -d 0 -f ref_file.fa -Q 0 --ff 0 -x in.sam
    

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-depth_](samtools-depth.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_bcftools_](bcftools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-phase(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools phase – call and phase heterozygous SNPs 

## SYNOPSIS

samtools [phase](samtools-phase.html) [**-AF**] [**-k** _len_] [**-b** _prefix_] [**-q** _minLOD_] [**-Q** _minBaseQ_] _in.bam_

## DESCRIPTION

Call and phase heterozygous SNPs. 

## OPTIONS

**-A**
    

Drop reads with ambiguous phase. 

**-b** _STR_
    

Prefix of BAM output. When this option is in use, phase-0 reads will be saved in file **STR**.0.bam and phase-1 reads in **STR**.1.bam. Phase unknown reads will be randomly allocated to one of the two files. Chimeric reads with switch errors will be saved in **STR**.chimeric.bam. [null] 

**-F**
    

Do not attempt to fix chimeric reads. 

**-k** _INT_
    

Maximum length for local phasing. [13] 

**-q** _INT_
    

Minimum Phred-scaled LOD to call a heterozygote. [40] 

**-Q, --min-BQ** _INT_
    

Minimum base quality to be used in het calling. [13] 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-quickcheck(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools quickcheck – a rapid sanity check on input files 

## SYNOPSIS

samtools [quickcheck](samtools-quickcheck.html) [_options_] _in.sam_ |_in.bam_ |_in.cram_ [ ... ] 

## DESCRIPTION

Quickly check that input files appear to be intact. Checks that beginning of the file contains a valid header (all formats) containing at least one target sequence and then seeks to the end of the file and checks that an end-of-file (EOF) is present and intact (BAM and CRAM only). 

Data in the middle of the file is not read since that would be much more time consuming, so please note that this command will not detect internal corruption, but is useful for testing that files are not truncated before performing more intensive tasks on them. 

This command will exit with a non-zero exit code if any input files don't have a valid header or are missing an EOF block. Otherwise it will exit successfully (with a zero exit code). 

## OPTIONS

**-v**
    

Verbose output: will additionally print the names of all input files that don't pass the check to stdout. Multiple -v options will cause additional messages regarding check results to be printed to stderr. 

**-q**
    

Quiet mode: disables warning messages on stderr about files that fail. If both -q and -v options are used then the appropriate level of -v takes precedence. 

**-u**
    

Expect unmapped input data, so do not require targets in the header. 

## AUTHOR

Written by Josh Randall from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-reference(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools reference – extracts an embedded reference from a CRAM file 

## SYNOPSIS

samtools [reference](samtools-reference.html) [**-q**] [**-r** _region_] [**-o** _out.fa_] _in.cram_

## DESCRIPTION

Creates the reference from aligned data using either the MD:Z auxiliary tags or an embedded reference in a CRAM file. The output is a FASTA file. 

For the embedded reference mode (**-e**) this operation is fast, but only works on CRAMs produced using **\--output-fmt-option embed_ref=1**. Note this may not be the complete reference used. Each CRAM slice will hold the entire reference that spans the slice coordinates, but gaps in coverage can lead to gaps between slices. However this reference should be suitable for passing into a CRAM decode (**samtools view -T ref.fa**). 

For SAM/BAM files or CRAMs without reference, using the MD:Z tag may also produce an incomplete reference. Unlike embedded reference, this reference may not be sufficient for decoding a CRAM file as the CRAM slice headers store the MD5sum of the portion of reference than spans that slice, but the slice may not have 100% coverage leading to Ns in the computed reference. However it should still be possible to decode such CRAMs by ignoring the md5 mismatches using e.g. **samtools view \--input-fmt-option ignore_md5=1**. 

## OPTIONS

**-e**
    

Enable CRAM embedded reference mode. 

**-q**
    

Enables quiet mode and will produce no output. By default a line per reference is reporting describing the percentage with non-N bases. 

**-r** _region_
    

Specifies a single region to produce the reference from. If specified, an index file must be present. 

**-o** _FILE_
    

Write the FASTA records to _FILE_. By default this is sent to stdout. 

**-@**_INT_
    

The number of BAM/CRAM decompression threads to use in addition to the main thread [0]. 

Note this does not multi-thread the main reference generation steps, so scaling may be capped by 2 or 3 threads, depending on the data. It will also not affect the **-e** option for CRAM embedded reference, although this is already the fastest method. 

## AUTHOR

Written by James Bonfield from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-reheader(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools reheader – replaces the header in the input file 

## SYNOPSIS

samtools [reheader](samtools-reheader.html) [**-iP**] [**-c** _CMD_ | _in.header.sam_] _in.bam_

## DESCRIPTION

Replace the header in _in.bam_ with the header in _in.header.sam_. This command is much faster than replacing the header with a BAM→SAM→BAM conversion. 

By default this command outputs the BAM or CRAM file to standard output (stdout), but for CRAM format files it has the option to perform an in-place edit, both reading and writing to the same file. No validity checking is performed on the header, nor that it is suitable to use with the sequence data itself. 

## OPTIONS

**-P, --no-PG**
    

Do not add a @PG line to the header of the output file. 

**-i, --in-place**
    

Perform the header edit in-place, if possible. This only works on CRAM files and only if there is sufficient room to store the new header. The amount of space available will differ for each CRAM file. 

**-c, --command** _CMD_
    

Allow the header from _in.bam_ to be processed by external _CMD_ and read back the result. When used in this manner, the external header file _in.header.sam_ has to be omitted. 

_CMD_ must take the original header through stdin in SAM format and output the modified header to stdout. _CMD_ is passed to the system's command shell. Care should be taken to ensure the command is quoted correctly to avoid unwanted shell expansions (for example of $ variables). 

_CMD_ must return an exit status of zero. 

## EXAMPLES

  * Remove comment lines 
        
        samtools reheader -c 'grep -v ^@CO' in.bam
        

  * Add “Chr” prefix to chromosome names. Note extra backslashes before dollar signs to prevent unwanted shell variable expansion. 
        
        samtools reheader -c 'perl -pe "s/^(@SQ.*)(\tSN:)(\d+|X|Y|MT)(\s|\$)/\$1Chr\$2\$3/"' in.bam
        

  * Remove “Chr” prefix 
        
        samtools reheader -c 'perl -pe "s/^(@SQ.*)(\tSN:)Chr/\$1\$2/"' in.bam
        

## AUTHOR

Written by Heng Li with modifications by James Bonfield and Valeriu Ohan, all from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-reset(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools reset – removes the alignment information added by aligners and updates flags accordingly 

## SYNOPSIS

samtools [reset](samtools-reset.html) [**-o** _FILE_] [**-x,--remove-tag** _STR_] [**\--keep-tag** _STR_] [**\--reject-PG** _pgid_] [**\--no-RG**] [**\--no-PG**] [**\--dupflag**] [...] 

## DESCRIPTION

Removes the alignment information added by the aligner. CIGAR and reference data are removed. Flags are updated as unmapped, non-duplicate and as not a proper pair. If the alignment was in reverse direction, data and its quality values are reversed and complemented and the reverse flag is reset. Supplementary and secondary alignment data are discarded. 

Aux tags that will be retained in output can be controlled by keep-tag and remove-tag/x. These options take tags as comma separated lists. Aux tags AS, CC, CG, CP, H1, H2, HI, H0, IH, MC, MD, MQ, NM, SA and TS are removed by default, this can be overridden using keep-tag. 

PG and RG tags from input are written on the output by default. CO lines are not retained after this operation. 

The sort order is unchanged, so users may consider combining this with **samtools collate** or **sort -n** if it is a requirement to group pairs of sequences together. 

## OPTIONS

**-o** _FILE_
    

Output file to which reset data is to be written. If not given, standard output will be used. 

**-x** _STR_**, --remove-tag** _STR_
    

Read tag(s) to exclude from output (repeatable) [null]. This can be a single tag or a comma separated list. Alternatively the option itself can be repeated multiple times. 

If the list starts with a `^' then it is negated and treated as a request to remove all tags except those in _STR_. The list may be empty, so **-x ^** will remove all tags. 

**\--keep-tag** _STR_
    

This keeps _only_ tags listed in _STR_ and is directly equivalent to **\--remove-tag ^**_STR_. Specifying an empty list will remove all tags. If both **\--keep-tag** and **\--remove-tag** are specified then **\--keep-tag** has precedence. 

**\--reject-PG** _pgid_
    

The PG line which has the ID matching _pgid_ and all subsequent PG lines will be removed. If the option itself is absent, the default, all PG entries will be in output. 

**\--no-RG**
    

RG lines in input will be discarded with this option. By default, RG lines will be present in output. 

With this option, RG aux tags will also be discarded. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file listing the **reset** command. By default the PG entry for reset will be present in the output. 

**\--dupflag**
    

Keep the duplicate flag as it is. This option is absent by default and alignments are marked non-duplicates. 

**-@, --threads** _N_
    

This gives the number of worker threads to be used. 

**-O, --output-fmt** _FMT[,options]_
    

Sets the format of the output file and any associated format-specific options. If this option is not present, the format is identified from the output file name extension. 

## EXAMPLES

Basic usage, to reset the data: 
    
    
    samtools reset -o out.bam in.bam
    

To keep aux tags RG and BC in the output: 
    
    
    samtools reset -o out.sam --keep-tag RG,BC in.bam
    

To discard PG entries from 'bwa_index' onwards, 
    
    
    samtools reset -o out.sam --reject-PG=bwa_index
    

To set output format for use within a pipeline: 
    
    
    samtools collate -O -u input.cram | \
      samtools reset --output-fmt BAM,level=0 | \
      myaligner -I bam -o out.bam
    

## AUTHOR

Written by Vasudeva Sarma of the Wellcome Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-collate_](samtools-collate.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-samples(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools samples – prints the samples from an alignment file 

## SYNOPSIS

**samtools samples** [_options_] _( <input>|stdin)_

**samtools samples** [_options_] **-X** _f1.bam_ _f2.bam_ ... _f1.bam.bai_ _f2.bam.bai_ ... 

## DESCRIPTION

Print the sample names found in the read-groups and the path to the reference genome from alignment files. The output of this tool can be used to create an input for any popular workflow manager. The input is a list of SAM/BAM/CRAM files, or the path to those files can be provided via stdin. The output is tab-delimited containing the sample name as the first column, the path to the alignment file as the second column, the path to the reference genome as a third optional column and a single character flag (Y/N) indicating whether the alignment file is indexed or not as a fourth optional column. If no reference is found for an alignment, a dot (.) will be used in the reference path column. If no sample is available in any read-group header, a dot (.) will be used as the sample name. If a BAM file contains more than one sample, one line will be printed for each sample. 

## OPTIONS

**-?**
    

print help and exit 

**-h**
    

print a header 

**-i**
    

test if the file is indexed. Add an extra column to the output with a single character value (Y/N). 

**-T** _TAG_
    

provide the sample tag name from the @RG line [SM]. 

**-o** _FILE_
    

output file [stdout]. 

**-f** _FILE_
    

load an indexed fasta file in the collection of references. Can be used multiple times. Add an extra column with the path to the reference file. 

**-F** _FILE_
    

read a file containing the paths to indexed fasta files. One path per line. 

**-X**
    

use a custom index file. 

## EXAMPLES

  * print the samples from a set of BAM/SAM files, with a header. There is no sample defined in the header of 'example.sam', so a dot is used for the sample name. 
        
        $ samtools  samples -h S*.bam *.sam
        #SM	PATH
        S1	S1.bam
        S2	S2.bam
        S3	S3.bam
        S4	S4.bam
        S5	S5.bam
        .	example.sam
        

  * print the samples from a set of BAM/SAM files, with a header, print whether the file is indexed. 
        
        $  samtools  samples -i -h S*.bam *.sam
        #SM	PATH	INDEX
        S1	S1.bam	Y
        S2	S2.bam	Y
        S3	S3.bam	Y
        S4	S4.bam	Y
        S5	S5.bam	Y
        .	example.sam	N
        

  * print whether the files are indexed using custom bai files. 
        
        $ samtools samples -i -h -X S1.bam S2.bam S1.bam.bai S2.bam.bai
        #SM	PATH	INDEX
        S1	S1.bam	Y
        S2	S2.bam	Y
        

  * read a tab delimited input <file>(tab)<bai> and print whether the files are indexed using custom bai files. 
        
        $ find . -type f \( -name "S*.bam" -o -name "S*.bai" \) | sort | paste - - | samtools samples -i -h -X
        #SM	PATH	INDEX
        S1	./S1.bam	Y
        S2	./S2.bam	Y
        S3	./S3.bam	Y
        S4	./S4.bam	Y
        S5	./S5.bam	Y
        

  * print the samples from a set of BAM/CRAM files, with a header, use '@RG/LB' instead of '@RG/SM'. 
        
        $ samtools  samples -h -T LB S*.bam
        #LB	PATH
        S1	S1.bam
        S2	S2.bam
        S3	S3.bam
        S4	S4.bam
        S5Lib1	S5.bam
        S5Lib2	S5.bam
        

  * pipe a list of BAM/CRAM files , pipe it into samtools samples. 
        
        $ find . -type f \( -name "S*.bam" -o -name "*.cram" \) | samtools  samples -h
        #SM	PATH
        S5	./S5.bam
        S2	./S2.bam
        S4	./S4.bam
        S3	./S3.bam
        S1	./example.cram
        S1	./S1.bam
        

  * provide two reference sequences with option '-f', print the associated reference for each BAM files. 
        
        $ samtools  samples  -h -f reference.fa -f example.fa S*.bam *.sam *.cram
        #SM	PATH	REFERENCE
        S1	S1.bam	reference.fa
        S2	S2.bam	reference.fa
        S3	S3.bam	reference.fa
        S4	S4.bam	reference.fa
        S5	S5.bam	reference.fa
        .	example.sam	example.fa
        S1	example.cram	example.fa
        

  * provide a list of reference sequences with option '-F', print the associated reference for each BAM files. 
        
        $ cat references.list
        reference.fa
        example.fa
        $ samtools  samples  -h -F references.list S*.bam *.sam *.cram
        #SM	PATH	REFERENCE
        S1	S1.bam	reference.fa
        S2	S2.bam	reference.fa
        S3	S3.bam	reference.fa
        S4	S4.bam	reference.fa
        S5	S5.bam	reference.fa
        .	example.sam	example.fa
        S1	example.cram	example.fa
        

## AUTHOR

Written by Pierre Lindenbaum from Institut du Thorax U1087, Nantes, France. 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-sort(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools sort – sorts SAM/BAM/CRAM files 

## SYNOPSIS

samtools [sort](samtools-sort.html) [_options_] [_in.sam_ |_in.bam_ |_in.cram_] 

## DESCRIPTION

Sort alignments by leftmost coordinates, by read name when **-n** or **-N** are used, by tag contents with **-t** , or a minimiser-based collation order with **-M**. An appropriate **@HD SO** sort order header tag will be added or an existing one updated if necessary, along with the **@HD SS** sub-sort header tag where appropriate. 

The sorted output is written to standard output by default, or to the specified file (_out.bam_) when **-o** is used. This command will also create temporary files _tmpprefix_**.**_%d_**.bam** as needed when the entire alignment data cannot fit into memory (as controlled via the **-m** option). 

Consider using **samtools collate** instead if you need name collated data without a full lexicographical sort. 

Note that if the sorted output file is to be indexed with **samtools index** , the default coordinate sort must be used. Thus the **-n** , **-N** and **-t** options are incompatible with **samtools index**. 

When sorting by minimiser (**-M**), the sort order for unplaced data is defined by the whole-read minimiser value and the offset into the read that this minimiser was observed. This produces small clusters (contig-like, but unaligned) and helps to improve compression with LZ algorithms. This can be improved by supplying a known reference to build a minimiser index (**-I** and **-w** options). 

## OPTIONS

**-l** _INT_
    

Set the desired compression level for the final output file, ranging from 0 (uncompressed) or 1 (fastest but minimal compression) to 9 (best compression but slowest to write), similarly to **gzip**(1)'s compression level setting. 

If **-l** is not used, the default compression level will apply. 

**-u**
    

Set the compression level to 0, for uncompressed output. This is a synonym for **-l 0**. 

**-m** _INT_
    

Approximately the maximum required memory per thread, specified either in bytes or with a **K** , **M** , or **G** suffix. [768 MiB] 

To prevent sort from creating a huge number of temporary files, it enforces a minimum value of 1M for this setting. 

**-n**
    

Sort by read names (i.e., the **QNAME** field) using an alpha-numeric ordering, rather than by chromosomal coordinates. The alpha-numeric or “natural” sort order detects runs of digits in the strings and sorts these numerically. Hence "a7b" appears before "a12b". Note this is not suitable where hexadecimal values are in use. Sets the header sub-sort (**@HD SS**) tag to **queryname:natural**. 

**-N**
    

Sort by read names (i.e., the **QNAME** field) using the lexicographical ordering, rather than by chromosomal coordinates. Unlike **-n** no detection of numeric components is used, instead relying purely on the ASCII value of each character. Hence "x12" comes before "x7" as "1" is before "7" in ASCII. This is a more appropriate name sort order where all digits in names are already zero-padded and/or hexadecimal values are being used. Sets the header sub-sort (**@HD SS**) tag to **queryname:lexicographical**. 

**-t** _TAG_
    

Sort first by the value in the alignment tag TAG, then by position or name (if also using **-n** or **-N**). 

**-M**
    

Sort unmapped reads (those in chromosome "*") by their sequence minimiser (Schleimer et al., 2003; Roberts et al., 2004), also reverse complementing as appropriate. This has the effect of collating some similar data together, improving the compressibility of the unmapped sequence. The minimiser kmer size is adjusted using the **-K** option. Note data compressed in this manner may need to be name collated prior to conversion back to fastq. 

Mapped sequences are sorted by chromosome and position. 

Files with at least one aligned record (being placed at a position on a chromosome) use the sort order "coordinate" with a sub-sort of "coordinate:minhash". Files entirely consisting of unaligned data use sort order "unsorted" with sub-sort "unsorted:minhash". 

**-R**
    

Do not use reverse strand with minimiser sort (only compatible with -M). 

**-K** _INT_
    

Sets the kmer size to be used in the **-M** option. [20] 

**-I** _FILE_
    

Build a minimiser index over _FILE_. The per-read minimisers produced by **-M** are no longer sorted by their numeric value, but by the reference coordinate this minimiser was found to come from (if found in the index). This further improves compression due to improved sequence similarity between sequences, albeit with a small CPU cost of building and querying the index. Specifying **-I** automatically implies **-M**. 

**-w** _INT_
    

Specifies the window size for building the minimiser index on the file specified in **-I**. This defaults to 100. It may be better to set this closer to 50 for short-read data sets (at a higher CPU and memory cost), or for more speed up to 1000 for long-read data sets. 

**-H**
    

Squashes base homopolymers down to a single base pair before constructing the minimiser. This is useful for instruments where the primary source of error is in the length of homopolymer. 

**-o** _FILE_
    

Write the final sorted output to _FILE_ , rather than to standard output. 

**-O** _FORMAT_
    

Write the final output as **sam** , **bam** , or **cram**. 

By default, samtools tries to select a format based on the **-o** filename extension; if output is to standard output or no format can be deduced, **bam** is selected. 

**-T** _PREFIX_
    

Write temporary files to _PREFIX_**.**_nnnn_**.bam,** or if the specified _PREFIX_ is an existing directory, to _PREFIX_**/samtools.**_mmm_**.**_mmm_**.tmp.**_nnnn_**.bam,** where _mmm_ is unique to this invocation of the **sort** command. 

By default, any temporary files are written alongside the output file, as _out.bam_**.tmp.**_nnnn_**.bam,** or if output is to standard output, in the current directory as **samtools.**_mmm_**.**_mmm_**.tmp.**_nnnn_**.bam.**

**-@**_INT_
    

Set number of sorting and compression threads. By default, operation is single-threaded. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

**\--template-coordinate**
    

Sorts by template-coordinate, whereby the sort order (@HD SO) is **unsorted** , the group order (GO) is **query** , and the sub-sort (SS) is **template-coordinate**. 

**Ordering Rules**

The following rules are used for ordering records. 

If option **-t** is in use, records are first sorted by the value of the given alignment tag, and then by position or name (if using **-n** or **-N**). For example, “-t RG” will make read group the primary sort key. The rules for ordering by tag are: 

  * Records that do not have the tag are sorted before ones that do. 
  * If the types of the tags are different, they will be sorted so that single character tags (type A) come before array tags (type B), then string tags (types H and Z), then numeric tags (types f and i). 
  * Numeric tags (types f and i) are compared by value. Note that comparisons of floating-point values are subject to issues of rounding and precision. 
  * String tags (types H and Z) are compared based on the binary contents of the tag using the C **strcmp**(3) function. 
  * Character tags (type A) are compared by binary character value. 
  * No attempt is made to compare tags of other types — notably type B array values will not be compared. 

When the **-n** or **-N** option is present, records are sorted by name. Historically samtools has used a “natural” ordering — i.e. sections consisting of digits are compared numerically while all other sections are compared based on their binary representation. This means “a1” will come before “b1” and “a9” will come before “a10”. However this alpha-numeric sort can be confused by runs of hexadecimal digits. The newer **-N** option adds a simpler lexicographical based name collation which does not attempt any numeric comparisons and may be more appropriate for some data sets. Note care must be taken when using **samtools merge** to ensure all files are using the same collation order. Records with the same name will be ordered according to the values of the READ1 and READ2 flags (see **samtools flags**). When that flag is also equal, ties are resolved with primary alignments first, then SUPPLEMENTARY, SECONDARY, and finally SUPPLEMENTARY plus SECONDARY. Any remaining ties are reported in the same order as the input data. 

When the **\--template-coordinate** option is in use, the reads are sorted by: 

The earlier unclipped 5' coordinate of the template. 

The higher unclipped 5' coordinate of the template. 

The library (from the read group). 

The molecular identifier (MI tag if present). 

The read name. 

If unpaired, or if R1 has the lower coordinates of the pair. 

When none of the above options are in use, reads are sorted by reference (according to the order of the @SQ header records), then by position in the reference, and then by the REVERSE flag. 

**Note**

Historically **samtools sort** also accepted a less flexible way of specifying the final and temporary output filenames: 

samtools sort [**-f**] [**-o**] _in.bam out.prefix_

This has now been removed. The previous _out.prefix_ argument (and **-f** option, if any) should be changed to an appropriate combination of **-T** _PREFIX_ and **-o** _FILE_. The previous **-o** option should be removed, as output defaults to standard output. 

## AUTHOR

Written by Heng Li from the Sanger Institute with numerous subsequent modifications. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-collate_](samtools-collate.html) (1), [_samtools-merge_](samtools-merge.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-split(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools split – splits a file by read group. 

## SYNOPSIS

samtools [split](samtools-split.html) [_options_] _merged.sam_ |_merged.bam_ |_merged.cram_

## DESCRIPTION

Splits a file by read group, or a specified tag, producing one or more output files matching a common prefix (by default based on the input filename). 

Unless the **-d** option is used, the file will be split according to the **@RG** tags listed in the header. Records without an RG tag or with an RG tag undefined in the header will cause the program to exit with an error unless the **-u** option is used. 

RG values defined in the header but with no records will produce an output file only containing a header. 

If the **-d** _TAG_ option is used, the file will be split on the value in the given aux tag. Only string (type **Z**) and integer (type **i** in SAM, plus equivalents in BAM/CRAM) tags are currently supported. Unless the **-u** option is used, the program will exit with an error if it finds a record without the given tag. 

Note that attempting to split on a tag with high cardinality may result in the creation of a large number of output files. To prevent this, the **-M** option can be used to set a limit on the number of splits made. 

Using **-d RG** behaves in a similar way to the default (without **-d**), opening an output file for each **@RG** line in the header. However, unlike the default, new output files will be opened for any RG tags found in the alignment records irrespective of if they have a matching header **@RG** line. 

The **-u** option may be used to specify the output filename for any records with a missing or unrecognised tag. This option will always write out a file even if there are no records. 

Output format defaults to BAM. For SAM or CRAM then either set the format with **\--output-fmt** or use **-f** to set the file extension e.g. **-f %*_%#.sam**. 

## OPTIONS

**-u** _FILE1_
    

Put reads with no tag or an unrecognised tag into _FILE1_

**-h** _FILE2_
    

Use the header from _FILE2_ when writing the file given in the _-u_ option. This header completely replaces the one from the input file. It must be compatible with the input file header, which means it must have the same number of references listed in the @SQ lines and the references must be in the same order and have the same lengths. 

**-f** _STRING_
    

Output filename format string (see below) ["%*_%#.%."] 

**-d** _TAG_
    

Split reads by TAG value into distinct files. Only the TAG key must be supplied with the option. The value of the TAG has to be a string (i.e. **key:Z:value**) or an integer (**key:i:value**). 

Using this option changes the default filename format string to "%*_%!.%.", so that tag values appear in the output file names. This can be overridden by using the **-f** option. 

**-p** _NUMBER_
    

Pad numeric values in **%#** and **%!** format expansions to this many digits using leading zeros. For **%!** , only integer tag values will be padded. String tag values will be left unchanged, even if the value only includes digits. 

**-M,--max-split** _NUM_
    

Limit the number of files created by the **-d** option to _NUM_ (default 100). This prevents accidents where trying to split on a tag with high cardinality could result in the creation of a very large number of output files. Once the file limit is reached, any tag values not already seen will be treated as unmatched and the program will exit with an error unless the **-u** option is in use. 

If desired, the limit can be removed using **-M -1** , although in practice the number of outputs will still be restricted by system limits on the number of files that can be open at once. 

If splitting by read group, and the read group count in the header is higher than the requested limit then the limit will be raised to match. 

**-v**
    

Verbose output 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

Format string expansions:  **%%**|  %  
---|---  
**%***|  basename  
**%#**|  index (of @RG in the header, or count of TAG values seen so far)  
**%!**|  @RG ID or TAG value  
**%.**|  output format filename extension  
  
**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

## AUTHOR

Written by Martin Pollard from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-addreplacerg_](samtools-addreplacerg.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-stats(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools stats – produces comprehensive statistics from alignment file 

## SYNOPSIS

samtools [stats](samtools-stats.html) [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

## DESCRIPTION

samtools stats collects statistics from BAM files and outputs in a text format. The output can be visualized graphically using plot-bamstats. 

A summary of output sections is listed below, followed by more detailed descriptions. 

**CHK**|  Checksum  
---|---  
**SN**|  Summary numbers  
**FFQ**|  First fragment qualities  
**LFQ**|  Last fragment qualities  
**GCF**|  GC content of first fragments  
**GCL**|  GC content of last fragments  
**GCC**|  ACGT content per cycle  
**GCT**|  ACGT content per cycle, read oriented  
**FBC**|  ACGT content per cycle for first fragments only  
**FTC**|  ACGT raw counters for first fragments  
**LBC**|  ACGT content per cycle for last fragments only  
**LTC**|  ACGT raw counters for last fragments  
**BCC**|  ACGT content per cycle for BC barcode  
**CRC**|  ACGT content per cycle for CR barcode  
**OXC**|  ACGT content per cycle for OX barcode  
**RXC**|  ACGT content per cycle for RX barcode  
**MPC**|  Mismatch distribution per cycle  
**QTQ**|  Quality distribution for BC barcode  
**CYQ**|  Quality distribution for CR barcode  
**BZQ**|  Quality distribution for OX barcode  
**QXQ**|  Quality distribution for RX barcode  
**IS**|  Insert sizes  
**RL**|  Read lengths  
**FRL**|  Read lengths for first fragments only  
**LRL**|  Read lengths for last fragments only  
**MAPQ**|  Mapping qualities  
**ID**|  Indel size distribution  
**IC**|  Indels per cycle  
**COV**|  Coverage (depth) distribution  
**GCD**|  GC-depth  
**RFS**|  Reference Statistics  
  
The "cycle" terminology used here originates from the Illumina instruments, but it is interpreted more generally as the Nth base reported in the original read orientation (starting from 1). 

Not all sections will be reported as some depend on the data being coordinate sorted while others are only present when specific barcode tags are in use. 

Some of the statistics are collected for “first” or “last” fragments. Records are put into these categories using the PAIRED (0x1), READ1 (0x40) and READ2 (0x80) flag bits, as follows: 

  * Unpaired reads (i.e. PAIRED is not set) are all “first” fragments. For these records, the READ1 and READ2 flags are ignored. 
  * Reads where PAIRED and READ1 are set, and READ2 is not set are “first” fragments. 
  * Reads where PAIRED and READ2 are set, and READ1 is not set are “last” fragments. 
  * Reads where PAIRED is set and either both READ1 and READ2 are set or neither is set are not counted in either category. 

Information on the meaning of the flags is given in the SAM specification document <<https://samtools.github.io/hts-specs/SAMv1.pdf>>. 

The CHK row contains distinct CRC32 checksums of read names, sequences and quality values. The checksums are computed per alignment record and summed, meaning the checksum does not change if the input file has the sort-order changed. NOTE: Checksum calculation for quality values was modified and quality checksum value will be different from that generated using versions up to 1.21. The SN section contains a series of counts, percentages, and averages, in a similar style to **samtools flagstat** , but more comprehensive. 

**raw total sequences** \- total number of reads in a file, excluding supplementary and secondary reads. Same number reported by **samtools view -c -F 0x900**. 

**filtered sequences** \- number of discarded reads when using -f or -F option. 

**sequences** \- number of processed reads. 

**is sorted** \- flag indicating whether the file is coordinate sorted (1) or not (0). 

**1st fragments** \- number of **first** fragment reads (flags 0x01 not set; or flags 0x01 and 0x40 set, 0x80 not set). 

**last fragments** \- number of **last** fragment reads (flags 0x01 and 0x80 set, 0x40 not set). 

**reads mapped** \- number of reads, paired or single, that are mapped (flag 0x4 or 0x8 not set). 

**reads mapped and paired** \- number of mapped paired reads (flag 0x1 is set and flags 0x4 and 0x8 are not set). 

**reads unmapped** \- number of unmapped reads (flag 0x4 is set). 

**reads properly paired** \- number of mapped paired reads with flag 0x2 set. 

**paired** \- number of paired reads, mapped or unmapped, that are neither secondary nor supplementary (flag 0x1 is set and flags 0x100 (256) and 0x800 (2048) are not set). 

**reads duplicated** \- number of duplicate reads (flag 0x400 (1024) is set). 

**reads MQ0** \- number of mapped reads with mapping quality 0. 

**reads QC failed** \- number of reads that failed the quality checks (flag 0x200 (512) is set). 

**non-primary alignments** \- number of secondary reads (flag 0x100 (256) set). 

**supplementary alignments** \- number of supplementary reads (flag 0x800 (2048) set). 

**total length** \- number of processed bases from reads that are neither secondary nor supplementary (flags 0x100 (256) and 0x800 (2048) are not set). 

**total first fragment length** \- number of processed bases that belong to **first** fragments. 

**total last fragment length** \- number of processed bases that belong to **last** fragments. 

**bases mapped** \- number of processed bases that belong to **reads mapped.**

**bases mapped (cigar)** \- number of mapped bases filtered by the CIGAR string corresponding to the read they belong to. Only alignment matches(M), inserts(I), sequence matches(=) and sequence mismatches(X) are counted. 

**bases trimmed** \- number of bases trimmed by bwa, that belong to non secondary and non supplementary reads. Enabled by -q option. 

**bases duplicated** \- number of bases that belong to **reads duplicated.**

**mismatches** \- number of mismatched bases, as reported by the NM tag associated with a read, if present. 

**error rate** \- ratio between **mismatches** and **bases mapped (cigar).**

**average length** \- ratio between **total length** and **sequences.**

**average first fragment length** \- ratio between **total first fragment length** and **1st fragments.**

**average last fragment length** \- ratio between **total last fragment length** and **last fragments.**

**maximum length** \- length of the longest read (includes hard-clipped bases). 

**maximum first fragment length** \- length of the longest **first** fragment read (includes hard-clipped bases). 

**maximum last fragment length** \- length of the longest **last** fragment read (includes hard-clipped bases). 

**average quality** \- ratio between the sum of base qualities and **total length.**

**insert size average** \- the average absolute template length for paired and mapped reads. 

**insert size standard deviation** \- standard deviation for the average template length distribution. 

**inward oriented pairs** \- number of paired reads with flag 0x40 (64) set and flag 0x10 (16) not set or with flag 0x80 (128) set and flag 0x10 (16) set. 

**outward oriented pairs** \- number of paired reads with flag 0x40 (64) set and flag 0x10 (16) set or with flag 0x80 (128) set and flag 0x10 (16) not set. 

**pairs with other orientation** \- number of paired reads that don't fall in any of the above two categories. 

**pairs on different chromosomes** \- number of pairs where one read is on one chromosome and the pair read is on a different chromosome. 

**percentage of properly paired reads** \- percentage of **reads properly paired** out of **sequences.**

**bases inside the target** \- number of bases inside the target region(s) (when a target file is specified with -t option). 

**percentage of target genome with coverage > VAL** \- percentage of target bases with a coverage larger than VAL. By default, VAL is 0, but a custom value can be supplied by the user with -g option. 

The FFQ and LFQ sections report the quality distribution per first/last fragment and per cycle number. They have one row per cycle (reported as the first column after the FFQ/LFQ key) with remaining columns being the observed integer counts per quality value, starting at quality 0 in the left-most row and ending at the largest observed quality. Thus each row forms its own quality distribution and any cycle specific quality artefacts can be observed. 

GCF and GCL report the total GC content of each fragment, separated into first and last fragments. The columns show the GC percentile (between 0 and 100) and an integer count of fragments at that percentile. 

GCC, FBC and LBC report the nucleotide content per cycle either combined (GCC) or split into first (FBC) and last (LBC) fragments. The columns are cycle number (integer), and percentage counts for A, C, G, T, N and other (typically containing ambiguity codes) normalised against the total counts of A, C, G and T only (excluding N and other). 

GCT offers a similar report to GCC, but whereas GCC counts nucleotides as they appear in the SAM output (in reference orientation), GCT takes into account whether a nucleotide belongs to a reverse complemented read and counts it in the original read orientation. If there are no reverse complemented reads in a file, the GCC and GCT reports will be identical. 

FTC and LTC report the total numbers of nucleotides for first and last fragments, respectively. The columns are the raw counters for A, C, G, T and N bases. 

MPC reports the number of mismatches per cycle and per quality value. The MPC statistics are only included when a reference is specified via the **-r** option. There is one row per cycle number. Each row includes the cycle number, the number of N bases (not counted in the per-qual columns), followed by one column per quality value (starting at zero and incrementing by one each time) listing the number of non-N mismatches with that quality. A mismatch is defined as an ACGT sequence base mismatching an ACGT reference base. Ambiguity codes are ignored (except for sequence N as mentioned above, which is counted even when the reference is also N). 

BCC, CRC, OXC and RXC are the barcode equivalent of GCC, showing nucleotide content for the barcode tags BC, CR, OX and RX respectively. Their quality values distributions are in the QTQ, CYQ, BZQ and QXQ sections, corresponding to the BC/QT, CR/CY, OX/BZ and RX/QX SAM format sequence/quality tags. These quality value distributions follow the same format used in the FFQ and LFQ sections. All these section names are followed by a number (1 or 2), indicating that the stats figures below them correspond to the first or second barcode (in the case of dual indexing). Thus, these sections will appear as BCC1, CRC1, OXC1 and RXC1, accompanied by their quality correspondents QTQ1, CYQ1, BZQ1 and QXQ1. If a separator is present in the barcode sequence (usually a hyphen), indicating dual indexing, then sections ending in "2" will also be reported to show the second tag statistics (e.g. both BCC1 and BCC2 are present). 

IS reports insert size distributions with one row per size, reported in the first column, with subsequent columns for the frequency of total pairs, inward oriented pairs, outward orient pairs and other orientation pairs. The **-i** option specifies the maximum insert size reported. 

RL reports the distribution for all read lengths, with one row per observed length (up to the maximum specified by the **-l** option). Columns are read length and frequency. FRL and LRL contains the same information separated into first and last fragments. 

MAPQ reports the mapping qualities for the mapped reads, ignoring the duplicates, supplementary, secondary and failing quality reads. 

ID reports the distribution of indel sizes, with one row per observed size. The columns are size, frequency of insertions at that size and frequency of deletions at that size. 

IC reports the frequency of indels occurring per cycle, broken down by both insertion / deletion and by first / last read. Note for multi-base indels this only counts the first base location. Columns are cycle, number of insertions in first fragments, number of insertions in last fragments, number of deletions in first fragments, and number of deletions in last fragments. 

COV reports a distribution of the alignment depth per covered reference site. For example an average depth of 50 would ideally result in a normal distribution centred on 50, but the presence of repeats or copy-number variation may reveal multiple peaks at approximate multiples of 50. The first column is an inclusive coverage range in the form of **[**_min_**-**_max_**]**. The next columns are a repeat of the _max_ imum portion of the depth range (now as a single integer) and the frequency that depth range was observed. The minimum, maximum and range step size are controlled by the **-c** option. Depths above and below the minimum and maximum are reported with ranges **[ <**_min_**]** and **[**_max_**<]**. 

GCD reports the GC content of the reference data aligned against per alignment record, with one row per observed GC percentage reported as the first column and sorted on this column. The second column is a total sequence percentile, as a running total (ending at 100%). The first and second columns may be used to produce a simple distribution of GC content. Subsequent columns list the coverage depth at 10th, 25th, 50th, 75th and 90th GC percentiles for this specific GC percentage, revealing any GC bias in mapping. These columns are averaged depths, so are floating point with no maximum value. 

RFS reports statistics of the reference data. The first line gives the overall statistics for the reference. This comprises of the total number of targets in the input file and the number covered; followed by the average GC content, minimum, maximum, average and total lengths of targets in the report. The second and subsequent lines contain the statistics for each target. Targets are regions either specified on the command line or given in the target file (**-t** option). If no regions are chosen then all the reference data is used. Each line gives the name of target, length, GC content and number of unknown bases. For the GC content and the number of unknown bases a reference file is required (**-t** option), otherwise the value is set to -1. The lengths are from the region specification and from file header. 

## OPTIONS

**-c, --coverage** _MIN_**,**_MAX_**,**_STEP_
    

Set coverage distribution to the specified range (MIN, MAX, STEP all given as integers) [1,1000,1] 

**-d, --remove-dups**
    

Exclude from statistics reads marked as duplicates 

**-f, --required-flag** _STR_**|**_INT_
    

Required flag, 0 for unset. See also `samtools flags` [0] 

**-F, --filtering-flag** _STR_**|**_INT_
    

Filtering flag, 0 for unset. See also `samtools flags` [0] 

**\--GC-depth** _FLOAT_
    

the size of GC-depth bins (decreasing bin size increases memory requirement) [2e4] 

**-h, --help**
    

This help message 

**-i, --insert-size** _INT_
    

Maximum insert size [8000] 

**-I, --id** _STR_
    

Include only listed read group or sample name [] 

**-l, --read-length** _INT_
    

Include in the statistics only reads with the given read length [-1] 

**-m, --most-inserts** _FLOAT_
    

Report only the main part of inserts [0.99] 

**-P, --split-prefix** _STR_
    

A path or string prefix to prepend to filenames output when creating categorised statistics files with **-S** /**\--split**. [input filename] 

**-q, --trim-quality** _INT_
    

The BWA trimming parameter [0] 

**-r, --ref-seq** _FILE_
    

Reference sequence (required for GC-depth and mismatches-per-cycle calculation). [] 

**-S, --split** _TAG_
    

In addition to the complete statistics, also output categorised statistics based on the tagged field _TAG_ (e.g., use **\--split RG** to split into read groups). 

Categorised statistics are written to files named <_prefix_ >_<_value_ >.bamstat, where _prefix_ is as given by **\--split-prefix** (or the input filename by default) and _value_ has been encountered as the specified tagged field's value in one or more alignment records. 

**-t, --target-regions** _FILE_
    

Do stats in these regions only. Tab-delimited file chr,from,to, 1-based, inclusive. [] 

**-x, --sparse**
    

Suppress outputting IS rows where there are no insertions. 

**-p, --remove-overlaps**
    

Remove overlaps of paired-end reads from coverage and base count computations. 

**-g, --cov-threshold** _INT_
    

Only bases with coverage above this value will be included in the target percentage computation [0] 

**-X**
    

If this option is set, it will allows user to specify customized index file location(s) if the data folder does not contain any index file. Example usage: samtools stats [options] -X /data_folder/data.bam /index_folder/data.bai chrM:1-10 

**-@, --threads** _INT_
    

Number of input/output compression threads to use in addition to main thread [0]. 

**\--ref-stats**
    

Create statistics on reference data. 

**\--ref-stats-chunk** _INT_
    

Number of reference bases to read at a time, in Mbs, for reference statistics [1]. 

## AUTHOR

Written by Petr Danacek with major modifications by Nicholas Clarke, Martin Pollard, Josh Randall, and Valeriu Ohan, all from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-flagstat_](samtools-flagstat.html) (1), [_samtools-idxstats_](samtools-idxstats.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-targetcut(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools targetcut – cut fosmid regions (for fosmid pool only) 

## SYNOPSIS

samtools [targetcut](samtools-targetcut.html) [**-Q** _minBaseQ_] [**-i** _inPenalty_] [**-0** _em0_] [**-1** _em1_] [**-2** _em2_] [**-f** _ref_] _in.bam_

## DESCRIPTION

This command identifies target regions by examining the continuity of read depth, computes haploid consensus sequences of targets and outputs a SAM with each sequence corresponding to a target. When option **-f** is in use, BAQ will be applied. This command is **only** designed for cutting fosmid clones from fosmid pool sequencing [Ref. Kitzman et al. (2010)]. 

## OPTIONS

**-Q** _minBaseQ_
    

Ignore bases with quality less than _minBaseQ_. 

**-i** _inPenalty_
    

Penalty for in state transition. 

**-0** _em0_
    

Emission score 0. 

**-1** _em1_
    

Emission score 1. 

**-2** _em2_
    

Emission score 2. 

**-f** _ref_
    

Reference FASTA file. 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-tview(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools tview – display alignments in a curses-based interactive viewer. 

## SYNOPSIS

**samtools tview** [**-p** _chr:pos_] [**-s** _STR_] [**-d** _display_] _in.sorted.bam_ [_ref.fasta_] 

## DESCRIPTION

Text alignment viewer (based on the ncurses library). In the viewer, press `?' for help and press `g' to check the alignment start from a region in the format like `chr10:10,000,000' or `=10,000,000' when viewing the same reference sequence. 

The top line shows the reference sequence, or '**N** 's if unknown. Underneath this is the consensus, derived from the sequence alignments. Below the consensus the sequence alignment records are shown. Uppercase and lowercase is used to distinguish the sequence strand, with uppercase being the top/forward strand. 

When the reference is known, both consensus and alignment record sequences are displayed in a dot-notation where a matching character is shown as '**.** ' (forward strand) or '**,** ' (reverse strand) and only mismatching bases and missing bases are shown. This mode can be toggled with the "." command. 

## OPTIONS

**-d** _display_
    

Output as (H)tml, (C)urses or (T)ext. 

The width of generated text is controlled by the COLUMNS environment variable or the **-w** option for non-curses outputs. Note this may be a local shell variable so it may need exporting first or specifying on the command line prior to the command. For example 
    
    
    export COLUMNS ; samtools tview -d T -p 1:234567 in.bam
    

**-p** _chr:pos_
    

Go directly to this position 

**-s** _STR_
    

Display only alignments from this sample or read group. **STR** must match either an **ID** or **SM** field in an **@RG** header record. For example 
    
    
    samtools tview -p chr20:10M -s NA12878 grch38.fa
    

**-w** _INT_
    

Specifies the display width when using the HTML or Text output modes. 

**-X**
    

If this option is set, it will allows user to specify customized index file location(s) if the data folder does not contain any index file. Example usage: samtools tview [options] -X </data_folder/data.bam> [/index_folder/index.bai] [ref.fasta] 

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools-view(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools view – views and converts SAM/BAM/CRAM files 

## SYNOPSIS

**samtools view** [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

## DESCRIPTION

With no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header). 

You may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file (in BAM or CRAM format). 

The **-b** , **-C** , **-1** , **-u** , **-h** , **-H** , and **-c** options change the output format from the default of headerless SAM, and the **-o** and **-U** options set the output file name(s). 

The **-t** and **-T** options provide additional reference data. One of these two options is required when SAM input does not contain @SQ headers, and the **-T** option is required whenever writing CRAM output. 

The **-L** , **-M** , **-N** , **-r** , **-R** , **-n** , **-d** , **-D** , **-s** , **-q** , **-l** , **-m** , **-f** , **-F** , **-G** , and **\--rf** options filter the alignments that will be included in the output to only those alignments that match certain criteria. 

The **-p** , option sets the UNMAP flag on filtered alignments then writes them to the output file. 

The **-x** , **-B** , **\--add-flags** , and **\--remove-flags** options modify the data which is contained in each alignment. 

The **-X** option can be used to allow user to specify customized index file location(s) if the data folder does not contain any index file. See **EXAMPLES** section for sample of usage. 

Finally, the **-@** option can be used to allocate additional threads to be used for compression, and the **-?** option requests a long help message. 

**REGIONS:**
    

Regions can be specified as: RNAME[:STARTPOS[-ENDPOS]] and all position coordinates are 1-based. 

Important note: when multiple regions are given, some alignments may be output multiple times if they overlap more than one of the specified regions. 

Examples of region specifications: 

**chr1**
    

Output all alignments mapped to the reference sequence named `chr1' (i.e. @SQ SN:chr1). 

**chr2:1000000**
    

The region on chr2 beginning at base position 1,000,000 and ending at the end of the chromosome. 

**chr3:1000-2000**
    

The 1001bp region on chr3 beginning at base position 1,000 and ending at base position 2,000 (including both end positions). 

**'*'**
    

Output the unmapped reads at the end of the file. (This does not include any unmapped reads placed on a reference sequence alongside their mapped mates.) 

**.**
    

Output all alignments. (Mostly unnecessary as not specifying a region at all has the same effect.) 

## OPTIONS

**-b** , **\--bam**
    

Output in the BAM format. 

**-C** , **\--cram**
    

Output in the CRAM format (requires -T). 

**-1** , **\--fast**
    

Enable fast compression. This also changes the default output format to BAM, but this can be overridden by the explicit format options or using a filename with a known suffix. 

**-u** , **\--uncompressed**
    

Output uncompressed data. This also changes the default output format to BAM, but this can be overridden by the explicit format options or using a filename with a known suffix. 

This option saves time spent on compression/decompression and is thus preferred when the output is piped to another samtools command. 

**-h** , **\--with-header**
    

Include the header in the output. 

**-H** , **\--header-only**
    

Output the header only. 

**\--no-header**
    

When producing SAM format, output alignment records but not headers. This is the default; the option can be used to reset the effect of **-h** /**-H**. 

**-c** , **\--count**
    

Instead of printing the alignments, only count them and print the total number. All filter options, such as **-f** , **-F** , and **-q** , are taken into account. The **-p** option is ignored in this mode. 

**\--save-counts** _FILE_
    

Save data on the number of records processed, accepted and rejected by any filter options to _FILE_. The data is stored in JSON format. The counts only include records that are processed through the filtering options. Any records skipped while iterating over regions will not be included, so the number processed may be less than the total number of records in the file. If used with the **\--fetch-pairs** option, counts will be given for records processed during the second pass over the data. 

**-?** , **\--help**
    

Output long help and exit immediately. 

**-o** _FILE_**, --output** _FILE_
    

Output to _FILE [stdout]._

**-U** _FILE_**, --unoutput** _FILE_**, --output-unselected** _FILE_
    

Write alignments that are _not_ selected by the various filter options to _FILE_. When this option is used, all alignments (or all alignments intersecting the _regions_ specified) are written to either the output file or this file, but never both. 

**-p** , **\--unmap**
    

Set the UNMAP flag on alignments that are not selected by the filter options. These alignments are then written to the normal output. This is not compatible with **-U**. 

**-t** _FILE_**, --fai-reference** _FILE_
    

A tab-delimited _FILE_. Each line must contain the reference name in the first column and the length of the reference in the second column, with one line for each distinct reference. Any additional fields beyond the second column are ignored. This file also defines the order of the reference sequences in sorting. If you run: `samtools faidx <ref.fa>', the resulting index file _< ref.fa>.fai_ can be used as this _FILE_. 

**-T** _FILE_**, --reference** _FILE_
    

A FASTA format reference _FILE_ , optionally compressed by **bgzip** and ideally indexed by **samtools** **faidx**. If an index is not present one will be generated for you, if the reference file is local. 

If the reference file is not local, but is accessed instead via an https://, s3:// or other URL, the index file will need to be supplied by the server alongside the reference. It is possible to have the reference and index files in different locations by supplying both to this option separated by the string "##idx##", for example: 

**-T ftp://x.com/ref.fa##idx##ftp://y.com/index.fa.fai**

However, note that only the location of the reference will be stored in the output file header. If this method is used to make CRAM files, the cram reader may not be able to find the index, and may not be able to decode the file unless it can get the references it needs using a different method. 

**-L** _FILE_**, --target-file** _FILE_**, --targets-file** _FILE_
    

Only output alignments overlapping the input BED _FILE_ [null]. 

**-M** , **\--use-index**
    

Use the multi-region iterator on the union of a BED file and command-line region arguments. This avoids re-reading the same regions of files so can sometimes be much faster. Note this also removes duplicate sequences. Without this a sequence that overlaps multiple regions specified on the command line will be reported multiple times. The usage of a BED file is optional and its path has to be preceded by **-L** option. 

**\--region-file** _FILE_**, --regions-file** _FILE_
    

Use an index and multi-region iterator to only output alignments overlapping the input BED _FILE_. Equivalent to **-M -L** _FILE_ or **\--use-index --target-file** _FILE_. 

**-N** _FILE_**, --qname-file** _FILE_
    

Output only alignments with read names listed in _FILE_. If _FILE_ starts with **^** then the operation is negated and only outputs alignment with read groups not listed in _FILE_. It is not permissible to mix both the filter-in and filter-out style syntax in the same command. 

**-r** _STR_**, --read-group** _STR_
    

Output alignments in read group _STR_ [null]. Note that records with no **RG** tag will also be output when using this option. This behaviour may change in a future release. 

**-R** _FILE_**, --read-group-file** _FILE_
    

Output alignments in read groups listed in _FILE_ [null]. If _FILE_ starts with **^** then the operation is negated and only outputs alignment with read names not listed in _FILE_. It is not permissible to mix both the filter-in and filter-out style syntax in the same command. Note that records with no **RG** tag will also be output when using this option. This behaviour may change in a future release. 

**-n** , **\--exclude-no-read-group**
    

Do not output alignments that have no read group. 

**-d** _STR1[:STR2]_**, --tag** _STR1[:STR2]_
    

Only output alignments with tag _STR1_ and associated value _STR2_ , which can be a string or an integer [null]. The value can be omitted, in which case only the tag is considered. 

Note that this option does not specify a tag type. For example, use **-d XX:42** to select alignments with an **XX:i:42** field, not **-d XX:i:42**. 

**-D** _STR:FILE_**, --tag-file** _STR:FILE_
    

Only output alignments with tag _STR_ and associated values listed in _FILE_ [null]. 

**-q** _INT_**, --min-MQ** _INT_
    

Skip alignments with MAPQ smaller than _INT_ [0]. 

**-l** _STR_**, --library** _STR_
    

Only output alignments in library _STR_ [null]. 

**-m** _INT_**, --min-qlen** _INT_
    

Only output alignments with number of CIGAR bases consuming query sequence ≥ _INT_ [0] 

**-e** _STR_**, --expr** _STR_
    

Only include alignments that match the filter expression _STR_. The syntax for these expressions is described in the main samtools(1) man page under the FILTER EXPRESSIONS heading. 

**-f** _FLAG_**, --require-flags** _FLAG_
    

Only output alignments with all bits set in _FLAG_ present in the FLAG field. _FLAG_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. 

For a list of flag names see _samtools-flags_(1). 

**-F** _FLAG_**, --excl-flags** _FLAG_**, --exclude-flags** _FLAG_
    

Do not output alignments with any bits set in _FLAG_ present in the FLAG field. _FLAG_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. 

**\--rf** _FLAG_**, --incl-flags** _FLAG_**, --include-flags** _FLAG_
    

Only output alignments with any bit set in _FLAG_ present in the FLAG field. _FLAG_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. 

**-G** _FLAG_
    

Do not output alignments with all bits set in _INT_ present in the FLAG field. This is the opposite of _-f_ such that _-f12 -G12_ is the same as no filtering at all. _FLAG_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. 

**-x** _STR_**, --remove-tag** _STR_
    

Read tag(s) to exclude from output (repeatable) [null]. This can be a single tag or a comma separated list. Alternatively the option itself can be repeated multiple times. 

If the list starts with a `^' then it is negated and treated as a request to remove all tags except those in _STR_. The list may be empty, so **-x ^** will remove all tags. 

Note that tags will only be removed from reads that pass filtering. 

**\--keep-tag** _STR_
    

This keeps _only_ tags listed in _STR_ and is directly equivalent to **\--remove-tag ^**_STR_. Specifying an empty list will remove all tags. If both **\--keep-tag** and **\--remove-tag** are specified then **\--keep-tag** has precedence. 

Note that tags will only be removed from reads that pass filtering. 

**-B** , **\--remove-B**
    

Collapse the backward CIGAR operation. 

**\--add-flags** _FLAG_
    

Adds flag(s) to read. _FLAG_ can be specified in hex by beginning with `0x' (i.e. /^0x[0-9A-F]+/), in octal by beginning with `0' (i.e. /^0[0-7]+/), as a decimal number not beginning with '0' or as a comma-separated list of flag names. 

**\--remove-flags** _FLAG_
    

Remove flag(s) from read. _FLAG_ is specified in the same way as with the **\--add-flags** option. 

**\--subsample** _FLOAT_
    

Output only a proportion of the input alignments, as specified by 0.0 ≤ _FLOAT_ ≤ 1.0, which gives the fraction of templates/pairs to be kept. This subsampling acts in the same way on all of the alignment records in the same template or read pair, so it never keeps a read but not its mate. 

**\--subsample-seed** _INT_
    

Subsampling seed used to influence _which_ subset of reads is kept. When subsampling data that has previously been subsampled, be sure to use a different seed value from those used previously; otherwise more reads will be retained than expected. [0] 

**-s** _FLOAT_
    

Subsampling shorthand option: **-s** _INT_**.**_FRAC_ is equivalent to **\--subsample-seed** _INT_**\--subsample** 0._FRAC_. 

**-@**_INT_**, --threads** _INT_
    

Number of BAM compression threads to use in addition to main thread [0]. 

**-P** , **\--fetch-pairs**
    

Retrieve pairs even when the mate is outside of the requested region. Enabling this option also turns on the multi-region iterator (**-M**). A region to search must be specified, either on the command-line, or using the **-L** option. The input file must be an indexed regular file. 

This option first scans the requested region, using the **RNEXT** and **PNEXT** fields of the records that have the PAIRED flag set and pass other filtering options to find where paired reads are located. These locations are used to build an expanded region list, and a set of **QNAME** s to allow from the new regions. It will then make a second pass, collecting all reads from the originally-specified region list together with reads from additional locations that match the allowed set of **QNAME** s. Any other filtering options used will be applied to all reads found during this second pass. 

As this option links reads using **RNEXT** and **PNEXT** , it is important that these fields are set accurately. Use 'samtools fixmate' to correct them if necessary. 

Note that this option does not work with the **-c, --count** ; **-U, --output-unselected** ; or **-p, --unmap** options. 

**-S**
    

Ignored for compatibility with previous samtools versions. Previously this option was required if input was in SAM format, but now the correct format is automatically detected by examining the first few characters of input. 

**-X** , **\--customized-index**
    

Include customized index file as a part of arguments. See **EXAMPLES** section for sample of usage. 

**-z** _FLAGs_**, --sanitize** _FLAGs_
    

Perform some sanity checks on the state of SAM record fields, fixing up common mistakes made by aligners. These include soft-clipping alignments when they extend beyond the end of the reference, marking records as unmapped when they have reference * or position 0, and ensuring unmapped alignments have no CIGAR or mapping quality for unmapped alignments and no MD, NM, CG or SM tags. 

_FLAGs_ is a comma-separated list of keywords chosen from the following list. 

unmap
    

The UNMAPPED BAM flag. This is set for reads with position <= 0, reference name "*" or reads starting beyond the end of the reference. Note CIGAR "*" is permitted for mapped data so does not trigger this. 

pos
    

Position and reference name fields. These may be cleared when a sequence is unmapped due to the coordinates being beyond the end of the reference. Selecting this may change the sort order of the file, so it is not a part of the **on** compound argument. 

mqual
    

Mapping quality. This is set to zero for unmapped reads. 

cigar
    

Modifies CIGAR fields, either by adding soft-clips for reads that overlap the end of the reference or by clearing it for unmapped reads. 

cigdup
    

Canonicalises CIGAR by collapsing neighbouring elements with identical opcodes (provided the length field does not extend beyond 28-bits which is problematic for BAM). So for example 2M 3M becomes 5M, with spaces added for clarity only. 

cigarx
    

Replaces CIGAR "=" and "X" codes with "M". While "=" and "X" are valid codes, they are not supported by CRAM so this can aid validation and also improve support by some third party tools that do not cope with "=" and "X". Note this implicitly also enables **cigdup** so 10=1X9= becomes 10M1M9M which then becomes 20M. 

aux
    

For unmapped data, some auxiliary fields are meaningless and will be removed. These include NM, MD, CG and SM. 

off
    

Perform no sanity fixing. This is the default 

on
    

Sanitize data in a way that guarantees the same sort order. This is everything except for **pos** as it cannot be checked and **cigarx** as it is not erroneous data. 

all
    

All sanitizing options except **cigarx** , including **pos**. Combine with **all,cigarx** to perform the "=" and "X" replacement too. 

**\--no-PG**
    

Do not add a @PG line to the header of the output file. 

## EXAMPLES

  * Import SAM to BAM when **@SQ** lines are present in the header: 
        
        samtools view -bo aln.bam aln.sam
        

If **@SQ** lines are absent: 
        
        samtools faidx ref.fa
        samtools view -bt ref.fa.fai -o aln.bam aln.sam
        

where _ref.fa.fai_ is generated automatically by the **faidx** command. 

  * Convert a BAM file to a CRAM file using a local reference sequence. 
        
        samtools view -C -T ref.fa -o aln.cram aln.bam
        

  * Convert a BAM file to a CRAM with NM and MD tags stored verbatim rather than calculating on the fly during CRAM decode, so that mixed data sets with MD/NM only on some records, or NM calculated using different definitions of mismatch, can be decoded without change. The second command demonstrates how to decode such a file. The request to not decode MD here is turning off auto-generation of both MD and NM; it will still emit the MD/NM tags on records that had these stored verbatim. 
        
        samtools view -C --output-fmt-option store_md=1 --output-fmt-option store_nm=1 -o aln.cram aln.bam
        samtools view --input-fmt-option decode_md=0 -o aln.new.bam aln.cram
        

  * An alternative way of achieving the above is listing multiple options after the **\--output-fmt** or **-O** option. The commands below are equivalent to the two above. 
        
        samtools view -O cram,store_md=1,store_nm=1 -o aln.cram aln.bam
        samtools view --input-fmt cram,decode_md=0 -o aln.new.bam aln.cram
        

  * Include customized index file as a part of arguments. 
        
        samtools view [options] -X /data_folder/data.bam /index_folder/data.bai chrM:1-10
        

  * Output alignments in read group **grp2** (records with no **RG** tag will also be in the output). 
        
        samtools view -r grp2 -o /data_folder/data.rg2.bam /data_folder/data.bam
        

  * Only keep reads with tag **BC** and were the barcode matches the barcodes listed in the barcode file. 
        
        samtools view -D BC:barcodes.txt -o /data_folder/data.barcodes.bam /data_folder/data.bam
        

  * Only keep reads with tag **RG** and read group **grp2**. This does almost the same than **-r grp2** but will not keep records without the **RG** tag. 
        
        samtools view -d RG:grp2 -o /data_folder/data.rg2_only.bam /data_folder/data.bam
        

  * Remove the actions of samtools markdup. Clear the duplicate flag and remove the **dt** tag, keep the header. 
        
        samtools view -h --remove-flags DUP -x dt -o /data_folder/dat.no_dup_markings.bam /data_folder/data.bam
        

## AUTHOR

Written by Heng Li from the Sanger Institute. 

## SEE ALSO

[_samtools_](samtools.html) (1), [_samtools-tview_](samtools-tview.html) (1), [_sam_](sam.html) (5) 

Samtools website: <<http://www.htslib.org/>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 

# 工具文档: samtools(1) manual page

Manual page from samtools-1.23  
released on 16 December 2025

## NAME

samtools – Utilities for the Sequence Alignment/Map (SAM) format 

## SYNOPSIS

samtools [addreplacerg](samtools-addreplacerg.html) -r 'ID:fish' -r 'LB:1334' -r 'SM:alpha' -o output.bam input.bam 

samtools [ampliconclip](samtools-ampliconclip.html) -b bed.file input.bam 

samtools [ampliconstats](samtools-ampliconstats.html) primers.bed in.bam 

samtools [bedcov](samtools-bedcov.html) aln.sorted.bam 

samtools [calmd](samtools-calmd.html) in.sorted.bam ref.fasta 

samtools [cat](samtools-cat.html) out.bam in1.bam in2.bam in3.bam 

samtools [checksum](samtools-checksum.html) in.bam 

samtools [collate](samtools-collate.html) -o aln.name_collated.bam aln.sorted.bam 

samtools [consensus](samtools-consensus.html) -o out.fasta in.bam 

samtools [coverage](samtools-coverage.html) aln.sorted.bam 

samtools [cram-size](samtools-cram-size.html) -v -o out.size in.cram 

samtools [depad](samtools-depad.html) input.bam 

samtools [depth](samtools-depth.html) aln.sorted.bam 

samtools [dict](samtools-dict.html) -a GRCh38 -s "Homo sapiens" ref.fasta 

samtools [faidx](samtools-faidx.html) ref.fasta 

samtools [fasta](samtools-fasta.html) input.bam > output.fasta 

samtools [fastq](samtools-fastq.html) input.bam > output.fastq 

samtools [fixmate](samtools-fixmate.html) in.namesorted.sam out.bam 

samtools [flags](samtools-flags.html) PAIRED,UNMAP,MUNMAP 

samtools [flagstat](samtools-flagstat.html) aln.sorted.bam 

samtools [fqidx](samtools-fqidx.html) ref.fastq 

samtools [head](samtools-head.html) in.bam 

samtools [idxstats](samtools-idxstats.html) aln.sorted.bam 

samtools [import](samtools-import.html) input.fastq > output.bam 

samtools [index](samtools-index.html) aln.sorted.bam 

samtools [markdup](samtools-markdup.html) in.algnsorted.bam out.bam 

samtools [merge](samtools-merge.html) out.bam in1.bam in2.bam in3.bam 

samtools [mpileup](samtools-mpileup.html) -f ref.fasta -r chr3:1,000-2,000 in1.bam in2.bam 

samtools [phase](samtools-phase.html) input.bam 

samtools [quickcheck](samtools-quickcheck.html) in1.bam in2.cram 

samtools [reference](samtools-reference.html) -o ref.fa in.cram 

samtools [reheader](samtools-reheader.html) in.header.sam in.bam > out.bam 

samtools [reset](samtools-reset.html) -o /tmp/reset.bam processed.bam 

samtools [samples](samtools-samples.html) input.bam 

samtools [sort](samtools-sort.html) -T /tmp/aln.sorted -o aln.sorted.bam aln.bam 

samtools [split](samtools-split.html) merged.bam 

samtools [stats](samtools-stats.html) aln.sorted.bam 

samtools [targetcut](samtools-targetcut.html) input.bam 

samtools [tview](samtools-tview.html) aln.sorted.bam ref.fasta 

samtools [view](samtools-view.html) -bt ref_list.txt -o aln.bam aln.sam.gz 

## DESCRIPTION

Samtools is a set of utilities that manipulate alignments in the SAM (Sequence Alignment/Map), BAM, and CRAM formats. It converts between the formats, does sorting, merging and indexing, and can retrieve reads in any regions swiftly. 

Samtools is designed to work on a stream. It regards an input file `-' as the standard input (stdin) and an output file `-' as the standard output (stdout). Several commands can thus be combined with Unix pipes. Samtools always output warning and error messages to the standard error output (stderr). 

Samtools is also able to open files on remote FTP or HTTP(S) servers if the file name starts with `ftp://', `http://', etc. Samtools checks the current working directory for the index file and will download the index upon absence. Samtools does not retrieve the entire alignment file unless it is asked to do so. 

If an index is needed, samtools looks for the index suffix appended to the filename, and if that isn't found it tries again without the filename suffix (for example **in.bam.bai** followed by **in.bai**). However if an index is in a completely different location or has a different name, both the main data filename and index filename can be pasted together with **##idx##**. For example **/data/in.bam##idx##/indices/in.bam.bai** may be used to explicitly indicate where the data and index files reside. 

## COMMANDS

Each command has its own man page which can be viewed using e.g. **man samtools-view** or with a recent GNU man using **man samtools view**. Below we have a brief summary of syntax and sub-command description. 

Options common to all sub-commands are documented below in the GLOBAL COMMAND OPTIONS section. 

**view**
    

samtools view [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

With no options or regions specified, prints all alignments in the specified input alignment file (in SAM, BAM, or CRAM format) to standard output in SAM format (with no header by default). 

You may specify one or more space-separated region specifications after the input filename to restrict output to only those alignments which overlap the specified region(s). Use of region specifications requires a coordinate-sorted and indexed input file. 

Options exist to change the output format from SAM to BAM or CRAM, so this command also acts as a file format conversion utility. 

**tview**
    

samtools tview [**-p** _chr:pos_] [**-s** _STR_] [**-d** _display_] <in.sorted.bam> [ref.fasta] 

Text alignment viewer (based on the ncurses library). In the viewer, press `?' for help and press `g' to check the alignment start from a region in the format like `chr10:10,000,000' or `=10,000,000' when viewing the same reference sequence. 

**quickcheck**
    

samtools quickcheck [_options_] _in.sam_ |_in.bam_ |_in.cram_ [ ... ] 

Quickly check that input files appear to be intact. Checks that beginning of the file contains a valid header (all formats) containing at least one target sequence and then seeks to the end of the file and checks that an end-of-file (EOF) is present and intact (BAM only). 

Data in the middle of the file is not read since that would be much more time consuming, so please note that this command will not detect internal corruption, but is useful for testing that files are not truncated before performing more intensive tasks on them. 

This command will exit with a non-zero exit code if any input files don't have a valid header or are missing an EOF block. Otherwise it will exit successfully (with a zero exit code). 

**checksum**
    

samtools checksum [_options_] _in.sam_ |_in.bam_ |_in.cram_

samtools checksum produces a CRC32 based checksum of data contained within a BAM file. This can either be order and orientation agnostic for purposes of validating all the sequencing data has passed through the entire pipeline from FASTQ through alignment and sorting, or full alignment information and order aware for the purposes of validating format conversions and while file data processing. 

**head**
    

samtools head [_options_] _in.sam_ |_in.bam_ |_in.cram_

Prints the input file's headers and optionally also its first few alignment records. This command always displays the headers as they are in the file, never adding an extra @PG header itself. 

**index**
    

samtools index [**-bc**] [**-m** _INT_] _aln.sam.gz_ |_aln.bam_ |_aln.cram_ [_out.index_] 

Index a coordinate-sorted SAM, BAM or CRAM file for fast random access. Note for SAM this only works if the file has been BGZF compressed first. (Starting from Samtools 1.16, this command can also be given several alignment filenames, which are indexed individually.) 

This index is needed when _region_ arguments are used to limit **samtools view** and similar commands to particular regions of interest. 

If an output filename is given, the index file will be written to _out.index_. Otherwise, for a CRAM file _aln.cram_ , index file _aln.cram_**.crai** will be created; for a BAM or SAM file _aln.bam_ , either _aln.bam_**.bai** or _aln.bam_**.csi** will be created, depending on the index format selected. 

**sort**
    

samtools sort [**-l** _level_] [**-m** _maxMem_] [**-o** _out.bam_] [**-O** _format_] [**-n**] [**-t** _tag_] [**-T** _tmpprefix_] [**-@** _threads_] [_in.sam_ |_in.bam_ |_in.cram_] 

Sort alignments by leftmost coordinates, or by read name when **-n** is used. An appropriate **@HD-SO** sort order header tag will be added or an existing one updated if necessary. 

The sorted output is written to standard output by default, or to the specified file (_out.bam_) when **-o** is used. This command will also create temporary files _tmpprefix_**.**_%d_**.bam** as needed when the entire alignment data cannot fit into memory (as controlled via the **-m** option). 

Consider using **samtools collate** instead if you need name collated data without a full lexicographical sort. 

Note that if the sorted output file is to be indexed with **samtools index** , the default coordinate sort must be used. Thus the **-n** and **-t** options are incompatible with **samtools index**. 

**collate**
    

samtools collate [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_< prefix>_] 

Shuffles and groups reads together by their names. A faster alternative to a full query name sort, **collate** ensures that reads of the same name are grouped together in contiguous groups, but doesn't make any guarantees about the order of read names between groups. 

The output from this command should be suitable for any operation that requires all reads from the same template to be grouped together. 

**cram-size**
    

samtools cram-size [_options_] _in.cram_

Produces a summary of CRAM block Content ID numbers and their associated Data Series stored within them. Optionally a more detailed breakdown of how each data series is encoded per container may also be listed using the **-e** or **\--encodings** option. 

**idxstats**
    

samtools idxstats _in.sam_ |_in.bam_ |_in.cram_

Retrieve and print stats in the index file corresponding to the input file. Before calling idxstats, the input BAM file should be indexed by samtools index. 

If run on a SAM or CRAM file or an unindexed BAM file, this command will still produce the same summary statistics, but does so by reading through the entire file. This is far slower than using the BAM indices. 

The output is TAB-delimited with each line consisting of reference sequence name, sequence length, # mapped reads and # unmapped reads. It is written to stdout. 

**flagstat**
    

samtools flagstat _in.sam_ |_in.bam_ |_in.cram_

Does a full pass through the input file to calculate and print statistics to stdout. 

Provides counts for each of 13 categories based primarily on bit flags in the FLAG field. Each category in the output is broken down into QC pass and QC fail, which is presented as "#PASS + #FAIL" followed by a description of the category. 

**flags**
    

samtools flags _INT_ |_STR_[,...] 

Convert between textual and numeric flag representation. 

**FLAGS:** **0x1**|  PAIRED| paired-end (or multiple-segment) sequencing technology  
---|---|---  
**0x2**|  PROPER_PAIR| each segment properly aligned according to the aligner  
**0x4**|  UNMAP| segment unmapped  
**0x8**|  MUNMAP| next segment in the template unmapped  
**0x10**|  REVERSE| SEQ is reverse complemented  
**0x20**|  MREVERSE| SEQ of the next segment in the template is reverse complemented  
**0x40**|  READ1| the first segment in the template  
**0x80**|  READ2| the last segment in the template  
**0x100**|  SECONDARY| secondary alignment  
**0x200**|  QCFAIL| not passing quality controls  
**0x400**|  DUP| PCR or optical duplicate  
**0x800**|  SUPPLEMENTARY| supplementary alignment  
  
**stats**
    

samtools stats [_options_] _in.sam_ |_in.bam_ |_in.cram_ [_region_...] 

samtools stats collects statistics from BAM files and outputs in a text format. The output can be visualized graphically using plot-bamstats. 

**bedcov**
    

samtools bedcov [_options_] _region.bed_ _in1.sam_ |_in1.bam_ |_in1.cram_[...] 

Reports the total read base count (i.e. the sum of per base read depths) for each genomic region specified in the supplied BED file. The regions are output as they appear in the BED file and are 0-based. Counts for each alignment file supplied are reported in separate columns. 

**depth**
    

samtools depth [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

Computes the read depth at each position or region. 

**ampliconstats**
    

samtools ampliconstats [_options_] _primers.bed_ _in.sam_ |_in.bam_ |_in.cram_[...] 

samtools ampliconstats collects statistics from one or more input alignment files and produces tables in text format. The output can be visualized graphically using plot-ampliconstats. 

The alignment files should have previously been clipped of primer sequence, for example by **samtools ampliconclip** and the sites of these primers should be specified as a bed file in the arguments. 

**mpileup**
    

samtools mpileup [**-EB**] [**-C** _capQcoef_] [**-r** _reg_] [**-f** _in.fa_] [**-l** _list_] [**-Q** _minBaseQ_] [**-q** _minMapQ_] _in.bam_ [_in2.bam_ [_..._]] 

Generate textual pileup for one or multiple BAM files. For VCF and BCF output, please use the **bcftools mpileup** command instead. Alignment records are grouped by sample (SM) identifiers in @RG header lines. If sample identifiers are absent, each input file is regarded as one sample. 

See the samtools-mpileup man page for a description of the pileup format and options. 

**consensus**
    

samtools consensus [**options**] _in.bam_

Generate consensus from a SAM, BAM or CRAM file based on the contents of the alignment records. The consensus is written either as FASTA, FASTQ, or a pileup oriented format. 

The default output for FASTA and FASTQ formats include one base per non-gap consensus. Hence insertions with respect to the aligned reference will be included and deletions removed. This behaviour can be adjusted. 

Two consensus calling algorithms are offered. The default computes a heterozygous consensus in a Bayesian manner, derived from the "Gap5" consensus algorithm. A simpler base frequency counting method is also available. 

**reference**
    

samtools reference [**options**] _in.bam_

Generate a reference from a SAM, BAM or CRAM file based on the contents of the SEQuence field and the MD:Z: auxiliary tags, or from the embedded reference blocks within a CRAM file (provided it was constructed using the **embed_ref=1** option). 

**coverage**
    

samtools coverage [_options_] [_in1.sam_ |_in1.bam_ |_in1.cram_ [_in2.sam_ |_in2.bam_ |_in2.cram_] [...]] 

Produces a histogram or table of coverage per chromosome. 

**merge**
    

samtools merge [**-nur1f**] [**-h** _inh.sam_] [**-t** _tag_] [**-R** _reg_] [**-b** _list_] _out.bam_ _in1.bam_ [_in2.bam_ _in3.bam_ ... _inN.bam_] 

Merge multiple sorted alignment files, producing a single sorted output file that contains all the input records and maintains the existing sort order. 

If **-h** is specified the @SQ headers of input files will be merged into the specified header, otherwise they will be merged into a composite header created from the input headers. If the @SQ headers differ in order this may require the output file to be re-sorted after merge. 

The ordering of the records in the input files must match the usage of the **-n** and **-t** command-line options. If they do not, the output order will be undefined. See **sort** for information about record ordering. 

**split**
    

samtools split [_options_] _merged.sam_ |_merged.bam_ |_merged.cram_

Splits a file by read group, producing one or more output files matching a common prefix (by default based on the input filename) each containing one read-group. 

**cat**
    

samtools cat [**-b** _list_] [**-h** _header.sam_] [**-o** _out.bam_] _in1.bam_ _in2.bam_ [ ... ] 

Concatenate BAMs or CRAMs. Although this works on either BAM or CRAM, all input files must be the same format as each other. The sequence dictionary of each input file must be identical, although this command does not check this. This command uses a similar trick to **reheader** which enables fast BAM concatenation. 

**import**
    

samtools import [_options_] _in.fastq_ [ ... ] 

Converts one or more FASTQ files to unaligned SAM, BAM or CRAM. These formats offer a richer capability of tracking sample meta-data via the SAM header and per-read meta-data via the auxiliary tags. The **fastq** command may be used to reverse this conversion. 

**fastq/a**
    

samtools fastq [_options_] _in.bam_   
samtools fasta [_options_] _in.bam_

Converts a BAM or CRAM into either FASTQ or FASTA format depending on the command invoked. The files will be automatically compressed if the file names have a .gz, .bgz, or .bgzf extension. 

The input to this program must be collated by name. Use **samtools collate** or **samtools sort -n** to ensure this. 

**faidx**
    

samtools faidx <ref.fasta> [region1 [...]] 

Index reference sequence in the FASTA format or extract subsequence from indexed reference sequence. If no region is specified, **faidx** will index the file and create _< ref.fasta>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTA format. 

The input file can be compressed in the **BGZF** format. 

FASTQ files can be read and indexed by this command. Without using **\--fastq** any extracted subsequence will be in FASTA format. 

**fqidx**
    

samtools fqidx <ref.fastq> [region1 [...]] 

Index reference sequence in the FASTQ format or extract subsequence from indexed reference sequence. If no region is specified, **fqidx** will index the file and create _< ref.fastq>.fai_ on the disk. If regions are specified, the subsequences will be retrieved and printed to stdout in the FASTQ format. 

The input file can be compressed in the **BGZF** format. 

**samtools fqidx** should only be used on fastq files with a small number of entries. Trying to use it on a file containing millions of short sequencing reads will produce an index that is almost as big as the original file, and searches using the index will be very slow and use a lot of memory. 

**dict**
    

samtools dict _ref.fasta_ |_ref.fasta.gz_

Create a sequence dictionary file from a fasta file. 

**calmd**
    

samtools calmd [**-Eeubr**] [**-C** _capQcoef_] _aln.bam_ _ref.fasta_

Generate the MD tag. If the MD tag is already present, this command will give a warning if the MD tag generated is different from the existing tag. Output SAM by default. 

Calmd can also read and write CRAM files although in most cases it is pointless as CRAM recalculates MD and NM tags on the fly. The one exception to this case is where both input and output CRAM files have been / are being created with the _no_ref_ option. 

**fixmate**
    

samtools fixmate [**-rpcm**] [**-O** _format_] _in.nameSrt.bam out.bam_

Fill in mate coordinates, ISIZE and mate related flags from a name-sorted alignment. 

**markdup**
    

samtools markdup [**-l** _length_] [**-r**] [**-s**] [**-T**] [**-S**] _in.algsort.bam out.bam_

Mark duplicate alignments from a coordinate sorted file that has been run through **samtools fixmate** with the **-m** option. This program relies on the MC and ms tags that fixmate provides. 

**rmdup**
    

samtools rmdup [-sS] <input.srt.bam> <out.bam>

**This command is obsolete. Use markdup instead.**

**addreplacerg**
    

samtools addreplacerg [**-r** _rg-line_ | **-R** _rg-ID_] [**-m** _mode_] [**-l** _level_] [**-o** _out.bam_] _in.bam_

Adds or replaces read group tags in a file. 

**reheader**
    

samtools reheader [**-iP**] _in.header.sam in.bam_

Replace the header in _in.bam_ with the header in _in.header.sam_. This command is much faster than replacing the header with a BAM→SAM→BAM conversion. 

By default this command outputs the BAM or CRAM file to standard output (stdout), but for CRAM format files it has the option to perform an in-place edit, both reading and writing to the same file. No validity checking is performed on the header, nor that it is suitable to use with the sequence data itself. 

**targetcut**
    

samtools targetcut [**-Q** _minBaseQ_] [**-i** _inPenalty_] [**-0** _em0_] [**-1** _em1_] [**-2** _em2_] [**-f** _ref_] _in.bam_

This command identifies target regions by examining the continuity of read depth, computes haploid consensus sequences of targets and outputs a SAM with each sequence corresponding to a target. When option **-f** is in use, BAQ will be applied. This command is **only** designed for cutting fosmid clones from fosmid pool sequencing [Ref. Kitzman et al. (2010)]. 

**phase**
    

samtools phase [**-AF**] [**-k** _len_] [**-b** _prefix_] [**-q** _minLOD_] [**-Q** _minBaseQ_] _in.bam_

Call and phase heterozygous SNPs. 

**depad**
    

samtools depad [**-SsCu1**] [**-T** _ref.fa_] [**-o** _output_] _in.bam_

Converts a BAM aligned against a padded reference to a BAM aligned against the depadded reference. The padded reference may contain verbatim "*" bases in it, but "*" bases are also counted in the reference numbering. This means that a sequence base-call aligned against a reference "*" is considered to be a cigar match ("M" or "X") operator (if the base-call is "A", "C", "G" or "T"). After depadding the reference "*" bases are deleted and such aligned sequence base-calls become insertions. Similarly transformations apply for deletions and padding cigar operations. 

**ampliconclip**
    

samtools ampliconclip [**-o** _out.file_] [**-f** _stat.file_] [**\--soft-clip**] [**\--hard-clip**] [**\--both-ends**] [**\--strand**] [**\--clipped**] [**\--fail**] [**\--no-PG**] **-b** _bed.file in.file_

Clip reads in a SAM compatible file based on data from a BED file. 

**samples**
    

samtools samples [**-o** _out.file_] [**-i**] [**-T** _TAG_] [**-f** _refs.fasta_] [**-F** _refs_list_] [**-X**] 

Prints the samples from alignment files 

**reset**
    

samtools reset [**-o** _FILE_] [**-x** /**\--remove-tag** _tag_list_] [**\--keep-tag** _tag_list_] [**\--reject-PG** _pgid_] [**\--no-RG**] [**\--no-PG**] [...] 

Removes alignment information from records, producing an unaligned SAM, BAM or CRAM file. Flags are reset, header tags are updated or removed as appropriate, and auxiliary tags are removed or retained as specified. Note that the sort order is unchanged. 

## SAMTOOLS OPTIONS

These are options that are passed after the **samtools** command, before any sub-command is specified. 

**help** , **\--help**
    

Display a brief usage message listing the samtools commands available. If the name of a command is also given, e.g., **samtools help view** , the detailed usage message for that particular command is displayed. 

**\--version**
    

Display the version numbers and copyright information for samtools and the important libraries used by samtools. 

**\--version-only**
    

Display the full samtools version number in a machine-readable format. 

## GLOBAL COMMAND OPTIONS

Several long-options are shared between multiple samtools sub-commands: **\--input-fmt** , **\--input-fmt-option** , **\--output-fmt** , **\--output-fmt-option** , **\--reference** , **\--write-index** , and **\--verbosity**. The input format is auto-detected and specifying the format is unnecessary, so this option is rarely offered. Note that not all subcommands have all options. Consult the subcommand help for more details. 

Format strings recognised are "sam", "sam.gz", "bam" and "cram". They may be followed by a comma separated list of options as _key_ or _key_ =_value_. See below for examples. 

The **fmt-option** arguments accept either a single _option_ or _option_ =_value_. Note that some options only work on some file formats and only on read or write streams. If value is unspecified for a boolean option, the value is assumed to be 1. The valid options are as follows. 

**level=**_INT_
    

Output only. Specifies the compression level from 1 to 9, or 0 for uncompressed. If the output format is SAM, this also enables BGZF compression, otherwise SAM defaults to uncompressed. 

**nthreads=**_INT_
    

Specifies the number of threads to use during encoding and/or decoding. For BAM this will be encoding only. In CRAM the threads are dynamically shared between encoder and decoder. 

**filter=**_STRING_
    

Apply filter STRING to all incoming records, rejecting any that do not satisfy the expression. See the FILTER EXPRESSIONS section below for specifics. 

**reference=**_fasta_file_
    

Specifies a FASTA reference file for use in CRAM encoding or decoding. It usually is not required for decoding except in the situation of the MD5 not being obtainable via the REF_PATH or REF_CACHE environment variables. 

**decode_md=**_0|1_
    

CRAM input only; defaults to 1 (on). CRAM does not typically store MD and NM tags, preferring to generate them on the fly. When this option is 0 missing MD, NM tags will not be generated. It can be particularly useful when combined with a file encoded using store_md=1 and store_nm=1. 

**store_md=**_0|1_
    

CRAM output only; defaults to 0 (off). CRAM normally only stores MD tags when the reference is unknown and lets the decoder generate these values on-the-fly (see decode_md). 

**store_nm=**_0|1_
    

CRAM output only; defaults to 0 (off). CRAM normally only stores NM tags when the reference is unknown and lets the decoder generate these values on-the-fly (see decode_md). 

**ignore_md5=**_0|1_
    

CRAM input only; defaults to 0 (off). When enabled, md5 checksum errors on the reference sequence and block checksum errors within CRAM are ignored. Use of this option is strongly discouraged. 

**required_fields=**_bit-field_
    

CRAM input only; specifies which SAM columns need to be populated. By default all fields are used. Limiting the decode to specific columns can have significant performance gains. The bit-field is a numerical value constructed from the following table.  **0x1**|  SAM_QNAME  
---|---  
**0x2**|  SAM_FLAG  
**0x4**|  SAM_RNAME  
**0x8**|  SAM_POS  
**0x10**|  SAM_MAPQ  
**0x20**|  SAM_CIGAR  
**0x40**|  SAM_RNEXT  
**0x80**|  SAM_PNEXT  
**0x100**|  SAM_TLEN  
**0x200**|  SAM_SEQ  
**0x400**|  SAM_QUAL  
**0x800**|  SAM_AUX  
**0x1000**|  SAM_RGAUX  
  
**name_prefix=**_string_
    

CRAM input only; defaults to output filename. Any sequences with auto-generated read names will use _string_ as the name prefix. 

**multi_seq_per_slice=**_0|1_
    

CRAM output only; defaults to 0 (off). By default CRAM generates one container per reference sequence, except in the case of many small references (such as a fragmented assembly). 

**version=**_major.minor_
    

CRAM output only. Specifies the CRAM version number. Acceptable values are "2.1", "3.0", and "3.1". 

**seqs_per_slice=**_INT_
    

CRAM output only; defaults to 10000. 

**slices_per_container=**_INT_
    

CRAM output only; defaults to 1. The effect of having multiple slices per container is to share the compression header block between multiple slices. This is unlikely to have any significant impact unless the number of sequences per slice is reduced. (Together these two options control the granularity of random access.) 

**embed_ref=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, this will store portions of the reference sequence in each slice, permitting decode without having requiring an external copy of the reference sequence. 

**no_ref=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, sequences will be stored verbatim with no reference encoding. This can be useful if no reference is available for the file. 

**use_bzip2=**_0|1_
    

CRAM output only; defaults to 0 (off). Permits use of bzip2 in CRAM block compression. 

**use_lzma=**_0|1_
    

CRAM output only; defaults to 0 (off). Permits use of lzma in CRAM block compression. 

**use_arith=**_0|1_
    

CRAM ≥ 3.1 output only; enables use of arithmetic entropy coding in CRAM block compression. This is off by default, but enabled for archive mode. This is significantly slower but sometimes smaller than the standard rANS entropy encoder. 

**use_fqz=**_0|1_
    

CRAM ≥ 3.1 output only; enables and disables the fqzcomp quality compression method. This is on by default for version 3.1 and above only when the small and archive profiles are in use. 

**use_tok=**_0|1_
    

CRAM ≥ 3.1 output only; enables and disables the name tokeniser compression method. This is on by default for version 3.1 and above. 

**lossy_names=**_0|1_
    

CRAM output only; defaults to 0 (off). If 1, templates with all members within the same CRAM slice will have their read names removed. New names will be automatically generated during decoding. Also see the **name_prefix** option. 

**fast, normal, small, archive**
    

CRAM output only. Set the CRAM compression profile. This is a simplified way of setting many output options at once. It changes the following options according to the profile in use. The "normal" profile is the default. 

**Option**| **fast**| **normal**| **small**| **archive**  
---|---|---|---|---  
**level**|  1| 5| 6| 7  
**use_bzip2**|  off| off| on| on  
**use_lzma**|  off| off| off| on if level>7  
**use_tok(*)**|  off| on| on| on  
**use_fqz(*)**|  off| off| on| on  
**use_arith(*)**|  off| off| off| on  
**seqs_per_slice**|  10000| 10000| 25000| 100000  
  
(*) **use_tok** , **use_fqz** and **use_arith** are only enabled for CRAM version 3.1 and above. 

The **level** listed is only the default value, and will not be set if it has been explicitly changed already. Additionally **bases_per_slice** is set to **500*seqs_per_slice** unless previously explicitly set. 

**fastq_name2**
    

FASTQ input only. Indicates that the names are not the first word in the header, but the second. This is a FASTQ variant commonly used in the SRA and ENA archives. 

**fastq_casava**
    

FASTQ input and output only. The Illumina CASAVA identifiers are stored in the second word of the FASTQ header lines and store read meta-data. The CASAVA tag defines the data held in the READ1, READ2 and QCFAIL flags and the barcode auxiliary tag ("BC" by default). This option may be used to both read and write CASAVA identifiers. 

**fastq_barcode=**_TAG_
    

FASTQ input and output only. When the **fastq_casava** option is used, this controls the name of the barcode aux tag to be used. _TAG_ defaults to "BC" if not specified. 

**fastq_aux=**_LIST_
    

FASTQ input and output only. Processes SAM format auxiliary tags following the other fields on the record identifier lines. If no **=**_LIST_ is specified or _LIST_ is "1" then all aux tags listed are copied to/from the SAM record. Otherwise it is a comma separated list of 2-letter tag types and is used to control which tags are processed with any others being omitted. 

Note as commas are used to separate options in the **\--output-fmt** string detailing file format and options combined together, you will need to use the **\--output-fmt-option** option if you want to specify a comma separated list of tag types. 

**fastq_rnum**
    

FASTQ output only. If set, paired reads will have "/1" and "/2" appended to their read names. This has no effect on unpaired reads. When reading FASTQ these suffixes are automatically detected and processed irrespective of the **fastq_rnum** option. 

**fastq_umi=**_TAGLIST_
    

FASTQ input and output only. When reading from a FASTQ file this indicates to extract the UMI tag from the read name and to put it in the TAG specified (which defaults to `RX' if no tag name is given). The UMI is assumed to be the 8th colon-separated element, conforming to Illumina BCL to FASTQ conversion specifications. However see the **fastq_umi_regexp** option for altering this. 

When converting from SAM to FASTQ, _TAGLIST_ is a comma separated list of tags which are checked in turn for their presence. The string from the first tag found is then appended to the end of the read-name. There is no regexp available in this case and the data is always appended to the end of the name, or if hash-number is present (for example `name#49') to just prior to the hash character. The _TAGLIST_ defaults to `OX,RX'. 

**fastq_umi_regex=**_REGEX_
    

FASTQ input only. Specifies the regular expression used for finding UMI strings in a read name. Any text within the single bracketted element will be used as the UMI string. Text matched by that string will be removed from the read name, with anything to the right of it being moved leftwards. This defaults to `^[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:[^:]+:([^:#/]+)'. 

For example: 
    
    
    samtools view --input-fmt-option decode_md=0
        --output-fmt cram,version=3.0 --output-fmt-option embed_ref
        --output-fmt-option seqs_per_slice=2000 -o foo.cram foo.bam
    
    
    
    samtools view -O cram,small -o bar.cram bar.bam
    

The **\--write-index** option enables automatic index creation while writing out BAM, CRAM or bgzf SAM files. Note to get compressed SAM as the output format you need to manually request a compression level, otherwise all SAM files are uncompressed. By default SAM and BAM will use CSI indices while CRAM will use CRAI indices. If you need to create BAI indices note that it is possible to specify the name of the index being written to, and hence the format, by using the **filename##idx##indexname** notation. 

For example: to convert a BAM to a compressed SAM with CSI indexing: 
    
    
    samtools view -h -O sam,level=6 --write-index in.bam -o out.sam.gz
    

To convert a SAM to a compressed BAM using BAI indexing: 
    
    
    samtools view --write-index in.sam -o out.bam##idx##out.bam.bai
    

The **\--verbosity** _INT_ option sets the verbosity level for samtools and HTSlib. The default is 3 (HTS_LOG_WARNING); 2 reduces warning messages and 0 or 1 also reduces some error messages, while values greater than 3 produce increasing numbers of additional warnings and logging messages. 

## FILTER EXPRESSIONS

Filter expressions are used as an on-the-fly checking of incoming SAM, BAM or CRAM records, discarding records that do not match the specified expression. 

The language used is primarily C style, but with a few differences in the precedence rules for bit operators and the inclusion of regular expression matching. 

The operator precedence, from strongest binding to weakest, is: 

Grouping| **(, )**|  E.g. "(1+2)*3"  
---|---|---  
Values:| **literals, vars**|  Numbers, strings and variables  
Unary ops:| **+, -, !, ~**|  E.g. -10 +10, !10 (not), ~5 (bit not)  
Math ops:| ***, /, %**|  Multiply, division and (integer) modulo  
Math ops:| **+, -**|  Addition / subtraction  
Bit-wise:| **&**|  Integer AND  
Bit-wise| **^**|  Integer XOR  
Bit-wise| **|**|  Integer OR  
Conditionals:| **> , >=, <, <=**  
Equality:| **==, !=, =~, !~**|  =~ and !~ match regular expressions  
Boolean:| **& &, ||**| Logical AND / OR  
  
Expressions are computed using floating point mathematics, so "10 / 4" evaluates to 2.5 rather than 2. They may be written as integers in decimal or "0x" plus hexadecimal, and floating point with or without exponents.However operations that require integers first do an implicit type conversion, so "7.9 % 5" is 2 and "7.9 & 4.1" is equivalent to "7 & 4", which is 4. Strings are always specified using double quotes. To get a double quote in a string, use backslash. Similarly a double backslash is used to get a literal backslash. For example **ab\"c\\\d** is the string **ab"c\d**. 

Comparison operators are evaluated as a match being 1 and a mismatch being 0, thus "(2 > 1) + (3 < 5)" evaluates as 2. All comparisons involving undefined (null) values are deemed to be false. 

The variables are where the file format specifics are accessed from the expression. The variables correspond to SAM fields, for example to find paired alignments with high mapping quality and a very large insert size, we may use the expression "**mapq >= 30 && (tlen >= 100000 || tlen <= -100000)**". Valid variable names and their data types are: 

**endpos**|  int| Alignment end position (1-based)  
---|---|---  
**flag**|  int| Combined FLAG field  
**flag.paired**|  int| Single bit, 0 or 1  
**flag.proper_pair**|  int| Single bit, 0 or 2  
**flag.unmap**|  int| Single bit, 0 or 4  
**flag.munmap**|  int| Single bit, 0 or 8  
**flag.reverse**|  int| Single bit, 0 or 16  
**flag.mreverse**|  int| Single bit, 0 or 32  
**flag.read1**|  int| Single bit, 0 or 64  
**flag.read2**|  int| Single bit, 0 or 128  
**flag.secondary**|  int| Single bit, 0 or 256  
**flag.qcfail**|  int| Single bit, 0 or 512  
**flag.dup**|  int| Single bit, 0 or 1024  
**flag.supplementary**|  int| Single bit, 0 or 2048  
**hclen**|  int| Number of hard-clipped bases  
**library**|  string| Library (LB header via RG)  
**mapq**|  int| Mapping quality  
**mpos**|  int| Synonym for pnext  
**mrefid**|  int| Mate reference number (0 based)  
**mrname**|  string| Synonym for rnext  
**ncigar**|  int| Number of cigar operations  
**pnext**|  int| Mate's alignment position (1-based)  
**pos**|  int| Alignment position (1-based)  
**qlen**|  int| Alignment length: no. query bases  
**qname**|  string| Query name  
**qual**|  string| Quality values (raw, 0 based)  
**refid**|  int| Integer reference number (0 based)  
**rlen**|  int| Alignment length: no. reference bases  
**rname**|  string| Reference name  
**rnext**|  string| Mate's reference name  
**sclen**|  int| Number of soft-clipped bases  
**seq**|  string| Sequence  
**tlen**|  int| Template length (insert size)  
**[XX]**|  int / string| XX tag value  
  
Flags are returned either as the whole flag value or by checking for a single bit. Hence the filter expression **flag.dup** is equivalent to **flag & 1024**. 

"qlen" and "rlen" are measured using the CIGAR string to count the number of query (sequence) and reference bases consumed. Note "qlen" may not exactly match the length of the "seq" field if the sequence is "*". 

"sclen" and "hclen" are the number of soft and hard-clipped bases respectively. The formula "qlen-sclen" gives the number of sequence bases used in the alignment, distinguishing between global alignment and local alignment length. 

"endpos" is the (1-based inclusive) position of the rightmost mapped base of the read, as measured using the CIGAR string, and for mapped reads is equivalent to "pos+rlen-1". For unmapped reads, it is the same as "pos". 

Reference names may be matched either by their string forms ("rname" and "mrname") or as the Nth **@SQ** line (counting from zero) as stored in BAM using "tid" and "mtid" respectively. 

Auxiliary tags are described in square brackets and these expand to either integer or string as defined by the tag itself (**XX:Z:**_string_ or **XX:i:**_int_). For example **[NM] >=10** can be used to look for alignments with many mismatches and **[RG]=~"grp[ABC]-"** will match the read-group string. 

If no comparison is used with an auxiliary tag it is taken simply to be a test for the existence of that tag. So **[NM]** will return any record containing an NM tag, even if that tag is zero (**NM:i:0**). In htslib <= 1.15 negating this with **![NM]** gave misleading results as it was true if the tag did not exist or did exist but was zero. Now this is strictly does-not-exist. An explicit **exists([NM])** and **!exists([NM])** function has also been added to make this intention clear. 

Similarly in htslib <= 1.15 using **[NM]!=0** was true both when the tag existed and was not zero as well as when the tag did not exist. From 1.16 onwards all comparison operators are only true for tags that exist, so **[NM]!=0** works as expected. 

Some simple functions are available to operate on strings. These treat the strings as arrays of bytes, permitting their length, minimum, maximum and average values to be computed. These are useful for processing Quality Scores. 

**length(x)**|  Length of the string (excluding nul char)  
---|---  
**min(x)**|  Minimum byte value in the string  
**max(x)**|  Maximum byte value in the string  
**avg(x)**|  Average byte value in the string  
  
Note that "avg" is a floating point value and it may be NAN for empty strings. This means that "avg(qual)" does not produce an error for records that have both seq and qual of "*". NAN values will fail any conditional checks, so e.g. "avg(qual) > 20" works and will not report these records. NAN also fails all equality, < and > comparisons, and returns zero when given as an argument to the **exists** function. It can be negated with **!x** in which case it becomes true. 

Functions that operate on both strings and numerics: 

**exists(x)**|  True if the value exists (or is explicitly true).  
---|---  
**default(x,d)**|  Value **x** if it exists or **d** if not.  
  
Functions that apply only to numeric values: 

**sqrt(x)**|  Square root of **x**  
---|---  
**log(x)**|  Natural logarithm of **x**  
**pow(x, y)**|  Power function, **x** to the power of **y**  
**exp(x)**|  Base-e exponential, equivalent to **pow(e,x)**  
  
## ENVIRONMENT VARIABLES

**HTS_PATH**
    

A colon-separated list of directories in which to search for HTSlib plugins. If $HTS_PATH starts or ends with a colon or contains a double colon (**::**), the built-in list of directories is searched at that point in the search. 

If no HTS_PATH variable is defined, the built-in list of directories specified when HTSlib was built is used, which typically includes **/usr/local/libexec/htslib** and similar directories. 

**REF_PATH**
    

A colon separated (semi-colon on Windows) list of locations in which to look for sequences identified by their MD5sums. This can be either a list of directories or URLs. Note that if a URL is included then the colon in http:// and ftp:// and the optional port number will be treated as part of the URL and not a PATH field separator. Alternatively a double colon may be used to indicate a single colon character. If REF_PATH includes **%**_num_**s** then it is replaced with the next _num_ elements of the md5sum. An implicit **/%s** is also added to each path element if any md5sum digits are unused. For example "REF_PATH=/some/dir/%4s/%s" or "REF_PATH=/some/dir/%4s" will search a directory structure with the first 4 characters of the md5sum as a subdirectory and the remaining 28 as the filename within that directory. 

Version 1.21 and earlier defaulted to using the EBI's CRAM reference server if no REF_PATH was specified. This default has been removed to reduce load on the EBI's service. It is recommended that a site-wide proxy is set up to allow better sharing of downloaded references, for example the _ref-cache_ server provided with HTSlib. The original behaviour can be restored by including **http://www.ebi.ac.uk/ena/cram/md5/%s** in your REF_PATH. If that is done, it is strongly encouraged you also specify a local REF_CACHE directory. 

See <<https://www.htslib.org/doc/reference_seqs.html>> and **REFERENCE SEQUENCES** below for more information. 

**REF_CACHE**
    

This can be defined to a single location housing a local cache of references. When REF_CACHE is set any non-local reference will create a file in the local REF_CACHE named after the sequence md5sum. This cache will be searched prior to REF_PATH. If you wish to search REF_CACHE but not to further populate it, add the directory to the start of REF_PATH instead. 

As per REF_PATH, the percent notation (e.g. "dir/%2s/%2s/%s") may be used to avoid too many files within a single directory. 

To pre-populate the REF_CACHE a script **misc/seq_cache_populate.pl** is provided in the Samtools distribution. This takes a fasta file or a directory of fasta files and generates the MD5sum named files. 

For example if you use **seq_cache_populate -subdirs 2 -root /local/ref_cache** to create 2 nested subdirectories (the default), each consuming 2 characters of the MD5sum, then REF_CACHE must be set to **/local/ref_cache/%2s/%2s/%s**. 

## REFERENCE SEQUENCES

The CRAM format requires use of a reference sequence for both reading and writing. 

When reading a CRAM the **@SQ** headers are interrogated to identify the reference sequence MD5sum (**M5:** tag) and the local reference sequence filename (**UR:** tag). Note that non-local URIs in the UR tag are not used, but _file://_ is supported. This is a change in behaviour, but not documentation, to htslib 1.21. 

To create a CRAM the **@SQ** headers will also be read to identify the reference sequences, but M5: and UR: tags may not be present. In this case the **-T** and **-t** options of samtools view may be used to specify the fasta or fasta.fai filenames respectively (provided the .fasta.fai file is also backed up by a .fasta file). 

The search order to obtain a reference is: 

Use any local file specified by the command line options (eg -T). 

Look for MD5 via REF_CACHE environment variable. 

Look for MD5 in each element of the REF_PATH environment variable. 

Look for a local file listed in the UR: header tag. 

## EXAMPLES

  * Import SAM to BAM when **@SQ** lines are present in the header: 
        
        samtools view -b aln.sam > aln.bam
        

If **@SQ** lines are absent: 
        
        samtools faidx ref.fa
        samtools view -bt ref.fa.fai aln.sam > aln.bam
        

where _ref.fa.fai_ is generated automatically by the **faidx** command. 

  * Convert a BAM file to a CRAM file using a local reference sequence. 
        
        samtools view -C -T ref.fa aln.bam > aln.cram
        

## AUTHOR

Heng Li from the Sanger Institute wrote the original C version of samtools. Bob Handsaker from the Broad Institute implemented the BGZF library. Petr Danecek and Heng Li wrote the VCF/BCF implementation. James Bonfield from the Sanger Institute developed the CRAM implementation. Other large code contributions have been made by John Marshall, Rob Davies, Martin Pollard, Andrew Whitwham, Valeriu Ohan, Vasudeva Sarma (all while primarily at the Sanger Institute), with numerous other smaller but valuable contributions. See the per-command manual pages for further authorship. 

## SEE ALSO

[_samtools-addreplacerg_](samtools-addreplacerg.html) (1), [_samtools-ampliconclip_](samtools-ampliconclip.html) (1), [_samtools-ampliconstats_](samtools-ampliconstats.html) (1), [_samtools-bedcov_](samtools-bedcov.html) (1), [_samtools-calmd_](samtools-calmd.html) (1), [_samtools-cat_](samtools-cat.html) (1), [_samtools-checksum_](samtools-checksum.html) (1), [_samtools-collate_](samtools-collate.html) (1), [_samtools-consensus_](samtools-consensus.html) (1), [_samtools-coverage_](samtools-coverage.html) (1), [_samtools-cram-size_](samtools-cram-size.html) (1), [_samtools-depad_](samtools-depad.html) (1), [_samtools-depth_](samtools-depth.html) (1), [_samtools-dict_](samtools-dict.html) (1), [_samtools-faidx_](samtools-faidx.html) (1), [_samtools-fasta_](samtools-fasta.html) (1), [_samtools-fastq_](samtools-fastq.html) (1), [_samtools-fixmate_](samtools-fixmate.html) (1), [_samtools-flags_](samtools-flags.html) (1), [_samtools-flagstat_](samtools-flagstat.html) (1), [_samtools-fqidx_](samtools-fqidx.html) (1), [_samtools-head_](samtools-head.html) (1), [_samtools-idxstats_](samtools-idxstats.html) (1), [_samtools-import_](samtools-import.html) (1), [_samtools-index_](samtools-index.html) (1), [_samtools-markdup_](samtools-markdup.html) (1), [_samtools-merge_](samtools-merge.html) (1), [_samtools-mpileup_](samtools-mpileup.html) (1), [_samtools-phase_](samtools-phase.html) (1), [_samtools-quickcheck_](samtools-quickcheck.html) (1), [_samtools-reference_](samtools-reference.html) (1), [_samtools-reheader_](samtools-reheader.html) (1), [_samtools-reset_](samtools-reset.html) (1), [_samtools-rmdup_](samtools-rmdup.html) (1), [_samtools-sort_](samtools-sort.html) (1), [_samtools-split_](samtools-split.html) (1), [_samtools-stats_](samtools-stats.html) (1), [_samtools-targetcut_](samtools-targetcut.html) (1), [_samtools-tview_](samtools-tview.html) (1), [_samtools-view_](samtools-view.html) (1), [_bcftools_](bcftools.html) (1), [_sam_](sam.html) (5), [_tabix_](tabix.html) (1) _ref-cache(1)_

Samtools website: <<http://www.htslib.org/>>   
File format specification of SAM/BAM,CRAM,VCF/BCF: <<http://samtools.github.io/hts-specs>>   
Samtools latest source: <<https://github.com/samtools/samtools>>   
HTSlib latest source: <<https://github.com/samtools/htslib>>   
Bcftools website: <<http://samtools.github.io/bcftools>>

* * *

Copyright © 2025 Genome Research Limited (reg no. 2742969) is a charity registered in England with number 1021457. [Terms and conditions](/terms). 
