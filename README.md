# Fitbyte - Personal Fitbit Data Ingestion for Dashboards

Fitbyte is a Python backend designed to authenticate with the Fitbit API, fetch your daily activity and profile data, and store it in a local SQLite database. This database can then be used as a direct data source for visualization tools like Grafana. It is designed to work with the "Personal" OAuth 2.0 application type, meaning it only accesses your own Fitbit data without needing to handle multiple users or complex authentication flows.

## Prerequisites

- Python 3.8+
- A Fitbit Developer Account

## Setup & Installation

### 1. clone the repository & setup Virtual Environment

```bash
# Navigate to the project directory
cd /path/to/fitbyte

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install the required dependencies
pip install requests python-dotenv
```

### 2. Configure Credentials

1. Go to the [Fitbit Developer Portal](https://dev.fitbit.com/build/reference/web-api/developer-guide/getting-started/) and register a new application with the following values:
   - **Application Name**: `fitbyte`
   - **Description**: `fitbit metrics`
   - **Application Website URL**: `<any valid URL, e.g., http://localhost>`
   - **Organization**: `<your organization or name>`
   - **Organization Website URL**: `<any valid URL, e.g., http://localhost>`
   - **Terms of Service URL**: `<any valid URL, e.g., http://localhost>`
   - **Privacy Policy URL**: `<any valid URL, e.g., http://localhost>`
   - **OAuth 2.0 Application Type**: `Personal` (Since you only need to access your own data)
   - **Redirect URL**: `http://localhost:8080/callback` (The `auth.py` script automatically runs a temporary local server to catch this callback)
   - **Default Access Type**: `Read Only`
   - **Subscriber**: Do not add a subscriber (Webhooks are not needed for this app)
2. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
3. Open the `.env` file and fill in your `FITBIT_CLIENT_ID` and `FITBIT_CLIENT_SECRET`.

### 3. Initial Authentication

You must authenticate the app once to grant it access to your Fitbit data.

```bash
python auth.py
```

This will open a browser window to Fitbit's authorization page. Log in and allow access. Your access and refresh tokens will be saved locally to `token.json`.

### 4. Run Data Ingestion

*(Note: You **do not** need to install a database server like MySQL or PostgreSQL. This project uses **SQLite**, which stores the entire database in a single local file automatically.)*

Run the ingestion script to fetch your data and store it in the database:

```bash
python ingest.py
```

This will:
1. Initialize `fitbit_data.sqlite` if it doesn't exist.
2. Read your tokens (refreshing them if they have expired).
3. Fetch your user profile and today's activity metrics.
4. Save the data to the database.

## Automation (Dockerized Ingestion)

We have provided a completely Dockerized environment that spins up Grafana, a SQLite web interface, and an ingestion service that automatically runs the `ingest.py` script every hour.


## Grafana Integration

We have provided a `docker-compose.yml` file to quickly spin up a Grafana instance with the necessary SQLite plugin pre-installed.

### 1. Build and Start the Stack

**IMPORTANT:** Before running Docker, you must authenticate manually at least once so the container has a valid token to use!

1. From your terminal, run `python auth.py` and log in via your web browser. This generates a `token.json` file on your computer.
2. Run the following command in the project directory. This will build the Python ingestion container and download the Grafana and SQLite-web images:

```bash
docker compose up -d --build
```

You now have three containers running:
1. **fitbyte-grafana** (Port 3001): The visualization dashboard.
2. **fitbyte-sqlite-web** (Port 8081): A web interface to explore your raw database.
3. **fitbyte-ingest** (Background): A cron job that silently mounts your local `token.json` and fetches your latest Fitbit data every hour.

*Troubleshooting*: To view the logs of your automatic background ingestion, run `docker logs -f fitbyte-ingest`.

### 2. Access Grafana

1. Open your browser and go to `http://localhost:3001`.
2. Log in with the default credentials:
   - **Username**: `admin`
   - **Password**: `admin` (You will be prompted to change this upon first login)

### 3. Configure the SQLite Data Source

1. Go to **Connections > Data sources** in the left sidebar.
2. Click **Add data source** and search for **SQLite**.
3. Set the **Path** to: `/var/lib/grafana/fitbit_data.sqlite`
4. Click **Save & test**.

Now you can query the `daily_activity` and `user_profile` tables to build your dashboards!

## Database Client (SQLite Web)

The `docker-compose.yml` also includes a lightweight web-based interface for exploring the SQLite database directly, which can help you write queries for Grafana.

1. Once Docker Compose is running, open your browser and go to `http://localhost:8081`.
2. This is the **SQLite Web** interface.
3. You can browse the tables, view rows, and even run raw SQL queries directly using the **Query** tab. This is perfect for testing out SQL statements before copying them into Grafana!
