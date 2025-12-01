# UnBarred Streamlit App

A Streamlit-based frontend interface for **UnBarred**, a tool designed to search and analyze county ordinances. This application allows users to query legal texts across multiple states (California, Florida, Georgia, Texas) with advanced filtering capabilities for readability and legal classifications (penalties, obligations, permissions, prohibitions).

## Features

- **Multi-State Search**: Search ordinances across counties in CA, FL, GA, and TX.
- **Advanced Filtering**:
  - **Rule Filters**: Filter by specific legal attributes: Penalty, Obligation, Permission, Prohibition.
  - **Readability Metrics**: Filter results based on Flesch-Kincaid Grade, Flesch Reading Ease, Word Count, and Complexity Percentage.
- **Interactive Results**: View search results with detailed metadata and scores.
- **Data Export**: Download search results (chunks) as a CSV file.
- **Responsive UI**: sticky search bar and sidebar controls for ease of use.

## Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (optional, but recommended for dependency management) or pip.

## Installation

1. Navigate to the streamlit-app directory:
   ```bash
   cd rag-pipeline/streamlit-app
   ```

2. Install dependencies:
   ```bash
   # Using pip
   pip install -r requirements.txt
   
   # Or using uv
   uv pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the streamlit-app directory to configure the connection to the RAG Query API:

```bash
UNBARRED_API="http://your-ec2-ip:8000/query"
UNBARRED_API_KEY=""  # Optional - leave empty if not using authentication
```

**Example for local testing:**
```bash
UNBARRED_API="http://localhost:8000/query"
UNBARRED_API_KEY=""
```

**Example for EC2 deployment:**
```bash
UNBARRED_API="http://3.234.136.27:8000/query"
UNBARRED_API_KEY=""
```

> **Note:** The RAG Query API (see `../rag-query/`) must be running and accessible at the configured URL. The API runs on port 8000 by default.

## Usage

You can run the application using the provided helper script or directly via Streamlit.

### Option 1: Using the runner script
This script automatically loads environment variables from `.env`.

```bash
python run.py
```

### Option 2: Direct Streamlit execution
Ensure your environment variables are set, then run:

```bash
streamlit run app.py
```

 The application will be available at `http://localhost:8501`.

## Project Structure

- `app.py`: Main application logic and UI definition.
- `Procfile`: Configuration for process managers (e.g., for cloud deployment).
- `pyproject.toml` / `requirements.txt`: Python dependency definitions.

## Deployment

The application is deployed to **AWS Elastic Beanstalk** as a single-instance environment.

### Platform Configuration
- **Platform**: Python 3.11 running on 64bit Amazon Linux 2023
- **Environment Type**: Single instance
- **Proxy**: Nginx (default) forwarding to Streamlit on port 8000

### Environment Variables
Configured under **Configuration → Software → Environment properties** in the Elastic Beanstalk console:

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `PYTHONPATH` | `/var/app/venv/staging-LQM1lest/bin` | Path to the virtual environment bin |
| `UNBARRED_API` | `http://3.234.136.27:8000/query` | RAG Query API Endpoint (port 8000) |
| `UNBARRED_API_KEY` | `""` | Optional - leave empty (RAG Query API doesn't require auth) |
| `UNBARRED_PASSCODES`| `demo123` | Passcode for application access (if enabled) |

> **Important:** Ensure your EC2 instance running the RAG Query API has port 8000 open in its security group and is accessible from your Elastic Beanstalk instance.

### Packaging
The deployment artifact relies on `requirements.txt` for dependencies. Create the deployment bundle (`streamlit-app.zip`) by running the following command in the project root:

```bash
zip -r -X streamlit-app.zip . -x ".git" -x "pycache" -x ".pyc" -x ".env" -x "run.py" -x "uv.lock" -x ".python-version" -x ".DS_Store" -x ".venv/" -x ".egg-info/"
```

This excludes local development artifacts (virtualenv, git metadata, local `.env`, etc.) and the `run.py` launcher which is replaced by the `Procfile` in production.

### Deployment Steps
1. **Build**: Run the zip command above to generate `streamlit-app.zip`.
2. **Upload**: Go to the Elastic Beanstalk console for your environment.
3. **Deploy**: Click **"Upload and deploy"**, select the `streamlit-app.zip` file, and confirm.

### Process Definition (`Procfile`)
The application runs via a `Procfile` which instructs Beanstalk to launch Streamlit headless on port 8000:

```text
web: streamlit run app.py --server.address 0.0.0.0 --server.port 8000 --server.headless true --server.enableCORS false --server.enableXsrfProtection false
```

## Troubleshooting

**App Fails to Start on Beanstalk**
- Check **Health** status in the AWS Console.
- Review logs (`/var/log/web.stdout.log` or `/var/log/nginx/error.log`) for Python tracebacks.
- Ensure `PYTHONPATH` is correctly pointing to the virtual environment bin.

**Backend Connection Errors**
- Verify `UNBARRED_API` is reachable from the Elastic Beanstalk instance
- Check that the RAG Query API is running on the target EC2 instance (port 8000)
- Verify EC2 security group allows inbound traffic on port 8000
- Test the API endpoint directly: `curl http://your-ec2-ip:8000/health`

**Related Documentation**
- [RAG Query API Documentation](../rag-query/README.md)
- [EC2 Deployment Guide](../rag-query/Documentation/EC2_SETUP.md)
