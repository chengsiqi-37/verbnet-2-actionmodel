# VerbNet 2 Action Model

This is the official repository for the paper:

> ### From Words to Action: Creating a General Narrative Planning Domain from VerbNet
>
> **Siqi Cheng** and **P@trik Haslum**
>
> *KRPlan Workshop, The 35th International Conference on Automated Planning and Scheduling*

This repository contains the source code and analysis scripts to automatically extract **STRIPS** and **PDDL**-style planning action models from **VerbNet 3.4** annotations, as described in our paper. For a quick reference, pre-generated example outputs are available in the `./examples/` directory.


# Installation

The core extraction script (`src/main.py`) relies only on standard Python libraries.

The analysis scripts in the `./analysis/` directory require additional packages for data manipulation and plotting. You can install these dependencies using your preferred package manager.

### Install dependencies for analysis:
- Using **uv**:
``` bash
uv sync
```

- Using **pip**:
```bash
pip install -r requirements.txt
```


# Usage

To run the full extraction pipeline as described in the paper, execute the main script:

``` bash
python src/main.py
```

This script will process the VerbNet 3.4 data and generate four distinct outputs in the `./output/` directory:

| Output File | Description |
| - | - |
| `extracted_example_texts.json`| A collection of all example sentences from verbnet 3.4. |
| `extracted_unfiltered_STRIPS.json`| All action models extracted from VerbNet in STRIPS format. |
| `extracted_filtered_STRIPS.json`| The filtered action models in STRIPS format after the deduplication process. | 
| `extracted_PDDL.json`| The filtered action models in PDDL format. |
| `extracted_unfiltered_STRIPS.log`| A human-readable record of unfiltered action models. |


# Analysis

The Jupyter Notebooks in the `./analysis/` directory were used to generate the statistics presented in our paper.

| Analysis Notebooks | Description |
| - | - |
|`verbnet_class_and_frames.ipynb` | Counts the number of verb classes and frames in VerbNet 3.4 |
| `verbnet_predicates.ipynb` | Analyses the predicates distribution in VerbNet 3.4 |
| `verbnet_themroles.ipynb` | Analyses the thematic role in VerbNet 3.4 |
| `extracted_counting.ipynb` | Provides statistics on the number of action models we extracted |
| `extracted_links.ipynb` | Evaluates the precondition-effect connectivity between extracted models |
