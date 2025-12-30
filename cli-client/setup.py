from setuptools import setup, find_packages

setup(
    name='se2534',
    version='0.1',
    packages=find_packages('cli-client'), 
    py_modules=['main'], 
    entry_points={
        'console_scripts': [
            'se2534=main:main',
        ],
    },
    install_requires=[
        'requests',
    ],
)