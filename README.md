# AstroInsight

AI-powered academic research assistant with MCP server integration for paper analysis and research idea generation.

## Features

- **Research Paper Analysis**: Automated paper search, download, and analysis
- **Research Idea Generation**: AI-powered research idea generation with expert review
- **MCP Server Integration**: Model Context Protocol server for seamless AI assistant integration
- **Celery Task Queue**: Asynchronous task processing for heavy computations
- **Multi-format Support**: PDF to Markdown conversion, arXiv integration

## Quick Start

### Prerequisites

- Python 3.8+
- Neo4j Database
- Redis (for Celery)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/daiduo2/TaShan-SciSpark.git
cd TaShan-SciSpark
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements_mcp.txt
```

3. Configure environment variables in `.env`

### Usage

1. Start Celery Worker (for async tasks):
```bash
python start_celery_worker.py
```

2. Start MCP Server:
```bash
python mcp_server.py
```

## MCP Tools

- `search_papers` - Search academic papers
- `extract_keywords` - Extract technical keywords from text
- `generate_research_idea` - Generate research ideas (async)
- `get_task_status` - Get async task status
- `review_research_idea` - Review research ideas
- `compress_paper_content` - Compress paper content

## License

MIT License