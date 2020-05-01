from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name="beebird", 
    version="0.0.1",
    description = "task running platform for python 3",
    long_description = long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/randydu/beebird.git",
    author="Randy Du",
    author_email="randydu@gmail.com",
    packages=["beebird"],
    keywords=["task", "cmdlet"],
    license="MIT",
    classifiers=[
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers', 
    'Operating System :: OS Independent',
    'Topic :: Software Development :: Libraries',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'License :: OSI Approved :: MIT License',  
    'Programming Language :: Python :: 3',
  ],

)