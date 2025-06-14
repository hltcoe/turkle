import setuptools

with open("turkle/__init__.py") as fp:
    ns = {}
    exec(fp.read(), ns)

with open("README.md") as fp:
    long_description = fp.read()

with open('requirements.txt') as f:
    requirements = [line.strip() for line in f]

setuptools.setup(
    name="turkle",
    version=ns["__version__"],
    description="Django-based clone of Amazon's Mechanical Turk service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hltcoe/turkle",
    project_urls={
        "Documentation": "https://turkle.readthedocs.io/",
    },
    author="Craig Harman",
    author_email="craig@craigharman.net",
    license="BSD",
    packages=setuptools.find_packages(exclude=['turkle_site', 'turkle.tests']),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
    keywords=['annotation', 'crowdsourcing', 'mturk', 'mechanical turk'],
)
