import json
import string
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import owncloud
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render

from yourls import YOURLSClient
from yourls.exceptions import YOURLSHTTPError


def home_view(request):
    return redirect(list_view)


def list_view(request, path=settings.OC_PATH):
    """
    List files in OwnCloud with YOURLS short URLs.
    Uses threading to fetch shares concurrently and caches per directory for 30s.
    Cache is invalidated when a share is created or deleted within that directory.
    """
    cache_key = _cache_key_for_path(path)
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, "shortener/index.html", cached_context)

    # Connect to OwnCloud
    oc = owncloud.Client(settings.OC_SERVER)
    oc.login(settings.OC_USER, settings.OC_PASSWORD)
    list_of_files = oc.list(path)

    # Connect to YOURLS and preload existing short URLs
    yourls = YOURLSClient(settings.YOURLS_ENDPOINT, signature=settings.YOURLS_SIGNATURE)
    list_of_short = yourls.list()

    def fetch_share(file):
        """Fetch share info + YOURLS mapping for one file."""
        try:
            shares = oc.get_shares(path=file.path)
            if not shares:
                return file
            share_url = shares[0].share_info["url"]
            short_entry = next((x for x in list_of_short if x.url == share_url), None)
            if short_entry:
                file.attributes["short"] = short_entry.shorturl
                file.attributes["keyword"] = short_entry.keyword
        except Exception as e:
            file.attributes["error"] = str(e)
        return file

    # Fetch concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        list_of_files = list(executor.map(fetch_share, list_of_files))

    context = {
        "path": path,
        "prev_path": get_prev_path(path),
        "list_of_files": list_of_files,
    }

    # Cache for 30 seconds
    cache.set(cache_key, context, timeout=60)
    return render(request, "shortener/index.html", context)


def delete_view(request, keyword):
    """
    Delete a YOURLS short URL and invalidate the related directory cache if known.
    """
    yourls = YOURLSClient(settings.YOURLS_ENDPOINT, signature=settings.YOURLS_SIGNATURE)
    yourls.delete(keyword)

    # Optionally invalidate cache (cannot infer path from keyword directly)
    # If you include a 'path' parameter in delete requests, uncomment below:
    path = request.GET.get("path")
    if path:
        _invalidate_cache(path)

    return redirect(list_view)


def shorten_view(request):
    """
    Create a short link for an OwnCloud file.
    Invalidate the cache of the file's parent directory.
    """
    txt = request.POST["txt"].lower() if request.POST["txt"] else get_random_string(5)
    path = request.POST["path"]

    oc = owncloud.Client(settings.OC_SERVER)
    oc.login(settings.OC_USER, settings.OC_PASSWORD)

    share = oc.get_shares(path=path)

    if share:
        link = share[0].share_info["url"]
    else:
        link = oc.share_file_with_link(path).get_link()

    try:
        yourls = YOURLSClient(settings.YOURLS_ENDPOINT, signature=settings.YOURLS_SIGNATURE)
        shorturl = yourls.shorten(link, keyword=txt).shorturl
    except YOURLSHTTPError as exc:
        response = json.loads(exc.response._content.decode())
        shorturl = response.get("shorturl", f"ERROR keyword: {txt} already exists")

    # Invalidate only the parent directory cache
    parent_path = str(Path(path).parent)
    _invalidate_cache(parent_path)

    context = {
        "path": path,
        "prev_path": get_prev_path(path),
        "longurl": link,
        "shorturl": shorturl,
    }
    return render(request, "shortener/short.html", context)


def refresh_view(request, path=settings.OC_PATH):
    _invalidate_cache(path)
    return redirect('list', path=path)

# ---------------------- helpers ---------------------- #


def _cache_key_for_path(path: str) -> str:
    """Generate cache key for a given OwnCloud path."""
    return f"owncloud_list::{path.rstrip('/')}"


def _invalidate_cache(path: str):
    """Invalidate cache for the given directory path only."""
    cache_key = _cache_key_for_path(path)
    cache.delete(cache_key)


def get_prev_path(path):
    if len(Path(path).parents) > 1:
        return str(Path(path).parents[0])
    else:
        return str(settings.OC_PATH)


def get_random_string(length):
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))
