from setuptools import setup, find_packages

setup(
    name="smart-object-storage",
    version="0.1.0",
    description="Production-ready semantic search and RAG system on top of object storage",
    author="Smart Storage Team",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pymilvus>=2.3.5",
        "psycopg2-binary>=2.9.9",
        "sqlalchemy>=2.0.25",
        "kafka-python>=2.0.2",
        "boto3>=1.34.28",
        "minio>=7.2.3",
        "sentence-transformers>=2.3.1",
        "pypdf>=4.0.1",
        "python-docx>=1.1.0",
        "pyyaml>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.4",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
)
