from setuptools import setup
from setuptools.command.install import install as _install

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

setup(name='offtopic2',
    cmdclass={'install': Install},
    version='0.9.0a0',
    description='Tools for determinine if web archive collecions are Off-Topic',
    url='http://github.com/shawnmjones/offtopic2',
    author='Shawn M. Jones',
    author_email='jones.shawn.m@gmail.com',
    license='MIT',
    packages=['otmt'],
    scripts=['bin/detect_off_topic', 'bin/download_collection'],
    install_requires=[
        'requests_futures',
        'bs4',
        'html5lib',
        'justext',
        'nltk',
        'scikit-learn',
        'distance',
        'warcio',
        'requests',
        'numpy',
        'scipy',
        'simhash',
        'gensim'
    ],
    setup_requires=['nltk'],
    test_suite="tests",
    zip_safe=True
    )