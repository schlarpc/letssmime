from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='letssmime',
    version='0.1.0',
    description="Let's S/MIME",
    long_description=readme,
    author='Chaz Schlarp',
    author_email='schlarpc@gmail.com',
    url='https://github.com/schlarpc/letssmime',
    license=license,
    packages=find_packages(),
    install_requires=[
        'cryptography',
        'asn1crypto',
        'requests',
    ],
)
