from os import path
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

reqs = [
    'matplotlib>=2.2.2',    
    'requests>=2.12.4',
    'scipy>=1.2.0',
    'numpy>=1.15.4',
    'joblib>=0.13.1',
    'pandas>=0.23.0',
    'networkx>=2.4',
    'scikit-learn>=0.20.2',
    'pydot',
    'cerebralcortex-kernel>=3.3.10'
]

# Get the long description from the README file
long_description = "The MD2K mFlow machine learning experimental workflow system."

if __name__ == '__main__':
    setup(
        name="mFlow",

        version='1.0.0',

        package_data={'': ['default.yml']},

        description="The MD2K mFlow machine learning experimental workflow system.",
        long_description_content_type='text/markdown',
        long_description=long_description,

        author='MD2K.org',
        author_email='dev@md2k.org',

        license='BSD2',
        url = 'https://github.com/mlds-lab/mFlow/',

        classifiers=[

            'Development Status :: 5 - Production/Stable',

            'Intended Audience :: Healthcare Industry',
            'Intended Audience :: Science/Research',

            'License :: OSI Approved :: BSD License',

            'Natural Language :: English',

            'Programming Language :: Python :: 3',

            'Topic :: Scientific/Engineering :: Information Analysis',
            'Topic :: System :: Distributed Computing'
        ],

        keywords='mHealth machine-learning data-analysis',

        # You can just specify the packages manually here if your project is
        # simple. Or you can use find_packages().
        package_dir={"": "mFlow"},
        packages=find_packages(exclude=['contrib', 'docs', 'tests','Examples']),

        # List run-time dependencies here.  These will be installed by pip when
        # your project is installed. For an analysis of "install_requires" vs pip's
        # requirements files see:
        # https://packaging.python.org/en/latest/requirements.html
        install_requires=reqs,


        entry_points={
            'console_scripts': [
                'main=main:main'
            ]
        },

    )