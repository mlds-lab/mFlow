.. mFlow documentation master file, created by
   sphinx-quickstart on Mon Sep  6 13:44:41 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

mFlow
=====

mFlow is a Python module for specifying and executing machine learning experimentation workflows. It organizes both 
data transformations and common experimental procedures into workflow blocks. mFlow focuses on the multi-core parallel 
setting and interoperates with machine learning model implementations that follow the 
`scikit-learn <https://github.com/scikit-learn/scikit-learn>`_ model class structure. mFlow can also interoperate 
with `Apache Spark <https://spark.apache.org/>`_ and the `MD2K <https://md2k.org/>`_ `Cerebral Cortex <https://github.com/MD2Korg/CerebralCortex-Kernel>`_ 
library to split workflow execution across a distributed pre-processing and feature extraction phase followed by a 
multi-core parallel model estimation phase. mFlow uses `Pandas <https://github.com/pandas-dev/pandas>`_ dataframes 
as the primary data structure for representing data sets and results.

mFlow supports a range of experimental workflows with a focus on multi-level data where individual data cases are nested 
within groups. It supports partitioning data sets both at the instance level and at the group level for most workflows.
Experimental designs currently supported by mFlow include:

* Train/Test performance assessment with instance-level partitioning
* Train/test performance assessment with group-level partitioning
* Cross-validation performance assessment with instance-level partitioning
* Cross-validation performance assessment with group-level partitioning
* Within group Train/Test performance assessment with random partitioning within groups 
* Within group Train/Test performance assessment with sequential partitioning within groups 

mFlow also includes a library of example workflows illustrating the application of data transformations and experimental workflows
on open data sets in the mobile health and activity recognition domains. 

Installation
------------

mFlow requires Python 3.6 or higher. To install mFlow using pip, clone this repository and run pip install:
::

    git clone https://github.com/mlds-lab/mFlow.git
    pip3 install ./mFlow


Examples
--------
See the `Examples <https://github.com/mlds-lab/mFlow/tree/master/Examples>`_ directory for a list of mFlow examples 
that can be run locally or launched in `Google Colab <https://colab.research.google.com/>`_.

Contributors
------------

Link to the `list of contributors <https://github.com/mlds-lab/mFlow/graphs/contributors>`_ who participated in this project.

License
-------

This project is licensed under the BSD 2-Clause - see the `license <https://github.com/mlds-lab/mFlow/blob/master/LICENSE>`_ file for details.

Acknowledgments
---------------

* `National Institutes of Health <https://www.nih.gov/>_` - `Big Data to Knowledge Initiative <https://datascience.nih.gov/bd2k>`_ Grant: 1U54EB020404
* `National Science Foundation <https://www.nsf.gov/>`_ Grants: 1640813, 1722646


.. toctree::
   :maxdepth: 2
   :caption: Contents:


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`