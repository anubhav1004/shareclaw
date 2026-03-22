from setuptools import setup, find_packages

setup(
    name="shareclaw",
    version="0.1.0",
    description="Shared memory + self-improving loops for multi-agent AI systems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Anubhav Mishra",
    url="https://github.com/anubhav1004/shareclaw",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "shareclaw=shareclaw.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
