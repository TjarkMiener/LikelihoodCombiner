# LikelihoodCombiner: Combining likelihoods from different experiments.

![Gloryduck logo](images/Gloryduck_logo.png)

**LikelihoodCombiner** is a package under active development to combine likelihoods from different experiments. The main target of this package is the **Gloryduck** project. This project joint analysis of gamma-ray data from [*Fermi*-LAT](https://glast.sites.stanford.edu/), [HAWC](https://www.hawc-observatory.org/), [H.E.S.S.](https://www.mpi-hd.mpg.de/hfm/HESS/), [MAGIC](https://magic.mpp.mpg.de/) and [VERITAS](https://veritas.sao.arizona.edu/) to search for gamma-ray signals from dark matter annihilation in dwarf satellite galaxies.

## Install LikelihoodCombiner

### Clone Repository with Git

Clone the LikelihoodCombiner repository:

```bash
cd </installation/path>
git clone https://github.com/TjarkMiener/likelihood_combiner
```

### Install Package with Anaconda

Next, download and install [Anaconda](https://www.anaconda.com/download/), or, for a minimal installation, [Miniconda](https://conda.io/miniconda.html). Create a new conda environment that includes all the dependencies for LikelihoodCombiner:

```bash
conda env create -f </installation/path>/likelihood_combiner/environment.yml
```

Finally, install LikelihoodCombiner into the new conda environment with pip:

```bash
conda activate lklcom
cd </installation/path>/likelihood_combiner
pip install --upgrade .
```
NOTE for developers: If you wish to fork/clone the respository and make changes to any of the LikelihoodCombiner modules, the package must be reinstalled for the changes to take effect.

### Dependencies

- Python 3.X
- NumPy
- SciPy
- Pandas
- PyTables
- PyYAML
- Matplotlib
  
## Run the Combiner

Run LikelihoodCombiner from the command line:
  
```bash
LikelihoodCombiner_dir=</installation/path>/likelihood_combiner
python $LikelihoodCombiner_dir/likelihood_combiner/combiner.py $LikelihoodCombiner_dir/config/config.yml 
```
  
Alternatively, import LikelihoodCombiner as a module in a Python script:
  
```python
import yaml
from likelihood_combiner.combiner import run_combiner
  
with open('</installation/path>/config/config.yml', 'r') as myconfig:
    config = yaml.safe_load(myconfig)
run_combiner(config)
```
  
## Uninstall LikelihoodCombiner

### Remove Anaconda Environment

First, remove the conda environment in which LikelihoodCombiner is installed and all its dependencies:

```bash
conda remove --name lklcom --all
```

### Remove LikelihoodCombiner

Next, completely remove LikelihoodCombiner from your system:

```bash
rm -rf </installation/path>/likelihood_combiner
```
