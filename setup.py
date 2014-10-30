from setuptools import setup, find_packages


setup(name='FTPRelayer',
    version='0.2',
    description="",
    long_description="""\
    """,
    classifiers=[],
    keywords='',
    author='Meteogrid',
    author_email='alberto@meteogrid.com',
    url='',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    test_suite = "nose.collector",
    zip_safe=True,
    dependency_links = [
    ],
    install_requires=[
       "configobj",
       #"paramiko",
       "ftputil<2.7",
       "pyinotify",
       "davclient",
    ],
    extras_require = {
    },
    tests_require = ["nose", "unittest2", "mox"],
    entry_points="""
    [console_scripts]
    ftprelayer = ftprelayer:main
    """,
    )
