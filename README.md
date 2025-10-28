# ppginf-ufpr-production

A tool to extract all items from collections within a DSpace community or subcommunity.

## Features

- Extracts all items from all collections in a specified community or subcommunity
- Configurable via `.env` file
- Supports DSpace REST API
- Outputs data in JSON format
- Handles pagination automatically

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BrunoMeyer/ppginf-ufpr-production.git
cd ppginf-ufpr-production
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the environment:
```bash
cp .env.example .env
```

4. Edit `.env` file with your DSpace instance details:
```env
DSPACE_API_URL=https://your-dspace-instance.edu/server/api
COMMUNITY_ID=your-community-uuid-here
```

## Usage

Run the extraction script:
```bash
python extract_items.py
```

The script will:
1. Connect to your DSpace instance
2. Fetch all collections from the specified community/subcommunity
3. Extract all items from each collection
4. Save the results to `extracted_items.json`

## Output Format

The output JSON file contains a dictionary where:
- Keys are collection names
- Values contain:
  - `collection_id`: The collection's ID
  - `collection_uuid`: The collection's UUID
  - `collection_handle`: The collection's handle
  - `items`: Array of items with their metadata

Example:
```json
{
  "Collection Name": {
    "collection_id": "abc-123",
    "collection_uuid": "uuid-here",
    "collection_handle": "123456789/123",
    "items": [
      {
        "id": "item-id",
        "uuid": "item-uuid",
        "name": "Item Name",
        "handle": "123456789/456",
        "metadata": {
          "dc.title": ["Item Title"],
          "dc.creator": ["Author Name"],
          ...
        }
      }
    ]
  }
}
```

## Configuration

### Required Environment Variables

- `DSPACE_API_URL`: The base URL of your DSpace REST API (e.g., `https://dspace.example.edu/server/api`)
- `COMMUNITY_ID`: The UUID of the community or subcommunity to extract items from

### Optional Environment Variables

- `DSPACE_EMAIL`: Email for authentication (if your DSpace instance requires authentication)
- `DSPACE_PASSWORD`: Password for authentication (if your DSpace instance requires authentication)

## Requirements

- Python 3.6+
- requests
- python-dotenv

## License

MIT