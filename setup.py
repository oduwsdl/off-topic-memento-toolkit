from setuptools import setup


# Python packaging info: http://python-packaging.readthedocs.io/en/latest/index.html
# More Python packaging info: http://python-packaging-user-guide.readthedocs.io/tutorials/distributing-packages/
# Python version info: https://www.python.org/dev/peps/pep-0440/

# def offtopic_test_suite():

#     test_loader = unittest.TestLoader()
#     test_suite = test_loader.discover('tests', pattern='test_*.py')
#     return test_suite


setup(name='offtopic2',
    version='2.0.0a0',
    description='Tools for determinine if web archive collecions are Off-Topic',
    url='http://github.com/shawnmjones/offtopic2',
    author='Shawn M. Jones',
    author_email='jones.shawn.m@gmail.com',
    license='MIT',
    packages=['offtopic'],
    scripts=['bin/detect_off_topic', 'bin/download_collection'],
    install_requires=[
        'requests_futures',
        'bs4'
    ],
    # test_suite='setup.offtopic_test_suite',
    test_suite="tests"
    # zip_safe=False
    )