# ppginf-ufpr-production

A Python tool to collect and store Thesis and Dissertation publications from a DSpace system and generate a markdown table summarizing each extracted document.

## Features

- Extracts thesis and dissertation metadata from DSpace repositories
- Generates markdown tables with publication summaries
- Configurable via environment variables
- Supports DSpace REST API (versions 6.x and 7.x)

## Requirements

- Python 3.6 or higher
- Access to a DSpace repository

## Installation

1. Clone this repository:
```bash
git clone https://github.com/BrunoMeyer/ppginf-ufpr-production.git
cd ppginf-ufpr-production
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on the example:
```bash
cp .env.example .env
```

4. Edit `.env` and configure your DSpace settings:
```
DSPACE_ENDPOINT=https://your-dspace-instance.org
COMMUNITY_ID=your-community-uuid
SUBCOMMUNITY_ID=your-subcommunity-uuid  # Optional
OUTPUT_FILE=production_summary.md
```

## Configuration

The following environment variables can be set in the `.env` file:

- `DSPACE_ENDPOINT` (required): Base URL of your DSpace instance
- `COMMUNITY_ID` (required): UUID of the community to extract from
- `SUBCOMMUNITY_ID` (optional): UUID of a specific subcommunity
- `OUTPUT_FILE` (optional): Name of the output markdown file (default: `production_summary.md`)

## Usage

Run the main script:
```bash
python main.py
```

This will:
1. Connect to the DSpace instance
2. Fetch all items from the specified community/subcommunity
3. Extract metadata (author, title, URL, summary) from each item
4. Generate a markdown table with the publication summaries
5. Save the output to the specified file

## Output Format

The generated markdown file contains a table with the following columns:

- **Author**: The author(s) of the thesis/dissertation
- **Title**: The title of the work
- **URL**: Link to the document file or handle
- **Summary**: Abstract or description (truncated to 200 characters)

Example output:
```markdown
# Thesis and Dissertation Production Summary

Total publications: 10

| Author | Title | URL | Summary |
|---|---|---|---|
| John Doe | Machine Learning Applications | [Link](https://...) | This thesis explores... |
```

## Project Structure

- `main.py`: Main script to orchestrate the extraction and generation
- `dspace_client.py`: DSpace API client for fetching publications
- `markdown_generator.py`: Markdown table generator
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment configuration

## License

MIT License