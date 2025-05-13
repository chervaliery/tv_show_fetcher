from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render

from pathlib import Path
from slugify import slugify

from yourls import YOURLSClient
from yourls.exceptions import YOURLSURLExistsError, YOURLSKeywordExistsError, YOURLSHTTPError

import logging
import json
import os
import owncloud
import random
import requests
import string

logger = logging.getLogger(__name__)


def get_prev_path(path):
    if len(Path(path).parents) > 1:
        return str(Path(path).parents[0])
    else:
        return str(settings.OC_PATH)


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase + string.digits
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def home_view(request):
    return redirect(list_view)


def refresh_oc_cache(path=settings.OC_PATH):
    oc = owncloud.Client(settings.OC_SERVER)
    oc.login(settings.OC_USER, settings.OC_PASSWORD)
    list_of_files = oc.list(path)
    cache.set(f"list_of_files-{slugify(path)}", list_of_files)
    return list_of_files


def refresh_share_cache(file):
    oc = owncloud.Client(settings.OC_SERVER)
    oc.login(settings.OC_USER, settings.OC_PASSWORD)
    share = oc.get_shares(path=file.path)

    cache.set(f"share-{slugify(file.path)}", share, timeout=None)
    return share


def refresh_yourls_cache():
    yourls = YOURLSClient(settings.YOURLS_ENDPOINT,signature=settings.YOURLS_SIGNATURE)
    list_of_short = yourls.list()
    cache.set("list_of_short", list_of_short)
    return list_of_short


def list_view(request, path=settings.OC_PATH):
    if (list_of_files :=cache.get(f"list_of_files-{slugify(path)}")) is None:
        list_of_files = refresh_oc_cache(path)

    if (list_of_short := cache.get("list_of_short")) is None:
        list_of_short = refresh_yourls_cache()

    for file in list_of_files:
        if (share :=cache.get(f"share-{slugify(file.path)}")) is None:
            share = refresh_share_cache(file)
        if share:
            if shorturl := _[0] if (_:=[x for x in list_of_short if x.url==share[0].share_info['url']]) else None:
                file.attributes['short'] = shorturl.shorturl
                file.attributes['keyword'] = shorturl.keyword

    context = {
        "prev_path": get_prev_path(path),
        "list_of_files": list_of_files,
    }

    return render(request, "shortener/index.html", context)


def delete_view(request, keyword):
    yourls = YOURLSClient(settings.YOURLS_ENDPOINT,signature=settings.YOURLS_SIGNATURE)
    yourls.delete(keyword)
    refresh_yourls_cache()
    return redirect(list_view)


def shorten_view(request):
    txt = request.POST["txt"].lower() if request.POST["txt"] else get_random_string(5)
    path = request.POST["path"]

    oc = owncloud.Client(settings.OC_SERVER)
    oc.login(settings.OC_USER, settings.OC_PASSWORD)

    if (share :=cache.get(f"share-{slugify(path)}")) is None:
        share = refresh_share_cache(file)

    if share:
        link = share[0].share_info['url']
    else:
        link = oc.share_file_with_link(path).get_link()
        cache.set(f"share-{slugify(path)}", link)

    try:
        yourls = YOURLSClient(settings.YOURLS_ENDPOINT,signature=settings.YOURLS_SIGNATURE)
        shorturl = yourls.shorten(link, keyword=txt).shorturl
    except YOURLSHTTPError as exc:
        response = json.loads(exc.response._content.decode())
        if 'shorturl' in response:
            shorturl = json.loads(exc.response._content.decode())['shorturl']
        else:
            shorturl = "ERROR keyword: {} already exists".format(txt)
    context = {
        "prev_path": get_prev_path(path),
        "longurl": link,
        "shorturl": shorturl,
    }
    refresh_yourls_cache()
    return render(request, "shortener/short.html", context)
