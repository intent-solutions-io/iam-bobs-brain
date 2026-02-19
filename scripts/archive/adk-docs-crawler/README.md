# ADK Documentation Crawler

Production-ready crawler for extracting ADK documentation and preparing it for Bob's Brain RAG system.

## Overview

This crawler pipeline performs the following steps:

1. **Crawl** - Fetches all ADK documentation pages from https://google.github.io/adk-docs/
2. **Extract** - Parses HTML and extracts structured content (headings, text, code blocks)
3. **Chunk** - Splits content into RAG-optimized chunks (max 1500 tokens by default)
4. **Upload** - Stores results in Google Cloud Storage for RAG ingestion

## Architecture

```
tools/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── adk_docs_crawler.py      # Web crawler with rate limiting
├── adk_docs_extract.py      # Content extraction from HTML
├── adk_docs_chunker.py      # RAG-optimized chunking
├── adk_docs_uploader.py     # GCS upload and versioning
└── __main__.py              # CLI entry point
```

## Quick Start

### 1. Setup Configuration

```bash
# Copy example configuration
cp .env.crawler.example .env.crawler

# Edit configuration
nano .env.crawler
```

Required configuration:
```bash
GCP_PROJECT_ID=bobs-brain
BOB_DOCS_BUCKET=bobs-brain-adk-docs
```

### 2. Install Dependencies

```bash
# Install crawler dependencies
pip install -r requirements.txt
```

### 3. Authenticate with GCP

```bash
# For local development
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 4. Run Crawler

```bash
# Using make (recommended)
make crawl-adk-docs

# Or run directly
python -m tools

# Verbose output
python -m tools --verbose
```

## Configuration

All configuration is managed via environment variables (loaded from `.env.crawler`):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GCP_PROJECT_ID` | Yes | - | Google Cloud project ID |
| `BOB_DOCS_BUCKET` | No | `{project_id}-adk-docs` | GCS bucket name |
| `CRAWLER_SA_EMAIL` | No | - | Service account email (CI only) |
| `CRAWL_DELAY_SECONDS` | No | `1.0` | Delay between requests |
| `MAX_CHUNK_TOKENS` | No | `1500` | Maximum tokens per chunk |
| `ADK_DOCS_START_URL` | No | `https://google.github.io/adk-docs/` | Starting URL |
| `CRAWLER_TMP_DIR` | No | `./tmp` | Temporary directory |

## Output

### Local Files (tmp/)

- `tmp/adk_docs_manifest.json` - Crawl metadata and page list
- `tmp/docs.jsonl` - Extracted documents (one per line)
- `tmp/chunks.jsonl` - RAG chunks (one per line)

### GCS Structure

```
gs://{BOB_DOCS_BUCKET}/
├── adk-docs/
│   ├── raw/
│   │   └── docs.jsonl                    # Latest extracted documents
│   ├── chunks/
│   │   └── chunks.jsonl                  # Latest RAG chunks
│   └── manifests/
│       ├── crawl-manifest-latest.json    # Latest manifest
│       └── crawl-manifest-{timestamp}.json  # Timestamped history
```

## Data Formats

### Extracted Document

```json
{
  "doc_id": "abc123...",
  "url": "https://google.github.io/adk-docs/page.html",
  "title": "Page Title",
  "sections": [
    {
      "heading_path": ["H1 Title", "H2 Subtitle"],
      "text": "Section content...",
      "code_blocks": [
        {
          "language": "python",
          "code": "def example():\n    pass"
        }
      ]
    }
  ],
  "last_crawled_at": "2025-11-19T12:00:00Z",
  "source_type": "adk-docs"
}
```

### RAG Chunk

```json
{
  "chunk_id": "xyz789...",
  "doc_id": "abc123...",
  "url": "https://google.github.io/adk-docs/page.html",
  "title": "Page Title",
  "heading_path": ["H1 Title", "H2 Subtitle"],
  "text": "Chunk content...",
  "code_blocks": [],
  "last_crawled_at": "2025-11-19T12:00:00Z",
  "source_type": "adk-docs",
  "estimated_tokens": 1200
}
```

## Features

### Web Crawling
- Respects robots.txt
- Rate limiting (configurable delay between requests)
- URL normalization and deduplication
- Internal link following only
- User-agent identification

### Content Extraction
- Semantic section extraction
- Heading hierarchy preservation (H1/H2/H3)
- Code block detection with language hints
- Clean text extraction (removes nav, footer, scripts)

### RAG Chunking
- Section-based chunking
- Token limit enforcement
- Paragraph-level splitting for long sections
- Code blocks attached to first chunk
- Unique chunk IDs

### GCS Upload
- Automatic bucket validation
- JSONL format for efficient streaming
- Timestamped manifest versioning
- Atomic uploads with retry

## Makefile Targets

```bash
# Run full crawler pipeline
make crawl-adk-docs

# Test configuration without running
make crawl-test

# Install dependencies
make deps
```

## Development

### Running Tests

```bash
# Test configuration loading
python -c "from tools.config import load_config; print(load_config())"

# Test GCP credentials
python -c "from tools.config import validate_gcp_credentials; validate_gcp_credentials()"

# Dry run (no upload)
# TODO: Add --dry-run flag to __main__.py
```

### Extending the Crawler

**Add new extractors:**
1. Edit `tools/adk_docs_extract.py`
2. Add extraction logic to `ContentExtractor`

**Change chunking strategy:**
1. Edit `tools/adk_docs_chunker.py`
2. Modify `DocumentChunker.chunk_document()`

**Add new storage backends:**
1. Create `tools/adk_docs_storage_*.py`
2. Implement same interface as `GCSUploader`

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Crawl ADK Documentation
  env:
    GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
    GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
  run: |
    make crawl-adk-docs
```

## Troubleshooting

### "GCP_PROJECT_ID is required"

**Solution:** Set environment variable in `.env.crawler`:
```bash
GCP_PROJECT_ID=bobs-brain
```

### "Permission denied accessing bucket"

**Solution:** Ensure service account has Storage Object Admin role:
```bash
gcloud projects add-iam-policy-binding bobs-brain \
  --member=serviceAccount:crawler@bobs-brain.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

### "Rate limited by remote server"

**Solution:** Increase crawl delay in `.env.crawler`:
```bash
CRAWL_DELAY_SECONDS=2.0
```

### "Chunks exceed token limit"

**Solution:** Reduce max tokens in `.env.crawler`:
```bash
MAX_CHUNK_TOKENS=1000
```

## Performance

Typical crawl metrics (as of 2025-11-19):

- **Pages crawled:** ~50-100 pages
- **Total time:** ~2-5 minutes (1s delay between requests)
- **Documents extracted:** Same as pages crawled
- **Chunks generated:** 300-500 chunks
- **GCS upload time:** ~10-30 seconds

## Maintenance

### Updating Dependencies

```bash
pip install --upgrade requests beautifulsoup4 lxml google-cloud-storage
```

### Re-crawling

The crawler is idempotent and safe to re-run. It will:
- Overwrite main files (docs.jsonl, chunks.jsonl)
- Keep timestamped manifest versions
- Skip unchanged pages (future enhancement)

### Monitoring

Check GCS for latest crawl results:
```bash
gsutil ls gs://bobs-brain-adk-docs/adk-docs/manifests/
gsutil cat gs://bobs-brain-adk-docs/adk-docs/manifests/crawl-manifest-latest.json
```

## License

Part of Bob's Brain project. See top-level LICENSE.

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in `tmp/` directory
3. Contact Build Captain: claude.buildcaptain@intentsolutions.io
