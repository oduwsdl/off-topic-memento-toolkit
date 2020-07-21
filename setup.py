from setuptools import setup
from setuptools.command.install import install as _install
from os import path

# to get pylint to shut up
__appname__ = None
__appversion__ = None

# __appname__, __appversion__, and friends come from here
exec(open("otmt/version.py").read())

# Python packaging info: http://python-packaging.readthedocs.io/en/latest/index.html
# More Python packaging info: http://python-packaging-user-guide.readthedocs.io/tutorials/distributing-packages/
# Python version info: https://www.python.org/dev/peps/pep-0440/

# Thanks https://stackoverflow.com/questions/26799894/installing-nltk-data-in-setup-py-script
# for detailing how to install nltk data as part of setup.py
# Thanks https://blog.niteoweb.com/setuptools-run-custom-code-in-setup-py/
# for detailing how to fix what that solution broke
class Install(_install):
    def run(self):
        _install.run(self)
        import nltk
        nltk.download("stopwords")
        nltk.download("punkt")

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=__appname__.lower(),
    cmdclass={'install': Install},
    version=__appversion__,
    description='Tools for determining if web archive collecions are Off-Topic',
    long_description_content_type="text/markdown",
    long_description=long_description,
    url='https://github.com/oduwsdl/off-topic-memento-toolkit',
    author='Shawn M. Jones',
    author_email='jones.shawn.m@gmail.com',
    license='MIT',
    packages=['otmt'],
    scripts=[
        'bin/detect_off_topic',
        'bin/exclude_duplicates',
        'bin/select_by_language',
        'bin/slice_by_datetime',
        'bin/cluster_by_simhash',
        'bin/select_high_quality'
    ],
    install_requires=[
        'aiu',
        'bs4',
        'distance',
        'gensim',
        'html5lib',
        'justext',
        'langdetect',
        'lxml',
        'nltk',
        'numpy',
        'paramiko',
        'requests',
        'requests_cache',
        'requests_futures',
        'scikit-learn',
        'scipy',
        'simhash',
        'warcio'
    ],
    setup_requires=['nltk'],
    test_suite="tests",
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='webarchives memento similarity offtopic'
    )
