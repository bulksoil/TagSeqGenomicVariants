# Calling genomic variants from 3' Tag Sequencing Data

## Introduction and reasoning
More and more, 3' tag sequencing (tag-seq) is being used as an alternative to traditional RNA sequencing to asses the transcriptional profile of samples. Tag-seq focusses the sequencing effort to the 3' end of a transcript, and in doing so requires less coverage to quantitatively determine expression levels for a gene. This means that one can expend less sequencing effort per sample to achieve similar concusions as traditional RNAseq. 

<img src="img/tagseq.png" width="250">

One thing that biologists interested in hybridization and heterosis are interested in is assessing the contribution of each parent to the overall transcriptional state of the offspring organism. To do this with tranditional RNAseq, one would find meaninful SNPs that define an allele, then map the reads back to the genomes and figure out how many reads map to these alleles that define the parental genomes. 

Because the sequencing effort is limited to the 3' end of the transcripts in tag-seq, I want to see here if it is feasible to use tag-seq to define parent of origin expression. In this example, I use tag-seq data from the parents of the Arabidopsis thaliana MAGIC lines to call variants.

## Data Processing

### Trimming sequencing results
Tag-seq reads originate mainly in the 3' UTR of transcripts, therefore many of the reads contain the polyA tail. This part needs to be trimmed off. I have written a python script `fq_trim.py` that will do this. Not only that, but with tag-seq data, it is important to trim the first 12 bases of the reads because they originate from random primers and likely have some mismatched bases from the reference genome. Some processing tips can be found [here](http://dnatech.genomecenter.ucdavis.edu/wp-content/uploads/2017/09/Quant-Seq-FWD-data-analysis-recommendations-Tag-Seq.pdf).

But before trimming, let's get everything in order so that we can automate the process.

I took some time to get a file together with unique identifying information for each fastq file so that I could write a quick shell script to automate some of the stuff. For example:

Original File | Unique identifier
------------- | -----------------
IMCK_tagseq_EVSPool2_Rsch-1_Juenger-7_I789_L2_R1.fastq | Pool2_Rsch-1
IMCJ_tagseq_EVSPool1_Bur-6_Juenger-3_I789_L1_R1.fastq | Pool1_Bur-6

Next we can loop over each file to trim it accordingly. Note that the the `-n` option is set to 25 here. This means that if after trimming away the polyA tail and there is less than 25 bases left, the program will discard the read. One may have to play with this option to see what they like the best.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; fq_trim.py -i *"$sample"* -n 15 -o "$sample"_trim.fq;
done;
```
### Aligning reads
Now that everything is trimmed down to remove the polyA tail we can align the reads to the genome. I think it is best to call SNPs verse one well-annotated genome, so in this case I am using the TAIR10 Columbia reference genome. We will do the aligning in the splice-aware manner because the reads can cover a few exons as well as the 3' UTR.

I'll align to the col genome using Bowtie2 + Tophat. Before aligning, bowtie2 needs to index the reference genome. You can do this with the below code.
```
bowtie2 index TAIR10_chr_all.fas at
```

`TAIR10_chr_all.fas` is the input fasta file and `at` is the prefix that will be put on the created index files. Next we will align the reads for each fastq file to the col genome.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; \
tophat -o "$sample"_th /Users/joeya/JOE/reference/at "$sample"_trim.fq; \
done;
```
This will output all kinds of stuff, but we are mainly interested in is the `accepted_hits.bam` it spits out. This file needs to be sorted before continuing.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; \
samtools sort "$sample"_th/accepted_hits.bam > "$sample"_sorted.bam; \
done;
```

Now we are ready to call variants

### Calling variants
We will use the mpileup command out of bcftools to call variants in the alignments compared to the columbia reference genome.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; \
bcftools mpileup -Ou -f ~/JOE/Reference/at.fa "$sample"_sorted.bam | bcftools call -mv -o "$sample"_calls.bcf; \
done;
```

Here we are looping through the sorted bam file, running them through the `mpileup` program. What mpileup does is it goes through your the alignment file (.bam) and stacks up each aligned base to the reference genome. For instance at position 1119587 on Chromosome one there may be 8 reads that share that space with basecalls of AAATAAAA. If you do this over every place where a read aligned in the genome, you get a pileup file.

We then pipe this into the bcftools `call` program which will make consesus base calls at each position - and assign a quality value to each. We can later use these quality assignments to filter for high confidence polymorphisms.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; \
bcftools view -i '%QUAL>=80' -o "$sample"_hq_calls.vcf "$sample"_calls.bcf; \
done;
```

```
echo -e "SampleID\tDepth\tVariants";\
for sample in $(cat samples); \
do echo -e "$sample\t" `awk '{s++}END{print s/4}' "$sample"_trim.fq` "\t" `grep -v "^#" "HQ_CALLS/$sample"_hq_calls.vcf | wc -l`; \
done;
```

This ultimately gives us the position of each snp compared to the Columbia genome, but we do not have any idea what the geneIDs are for the SNPs. So to figure this out, let's run this script over the generated files.

```
for sample in $(cat samples); \
do echo "On sample: $sample"; \
snp_to_gene.py -i "$sample"_hq_calls.vcf -g ~/tutorial/reference/TAIR10_GFF3_genes_transposons.gff -o "$sample"_calls_with_geneid.vcf; \
done;
```

We will actually need the counts for each geneID to be able to do some of the downstream analysis. So Let's go ahead and generate the counts using HTSeq.

```
for sample in $(cat samples); \
do echo "On sample $sample"; \
samtools view "$sample"_sorted.bam | htseq-count - ~/tutorial/reference/Arabidopsis_thaliana.TAIR10.40.gtf.gz > "$sample"_counts.tsv; \
done; 
```

Alternatively, if you would like to get counts from Salmon, you can do it this way on the trimmed reads.

```
for sample in $(cat samples); \
do echo "On sample $sample"; \
salmon quant -i ~/JOE/Arabidopsis/Reference/at_index -l A -r "$sample"_trim.fq -p 8 -o "$sample"_salmon_quant --noLengthCorrection; \
done;
```