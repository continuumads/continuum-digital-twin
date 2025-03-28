from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="continuum-ads-digital-twin",
    version="0.1.0",
    author="Continuum Ads Team",
    author_email="info@continuumads.com",
    description="Digital advertising experimentation platform for Google, Facebook, Instagram, Twitter, LinkedIn, TikTok and Snapchat",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://continuumads.com",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Marketing",
        "Intended Audience :: Information Technology",
        "Topic :: Advertising",
        "Topic :: Scientific/Engineering :: Simulation",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "python-dateutil>=2.8.2",
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "requests>=2.26.0",
        "pyyaml>=6.0",
        "tqdm>=4.62.0",
    ],
    extras_require={
        "visualization": [
            "matplotlib>=3.4.0",
            "seaborn>=0.11.2",
            "plotly>=5.3.0",
        ],
        "dev": [
            "pytest>=6.2.5",
            "black>=21.9b0",
            "flake8>=3.9.2",
            "sphinx>=4.2.0",
        ],
    },
)
