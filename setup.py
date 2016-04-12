from setuptools import find_packages, setup


setup(
      
    name='vesper',
    version='0.0.1',
    description=\
        'Software for acoustical monitoring of nocturnal bird migration.',
    url='https://github.com/HaroldMills/Vesper',
    author='Harold Mills',
    author_email='harold.mills@gmail.com',
    license='MIT',
    
    packages=find_packages(),
    
    # I decided to include all Python packages in the distribution,
    # including the unit tests, since that is most straightforward.
    # Prior to making that decision I tested the following for
    # excluding all packages named "tests", and it worked.
    # packages=find_packages(
    #     exclude=['tests', 'tests.*', '*.tests.*', '*.tests']),
    
    install_requires=[
        'matplotlib',
        'pandas',
        'pyephem',
        'pyyaml',
        'scikit-learn'
    ],
      
    entry_points={
        'console_scripts': [
            'vcl=vesper.vcl.vcl:main',
            'vesper_viewer=vesper.ui.vesper_viewer:main'
        ]
    },
      
    include_package_data=True,
    zip_safe=False
    
)
