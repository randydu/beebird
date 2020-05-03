from setuptools import setup, find_packages


author = "randydu"
package_name = "beebird"
packages = find_packages()


with open("README.md", "r") as fh:
    long_description = fh.read()

from beebird import __version__, __doc__, __license__

url = "https://github.com/%s/%s.git" % (author, package_name)
download_url = "https://github.com/%s/%s/archive/v%s.tar.gz" % (author, package_name, __version__)

setup(name=package_name, 
    packages=packages,
    version=__version__,
    description = __doc__.split('\n')[0],
    long_description = long_description,
    long_description_content_type="text/markdown",
    url=url,
    download_url = download_url,
    author = author,
    author_email= "randydu@gmail.com",
    keywords=["task", "cmdlet"],
    license=__license__,
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