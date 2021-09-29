import setuptools

with open("README.md") as file:
    long_description = file.read()

setuptools.setup(
    name="pegpog",
    version="0.1",
    license="MIT",
    author="George Zhang",
    author_email="geetransit@gmail.com",
    description="Parse strings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GeeTransit/pegpog",
    packages=["pegpog"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Text Processing :: General",
    ],
)
