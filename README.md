# TvShowFetcher

Django project with two apps: **backoffice** syncs TV shows and episodes from a Tv Show Time–style API, tracks watched/downloaded state, triggers torrent lookups (e.g. YGG) and download orchestration, sends Mailjet notifications, and provides a custom admin; **shortener** lets you browse OwnCloud and manage YOURLS short links for shared files.

## Features

- Show and episode sync from external API (Tv Show Time / Tozelabs)
- Management commands: `get_shows`, `fetch_show`, `download_episode`
- Torrent lookup and download flow (YGG-style), with Mailjet email summaries
- Custom Django admin (AdminPlus) with actions: enable/disable shows, fetch shows, download episodes, download by URL
- OwnCloud file listing with YOURLS short URLs: list, shorten, delete, refresh (cached)

## Requirements

- Python 3.10+
- Django 5.2
- MySQL (production) or SQLite (dev/tests)
- System: `libmysqlclient-dev` and `pkg-config` for the mysqlclient Python package

Optional external services: Tv Show Time API, YGG (or similar torrent API), Mailjet, OwnCloud, YOURLS.

## Installation

1. Clone the repo and create a virtualenv.
2. Install system dependencies (Debian/Ubuntu):

   ```bash
   sudo apt-get update
   sudo apt-get install -y libmysqlclient-dev pkg-config
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example settings and configure:

   ```bash
   cp tv_show_fetcher/settings.py.example tv_show_fetcher/settings.py
   ```

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

## Configuration

Edit `tv_show_fetcher/settings.py` (see `tv_show_fetcher/settings.py.example`). Main groups:

- **Database**: `DATABASES` (MySQL or SQLite)
- **Tv Show Time API**: `USER_ID`, `USER_URL`, `SHOW_URL`, `USER_PARAMS`, `SHOW_PARAMS`, `REQUESTS_HEADERS`
- **Mailjet**: `MAILJET_API_KEY`, `MAILJET_API_SECRET`, `FROM_EMAIL`, `TO_EMAIL`
- **YGG / torrent**: `YGG_PATH`, `YGG_PASSKEY`, `TEMP_DIR`, `TO_ADD`, `PREFERD_RES`, `PREFERD_LANG`
- **OwnCloud**: `OC_SERVER`, `OC_USER`, `OC_PASSWORD`, `OC_PATH`
- **YOURLS**: `YOURLS_ENDPOINT`, `YOURLS_SIGNATURE`

## Usage

- **Admin**: Open `/admin/` for shows and episodes. Use custom actions to fetch shows, download episodes, enable/disable shows, or download by URL.
- **Management commands**:
  - `python manage.py get_shows` — sync shows from the API
  - `python manage.py fetch_show <show_id>` — fetch episodes for a show (or `--all` / `--enabled`)
  - `python manage.py download_episode <episode_id> ...` — download episodes (or `--to-watch` for all to-download, aired, enabled shows)
- **Shortener**: Open `/short/` to list OwnCloud files, create short links, delete short links, and refresh cache.

## Testing

Tests use SQLite in-memory and dummy API settings so no real services are called. CI runs these tests (see `.github/workflows/ci.yml`).

Run all tests with Django's test runner:

```bash
python manage.py test --settings=tv_show_fetcher.settings_test
```

Run a single app's tests:

```bash
python manage.py test backoffice --settings=tv_show_fetcher.settings_test
python manage.py test shortener --settings=tv_show_fetcher.settings_test
```

Optional: with [pytest-django](https://pytest-django.readthedocs.io/) installed you can run:

```bash
pytest --ds=tv_show_fetcher.settings_test
```

## CI

The repo includes a GitHub Actions workflow (`.github/workflows/ci.yml`) for running tests and CodeQL analysis on push and pull requests.
