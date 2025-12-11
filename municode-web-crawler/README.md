# Municode Web Crawler

A Selenium-based web scraper for automatically downloading county ordinance PDFs from [Municode Library](https://library.municode.com). This crawler is designed to run in Google Colab and saves PDFs directly to Google Drive.

**Location**: `rag-pipeline/municode-web-crawler/`

## Overview

This crawler is the **data collection component** for the RAG pipeline. It automates the download of legal ordinance PDFs from Municode's online library, which are then processed by the data engineering pipeline.

**Workflow:**
```
Municode Web Crawler → PDFs in Google Drive → Upload to S3 → Data Engineering Pipeline
```

## Features

- **Automated PDF Downloads**: Scrapes county-level ordinances from Municode Library
- **State-Specific Crawling**: Currently configured for Georgia (easily adaptable to other states)
- **County Detection**: Automatically filters for county-level municipalities (vs. cities)
- **Google Drive Integration**: Saves PDFs directly to your Google Drive
- **Robust Error Handling**: Handles stale elements, timeouts, and session failures
- **Download Tracking**: Logs failed URLs for manual retry
- **Google Colab Optimized**: Runs in free Colab environment with pre-configured Chrome/Selenium

## Prerequisites

- Google Account (for Google Colab and Drive)
- Basic Python knowledge
- (Optional) AWS credentials if uploading directly to S3

## How to Use

### Step 1: Open in Google Colab

1. Upload `municode_crawler.ipynb` to your Google Drive
2. Right-click → Open with → Google Colab

### Step 2: Configure Download Location

Edit the `DOWNLOAD_DIR` variable in the notebook:

```python
# Change this to your preferred Google Drive folder
DOWNLOAD_DIR = "/content/drive/MyDrive/municode_downloads"
```

### Step 3: Run the Notebook

**Option A: Run All Cells**
- Click `Runtime → Run all`
- The notebook will:
  1. Install Chrome and Selenium
  2. Mount your Google Drive
  3. Scrape all Georgia county ordinances
  4. Save PDFs to your Drive folder

**Option B: Run Cell by Cell**
1. Run Cell 1: Install dependencies (Chrome, Selenium)
2. Run Cell 4: Main scraper code
3. Monitor progress in the output

### Step 4: Wait for Downloads

The crawler will:
- Navigate to https://library.municode.com/ga
- Identify county-level municipalities
- Click download buttons for each county's ordinances
- Save PDFs to your Google Drive folder
- Wait for all downloads to complete (up to 15 minutes)

### Step 5: Handle Failed Downloads

If any URLs fail, check:
```
/content/drive/MyDrive/municode_downloads/failed_urls.txt
```

You can manually retry these URLs or re-run the notebook.

## Configuration

### Target Different States

To scrape a different state, change the URL in the main code:

```python
# For Florida:
driver.get("https://library.municode.com/fl")

# For California:
driver.get("https://library.municode.com/ca")

# For Texas:
driver.get("https://library.municode.com/tx")
```

### County Detection Logic

The crawler identifies counties using these patterns:

```python
def is_county_level(name: str, url: str) -> bool:
    county_terms = [" county", " parish", " borough"]
    return any(t in name.lower() for t in county_terms)
```

**Examples of detected counties:**
- "Fulton County" ✅
- "DeKalb County" ✅
- "Atlanta" ❌ (city, not county)

### Adjust Download Timeout

Change the maximum wait time for downloads (default: 15 minutes):

```python
# In the final waiting loop:
if time.time() - start > 900:  # 900 seconds = 15 minutes
    print("!!! Timeout waiting for downloads")
    break
```

## How It Works

### 1. Chrome Setup
```python
# Headless Chrome with custom download directory
chrome_opts.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
    "download.prompt_for_download": False,
})
```

### 2. Page Navigation
```python
# Navigate to state page
driver.get("https://library.municode.com/ga")

# Find all municipality links
elements = wait.until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li a.index-link"))
)
```

### 3. County Filtering
```python
# Filter for county-level entries
county_links = [(n,u) for (n,u) in links if is_county_level(n,u)]
```

### 4. Download Triggering
```python
# For each county page:
# 1. Find download buttons
visible_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-pdf-download")

# 2. Click button to open modal
current_visible[i].click()

# 3. Click modal download button
modal_btn = wait.until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.get-pdf-download-btn"))
)
modal_btn.click()
```

### 5. Download Completion Waiting
```python
# Wait for .crdownload files to finish
while any(f.endswith(".crdownload") for f in os.listdir(DOWNLOAD_DIR)):
    time.sleep(5)
```

## Output

### Downloaded Files

PDFs are saved to your Google Drive with filenames like:
```
Fulton_County_GA_Code_of_Ordinances.pdf
DeKalb_County_GA_Code_of_Ordinances.pdf
Gwinnett_County_GA_Code_of_Ordinances.pdf
```

### Failed URLs Log

If any downloads fail:
```
/content/drive/MyDrive/municode_downloads/failed_urls.txt

https://library.municode.com/ga/fulton_county
https://library.municode.com/ga/dekalb_county
```

## Transferring to S3 (Next Step)

After downloading PDFs to Google Drive, upload them to S3 for processing:

> **⚠️ Important:** The S3 path is **state-specific**. Update the state code (`ga/`, `fl/`, `ca/`, `tx/`) in the S3 path to match the state you scraped. This ensures proper organization and processing by the data engineering pipeline.

### Option 1: Using AWS CLI in Colab

Add a cell to the notebook:

```python
# Install AWS CLI
!pip install awscli

# Configure credentials
import os
os.environ['AWS_ACCESS_KEY_ID'] = 'your_access_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'your_secret_key'

# Upload to S3 (UPDATE STATE CODE: ga, fl, ca, tx, etc.)
!aws s3 sync {DOWNLOAD_DIR} s3://your-bucket/input/pdfs/ga/ \
    --exclude "*.txt" \
    --exclude "*.crdownload"
```

**For other states, change the path:**
```python
# For Florida:
!aws s3 sync {DOWNLOAD_DIR} s3://your-bucket/input/pdfs/fl/ \
    --exclude "*.txt" \
    --exclude "*.crdownload"

# For California:
!aws s3 sync {DOWNLOAD_DIR} s3://your-bucket/input/pdfs/ca/ \
    --exclude "*.txt" \
    --exclude "*.crdownload"

# For Texas:
!aws s3 sync {DOWNLOAD_DIR} s3://your-bucket/input/pdfs/tx/ \
    --exclude "*.txt" \
    --exclude "*.crdownload"
```

### Option 2: Manual Download + Upload

1. Download PDFs from Google Drive to your local machine
2. Upload to S3 using AWS Console or CLI (**remember to update the state code**):
   ```bash
   # For Georgia:
   aws s3 cp municode_downloads/ s3://your-bucket/input/pdfs/ga/ --recursive

   # For Florida:
   aws s3 cp municode_downloads/ s3://your-bucket/input/pdfs/fl/ --recursive

   # For California:
   aws s3 cp municode_downloads/ s3://your-bucket/input/pdfs/ca/ --recursive

   # For Texas:
   aws s3 cp municode_downloads/ s3://your-bucket/input/pdfs/tx/ --recursive
   ```

## Troubleshooting

### Chrome Installation Fails

```bash
# Error: dpkg: error processing package
```

**Solution:** Re-run the first cell. Colab sometimes has transient package issues.

### Google Drive Mount Fails

```bash
# Error: Drive not mounted
```

**Solution:**
1. Click the link that appears
2. Allow Google Colab to access your Drive
3. Re-run the cell

### Download Buttons Not Found

```bash
# Found 0 visible download button(s).
```

**Possible causes:**
- Municode changed their HTML structure → Update CSS selectors
- County page doesn't have downloadable ordinances → Expected behavior
- Page didn't load fully → Increase `WebDriverWait` timeout

### Session Died Error

```bash
# SESSION DIED.
```

**Solution:**
- Colab runtime crashed or was disconnected
- Reconnect and re-run from the beginning
- Failed URLs are saved in `failed_urls.txt` for retry

### Downloads Stuck at `.crdownload`

```bash
# !!! Timeout waiting for downloads
```

**Possible causes:**
- Very large PDF files taking >15 minutes
- Network issues in Colab
- Municode server throttling

**Solutions:**
- Increase timeout from 900 to 1800 seconds
- Check Google Drive quota (free accounts have 15GB limit)
- Manually complete downloads from failed URLs

## Advanced Usage

### Scrape Specific Counties Only

Modify the filtering logic:

```python
# Only process specific counties
target_counties = ["fulton county", "dekalb county", "gwinnett county"]
county_links = [
    (n,u) for (n,u) in links
    if is_county_level(n,u) and any(t in n.lower() for t in target_counties)
]
```

### Add Rate Limiting

To be respectful to Municode's servers:

```python
import random

# After each download:
time.sleep(random.uniform(3, 7))  # Random delay 3-7 seconds
```

### Save Metadata

Track download metadata:

```python
import json

metadata = []
for name, url in county_links:
    metadata.append({
        "name": name,
        "url": url,
        "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"  # or "failed"
    })

with open(f"{DOWNLOAD_DIR}/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

## Known Limitations

1. **Google Colab Runtime**: Limited to 12-hour sessions (disconnects after)
2. **Drive Storage**: Free accounts have 15GB limit
3. **Municode Structure**: If Municode changes their HTML, CSS selectors need updating
4. **Download Speed**: Colab network speed varies (typically 10-50 Mbps)
5. **Single-Threaded**: Downloads are sequential, not parallel
6. **No Resume**: If interrupted, must restart (unless using failed_urls.txt)

## Integration with RAG Pipeline

After collecting PDFs:

1. **Upload to S3**: Transfer PDFs to your S3 bucket
   ```bash
   s3://your-bucket/input/pdfs/ga/
   ```

2. **Run Data Engineering Pipeline**: Extract text from PDFs
   ```bash
   cd ../data-engineering
   python main.py --state georgia --county fulton
   ```

3. **Generate Embeddings**: Create vector embeddings
   ```bash
   cd ../pinecone-embedding
   uv run python src/rag_ingest/ingest.py
   ```

4. **Query via API**: Search ordinances
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "dog leash regulations", "filters": {"locations": [{"state": "ga"}]}}'
   ```

## Performance

**Expected Results for Georgia:**
- **Counties**: ~159 counties in Georgia
- **Download Time**: 2-4 hours (depends on file sizes and Colab speed)
- **Total Size**: ~5-10GB of PDFs
- **Success Rate**: ~95% (some counties may not have downloadable ordinances)

## Future Improvements

- [ ] Add multi-state support (batch download for CA, FL, GA, TX)
- [ ] Implement parallel downloads using threading
- [ ] Add progress bar (tqdm)
- [ ] Direct S3 upload (bypass Google Drive)
- [ ] Resume capability (track completed counties)
- [ ] Better error recovery (retry logic with exponential backoff)
- [ ] Deduplication (skip already downloaded PDFs)

## Related Documentation

- [Data Engineering Pipeline](../data-engineering/README.md) - Process downloaded PDFs
- [Pinecone Embedding Pipeline](../pinecone-embedding/README.md) - Generate embeddings
- [RAG Query API](../rag-query/README.md) - Query ordinances

## License

[Add your license here]

---

**Note:** This crawler is for educational and research purposes. Be respectful of Municode's servers and terms of service. Consider adding rate limiting and user-agent headers for production use.
