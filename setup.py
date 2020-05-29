from setuptools import setup, find_packages

with open('README.md') as fd:
    readme = fd.read()

setup(
    name="mzmlripper",
    version="1.0.0",
    author="Graham Keenan",
    author_email="graham.keenan@glasgow.ac.uk",
    description="Extractor for MS1 and MS2 data from mzML file format",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="http://gitlab.com/croningroup/origins/mzmlripper",
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent'
    ],
    python_requires='>=3.6'
)
