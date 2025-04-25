from setuptools import setup, find_packages

setup(
    name='ecg_dicom_converter',
    version='1.0.5',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.18.4',
        'pydicom==3.0.1'
    ],
    entry_points={
        'console_scripts': [
            'ecg_dicom_converter=ecg_dicom_converter.cli:main',  # This should match the actual package and module names
        ],
    },
    author='Lennart Graf',
    author_email='frederiklennart.graf@med.uni-goettingen.de',
    description='A package for extracting ECG data and converting it to DICOM format.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://gitlab.gwdg.de/medinfpub/mi-xnat/extensions/clients/ecg-dicom-converter',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: GNU General Public License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
