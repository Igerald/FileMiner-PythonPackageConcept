import setuptools

with open("README.md",'r') as f:
    long_text = f.read()

setuptools.setup(
    name = "FileMiner",
    version = "1.0.0",
    author = "Isaiah Gerald",
    author_email = "e0dasci@gmail.com",
    description = "pkg-template-description",
    long_description = long_text,
    long_description_content_type = "text/markdown",
    url = "https://github.com/pypa/sampleproject",
    packages = setuptools.find_packages(),
    classifiers = ["Programming Language :: Python :: 3",
                   "License :: OSI Approved :: MIT License",
                   "Operating System :: OS Independent",],
    )
