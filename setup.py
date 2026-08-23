"""
CreditScoreV4 ML Governance — Setup Configuration
=================================================

Production ML Governance Framework for Consumer Lending
Python 3.11+ | Windows/Linux/Mac Compatible

Path: D:\GitHub Project\creditscorev4-ml-governance\setup.py
"""

from pathlib import Path
from setuptools import setup, find_packages

# ─────────────────────────────────────────────────────────────────────────────
# Project Metadata
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_NAME = "creditscorev4-ml-governance"
PROJECT_VERSION = "4.2.1"
PROJECT_AUTHOR = "ML Engineering Team"
PROJECT_EMAIL = "ml-eng@company.com"
PROJECT_DESCRIPTION = "Production ML Governance Framework for Credit Scoring"
PROJECT_URL = "https://github.com/company/creditscorev4-ml-governance"
PROJECT_LICENSE = "MIT"

# ─────────────────────────────────────────────────────────────────────────────
# Read Files
# ─────────────────────────────────────────────────────────────────────────────

def read_file(filename: str) -> str:
    """Read file content safely."""
    filepath = Path(__file__).parent / filename
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return ""


def read_requirements(filename: str = "requirements-fixed.txt") -> list:
    """Parse requirements file, skipping comments and empty lines."""
    content = read_file(filename)
    requirements = []
    for line in content.splitlines():
        line = line.strip()
        # Skip comments, empty lines, and section headers
        if not line or line.startswith("#") or line.startswith("-") or line.startswith("="):
            continue
        # Skip editable installs and URLs
        if line.startswith("-e") or line.startswith("http"):
            continue
        requirements.append(line)
    return requirements


# ─────────────────────────────────────────────────────────────────────────────
# Package Discovery
# ─────────────────────────────────────────────────────────────────────────────

def get_package_data() -> dict:
    """Define non-Python files to include in the package."""
    return {
        "": [
            "*.yaml",
            "*.yml",
            "*.json",
            "*.csv",
            "*.txt",
            "*.md",
        ],
        "configs": ["*.yaml", "*.yml"],
        "docs": ["*.md"],
    }


def get_entry_points() -> dict:
    """Define CLI entry points for the package."""
    return {
        "console_scripts": [
            # Data pipeline
            "csv4-ingest=src.data_ingestion.cli:main",
            "csv4-validate=src.data_validation.cli:main",

            # Model operations
            "csv4-train=src.model_training.cli:main",
            "csv4-evaluate=src.model_training.evaluate:main",

            # Serving
            "csv4-serve=src.serving_api.cli:main",
            "csv4-api=src.serving_api.main:run_server",

            # Monitoring & deployment
            "csv4-deploy=src.deployment.cli:main",
            "csv4-monitor=src.monitoring.cli:main",
            "csv4-drift=src.drift_detection.cli:main",
            "csv4-fairness=src.fairness_monitoring.cli:main",

            # Incident response
            "csv4-incident=src.incident_response.cli:main",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# Classifiers
# ─────────────────────────────────────────────────────────────────────────────

CLASSIFIERS = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
]


# ─────────────────────────────────────────────────────────────────────────────
# Extra Dependencies
# ─────────────────────────────────────────────────────────────────────────────

EXTRAS_REQUIRE = {
    # Development tools
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "hypothesis>=6.82.0",
        "factory-boy>=3.3.0",
        "black>=23.7.0",
        "isort>=5.12.0",
        "flake8>=6.1.0",
        "mypy>=1.5.0",
        "pre-commit>=3.3.3",
    ],

    # Airflow (install separately to avoid conflicts)
    "airflow": [
        "apache-airflow>=2.7.0",
        "apache-airflow-providers-postgres>=5.0.0",
        "apache-airflow-providers-redis>=3.0.0",
    ],

    # GPU support
    "gpu": [
        "xgboost[gpu]>=1.7.6",
    ],

    # All extras
    "all": [],
}

# Populate "all" with all extras
EXTRAS_REQUIRE["all"] = list(set(
    dep for deps in EXTRAS_REQUIRE.values() for dep in deps
))


# ─────────────────────────────────────────────────────────────────────────────
# Setup Configuration
# ─────────────────────────────────────────────────────────────────────────────

setup(
    # Basic metadata
    name=PROJECT_NAME,
    version=PROJECT_VERSION,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    description=PROJECT_DESCRIPTION,
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url=PROJECT_URL,
    license=PROJECT_LICENSE,

    # Package discovery
    packages=find_packages(
        where="src",
        exclude=[
            "tests",
            "tests.*",
            "notebooks",
            "notebooks.*",
            "docs",
            "terraform",
            "docker",
            "scripts",
        ],
    ),
    package_dir={"": "src"},
    package_data=get_package_data(),
    include_package_data=True,
    zip_safe=False,

    # Dependencies
    python_requires=">=3.10",
    install_requires=read_requirements("requirements-fixed.txt"),
    extras_require=EXTRAS_REQUIRE,

    # Entry points
    entry_points=get_entry_points(),

    # Metadata
    classifiers=CLASSIFIERS,
    keywords=[
        "machine-learning",
        "mlops",
        "credit-scoring",
        "fairness",
        "governance",
        "drift-detection",
        "data-validation",
        "great-expectations",
        "xgboost",
        "airflow",
        "mlflow",
    ],

    # Project URLs
    project_urls={
        "Bug Reports": f"{PROJECT_URL}/issues",
        "Source": PROJECT_URL,
        "Documentation": f"{PROJECT_URL}/wiki",
    },
)


# ─────────────────────────────────────────────────────────────────────────────
# Post-Install Verification (Optional)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  {PROJECT_NAME} v{PROJECT_VERSION}")
    print(f"{'='*60}")
    print(f"  Setup complete!")
    print(f"  Install with: pip install -e .")
    print(f"  Or with extras: pip install -e '.[dev,airflow]'")
    print(f"{'='*60}\n")