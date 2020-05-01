from setuptools import setup, find_packages


author = "randydu"
package_name = "beebird"
packages = find_packages()


with open("README.md", "r") as fh:
    long_description = fh.read()

def extract_version(filename):
    import re
    pattern = re.compile(r'''__version__\s*=\s*"(?P<ver>[0-9\.]+)".*''')
    with open(filename, 'r') as fd:
        for line in fd:
            match = pattern.match(line)
            if match:
                ver = match.groupdict()['ver']
                break
        else:
            raise Exception('ERROR: cannot find version string.')
    return ver

version = extract_version('%s/__init__.py' % package_name)

url = "https://github.com/%s/%s.git" % (author, package_name)
download_url = "https://github.com/%s/%s/archive/v%s.tar.gz" % (author, package_name, version)

setup(name=package_name, 
    packages=packages,
    version=version,
    description = "task running platform for python 3",
    long_description = long_description,
    long_description_content_type="text/markdown",
    url=url,
    download_url = download_url,
    author = author,
    author_email= "randydu@gmail.com",
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