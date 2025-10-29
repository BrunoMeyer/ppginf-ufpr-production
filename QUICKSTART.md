# Quick Start Guide

This guide will help you get started with the DSpace Thesis/Dissertation Extraction Tool.

## Prerequisites

- Python 3.6 or higher
- Access to a DSpace repository
- Community/Subcommunity UUID from your DSpace instance

## Setup (5 minutes)

### 1. Clone and Install

```bash
git clone https://github.com/BrunoMeyer/ppginf-ufpr-production.git
cd ppginf-ufpr-production
pip install -r requirements.txt
```

### 2. Configure

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your DSpace details:
```
DSPACE_ENDPOINT=https://your-dspace-instance.org
COMMUNITY_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SUBCOMMUNITY_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
OUTPUT_FILE=production_summary.md
```

**How to find your IDs:**
- Navigate to your community/collection in DSpace
- The UUID is usually in the URL: `.../handle/123456789/123` or visible in the admin panel
- Some DSpace versions show the UUID in the collection settings

### 3. Run

```bash
python main.py
```

The script will:
1. Connect to DSpace
2. Fetch all items from the specified collection
3. Extract metadata
4. Generate a markdown file

### 4. View Results

Open the generated `production_summary.md` file in any markdown viewer or text editor.

## Troubleshooting

**Error: DSPACE_ENDPOINT not set**
- Make sure you created the `.env` file
- Check that the file is in the same directory as `main.py`

**No items found**
- Verify your Community/Subcommunity IDs are correct
- Check that your DSpace instance is accessible
- Some DSpace instances require authentication (not yet supported)

**Connection errors**
- Verify the DSpace endpoint URL is correct
- Check your internet connection
- Some DSpace instances may have CORS or firewall restrictions

## Testing

Run the demo without a DSpace instance:
```bash
python demo.py
```

This will generate sample output to verify the tool is working.

Run unit tests:
```bash
python -m unittest test_markdown_generator.py
```

## Next Steps

- Customize the output format in `markdown_generator.py`
- Add filters for specific thesis types
- Schedule regular extractions with cron or Task Scheduler
- Integrate with your documentation system

## Support

For issues or questions, please file an issue on GitHub.
