# Installation

## Important!

We strongly recommend installing each new version of Vesper into its own Conda environment (see the [Background](#background) section below if you're new to Conda environments). This has several advantages, including allowing you to easily revert to a previously installed Vesper version if you encounter problems with a new one.

## Installing Vesper

To install the most recent version of Vesper in a new Conda environment:

1. If you don't have one of them already, download and install either the [Miniconda](http://conda.pydata.org/miniconda.html) or the [Anaconda](https://www.anaconda.com/distribution/) Python 3 distribution.

2. Open a Windows `Anaconda Prompt` or Unix terminal.

3. Create a new Conda environment for Vesper and install various Vesper dependencies in it by issuing the command:

        conda create -n vesper-0.4.7 -c defaults -c conda-forge django=2.1 h5py jsonschema librosa pandas pyephem python=3.6 "pyyaml<5.1" resampy scikit-learn sqlite=3.25

    Conda will display a list of packages that it proposes to install, including those listed in the command and others on which they depend. Press the `Return` key to accept.

4. Activate the environment you just created with:

        conda activate vesper-0.4.7

5. Install TensorFlow and Keras packages into the new environment with:

        pip install tensorflow==1.12 keras

    Here we recommend using `pip` rather than `conda` for the installation since the installed TensorFlow package performs better on many computers than the one you get with `conda`.

6. Finally, install the Vesper package into the environment with:

        pip install vesper

   You must use `pip` here rather than `conda` since `pip` was used in the previous step.


## Background

The instructions on this page assume that you will use Vesper in conjunction with either the [Miniconda](http://conda.pydata.org/miniconda.html) or the [Anaconda](https://www.anaconda.com/distribution/) Python 3 distribution. Note that Vesper requires Python 3: it cannot run on Python 2 interpreters. We recommend Miniconda and Anaconda mainly due to their superior package management functionality, which makes it relatively easy to install and maintain both Vesper and its dependencies. Miniconda and Anaconda also offer excellent environment management functionality, which you can read more about in the [Conda Environments](#conda-environments) section below.

Miniconda and Anaconda are both free and open source, and are offered by [Continuum Analytics](https://www.continuum.io), a software company that specializes in scientific applications of the Python programming language. Anaconda includes many packages, some of which Vesper uses but most of which it doesn't. Miniconda is much smaller than Anaconda, including only a minimal set of packages. Either Miniconda or Anaconda is fine for Vesper use.

### Conda Environments
Miniconda and Anaconda both include a command line program called [Conda](https://conda.io/en/latest/index.html). You can use Conda to manage multiple Python *environments* within your Miniconda or Anaconda installation, where each environment contains a set of software *packages*. For example, we strongly recommend installing each version of Vesper that you use in its own Conda environment. Such an environment will include a Vesper package and several tens of other packages on which Vesper depends, including, for example, packages for TensorFlow, NumPy, and Python itself. Installing each version of Vesper in its own environment keeps the packages for those different versions from interfering with each other, and with other packages that you might want to install in other, non-Vesper environments.

Every Miniconda or Anaconda installation includes a default `base` environment that is created automatically on installation. We do *not* recommend installing Vesper in the `base` environment, but rather in its own environment, as discussed above.

Conda environments are fully documented in the [Managing environments](https://conda.io/projects/conda/user-guide/tasks/manage-environments.html) section of the [Conda documentation](https://conda.io/en/latest/index.html). We will describe only a few of the more common commands for managing Conda environments here.

Conda environments are managed mainly using the `conda` command line program, which you can run from either the Windows `Anaconda Prompt` or a Unix terminal. The Windows `Anaconda Prompt` program comes with Miniconda and Anaconda, and is similar to the regular `Command Prompt` program, except that it is customized for use with Miniconda and Anaconda. The `conda` commands you type are the same on all platforms. (If you are using Linux, however, note that some shell initialization is required for the `conda activate` and `conda deactivate` commands to work. Issue the `conda init --help` command for more about this.)

To create a new Conda environment, issue the command:

    conda create -n <env> <package list>

where `<env>` is the name of the new environment (for example, `vesper-1.0.0`) and `<package list>` is a list of packages that you want to install. Conda will present you with a list of the Python packages it proposes to install, including the ones you listed and any other packages that they depend upon, and ask for confirmation before proceeding.

To remove an environment named `<env>`:

    conda remove -n <env> --all

To see a list of your environments:

    conda env list

To activate the environment named `<env>` in the current Windows `Anaconda Prompt` or Unix terminal, issue the command:

    conda activate <env>

The name of the environment will subsequently appear at the beginning of each command prompt in the window.

If an environment is active in the current Windows `Anaconda Prompt` or Unix terminal, you can deactivate it with the command:

    conda deactivate