from distutils.core import setup

setup(
    name='breakdancer',
    description='Generate all the tests.',
    version='1.0',
    packages=['breakdancer',],
    license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description="""BreakDancer thinks of everything so you don't have to.

See my blog post for more info:

    http://dustin.github.com/2010/10/27/breakdancer.html
""",
    url='http://github.com/dustin/breakdancer',
    author = "Dustin Sallings",
    author_email = "dustin@spy.net",
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Testing :: Traffic Generation",
        ],
)
