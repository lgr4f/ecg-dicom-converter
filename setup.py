from setuptools import setup, find_packages

setup(
    name='ecg-dicom-converter',
    version='0.1.1',
    packages=find_packages(),
    install_requires=[
        'wfdb>=3.3.0',
        'numpy>=1.18.4',
        'pydicom>=2.1.0'
    ],
    entry_points={
        'console_scripts': [
            'ecg-dicom-converter=scripts.cli:main',  # This should match the actual package and module names
        ],
    },
    author='Lennart Graf',
    author_email='frederiklennart.graf@med.uni-goettingen.de',
    description='A package for extracting ECG data and converting it to DICOM format.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://your-repo-url.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
