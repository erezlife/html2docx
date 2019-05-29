from setuptools import setup


def readall(path):
    with open(path) as fp:
        return fp.read()


setup(
    name="html2docx",
    version="1.1.0",
    license="MIT",
    description="Convert valid HTML input to docx",
    long_description=readall("README.md"),
    long_description_content_type="text/markdown",
    author="eRezLife",
    author_email="noreply@erezlife.com",
    maintainer="eRezLife",
    maintainer_email="noreply@erezlife.com",
    url="https://github.com/erezlife/html2docx",
    py_modules=["html2docx"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=["python-docx"],
)
