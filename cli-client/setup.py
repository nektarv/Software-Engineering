from setuptools import setup

setup(
    name='se2534',
    version='0.1',
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
