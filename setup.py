from setuptools import setup, find_packages

setup(
    name="obsidian-agent-rag",
    version="0.1.0",
    description="Multi-agent RAG system for Obsidian",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
        ]
    },
)
