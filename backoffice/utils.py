import datetime
import logging
import os
import re
import secrets
import string
import unicodedata
import requests
import torrent_parser

from backoffice.models import Show, Episode
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str
from mailjet_rest import Client
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_shows():
    """
    Fetch the API to get the Show.
    Add or update them if already exists.
    """
    final_url = f"{settings.USER_URL}/{settings.USER_ID}/profile"
    resp = requests.get(final_url, params=settings.USER_PARAMS, headers=settings.REQUESTS_HEADERS).json()
    pattern = re.compile(r"\(\d{4}\)")
    for show in resp["shows"]:
        show_id = show['id']
        name = re.sub(pattern, "", show['name'].replace("&", "and")).strip()
        create_or_update_with_log(
            Show,
            tst_id=show_id,
            defaults={
                "name": name
            }
        )


def fetch_show(show):
    final_url = f"{settings.SHOW_URL}/{show.tst_id}/data/en"
    resp = requests.get(final_url, params=settings.SHOW_PARAMS, headers=settings.REQUESTS_HEADERS).json()
    if "episodes" in resp:
        for episode in resp.get("episodes", []):
            episode_id = episode.get("id")
            air_date_str = episode.get("air_date")
            aired = False
            air_date = None
            if air_date_str:
                try:
                    air_date = datetime.datetime.strptime(air_date_str, '%Y-%m-%d').date()
                    aired = air_date <= datetime.date.today()
                except (ValueError, TypeError):
                    # Invalid or malformed date string — leave aired as False
                    pass

            create_or_update_with_log(
                Episode,
                tst_id=episode_id,
                defaults={
                    "show": show,
                    "name": episode['name'],
                    "season": episode['season_number'],
                    "number": episode['number'],
                    "watched": episode['seen'],
                    "date": air_date,
                    "aired": aired
                }
            )


def download_episode(episode_list):
    resp = {}
    if not episode_list:
        return resp
    ct = ContentType.objects.get_for_model(episode_list.model)
    text = "Hello,\nI proudly download:\n"
    for episode in episode_list:
        res = lookup(
            settings.YGG_PATH,
            str(episode),
            settings.YGG_PASSKEY,
            settings.TO_ADD,
            settings.PREFERD_LANG,
            settings.PREFERD_RES)
        text += f" * {episode}: {bool(res)}\r\n"
        logger.info(f"Downloaded {episode}: {bool(res)}")
        if res:
            episode.downloaded = True
            episode.save()
            LogEntry.objects.log_action(
                user_id=1,
                content_type_id=ct.pk,
                object_id=episode.pk,
                object_repr=str(episode),
                action_flag=CHANGE,
                change_message="The episode has been download")
        resp[episode] = bool(res)
    send_mail(
        'Download resum',
        text,
        settings.FROM_EMAIL,
        settings.TO_EMAIL
    )
    return resp


def download_by_urls(urls):
    resp = {}
    for url in urls:
        last_part = urlparse(url).path.split('/')[-1]
        match = re.search(r'\d+', last_part)
        if not match:
            return resp

        text = "Hello,\nI proudly download:\n"
        torrent_id = match.group()
        res = lookup(
            settings.YGG_PATH,
            "blop",
            settings.YGG_PASSKEY,
            settings.TO_ADD,
            settings.PREFERD_LANG,
            settings.PREFERD_RES,
            torrent_id)
        text += ' * ' + str(res) + ": " + str(bool(res)) + "\r\n"
        resp[str(res)] = bool(res)
        send_mail(
            'Download resum',
            text,
            settings.FROM_EMAIL,
            settings.TO_EMAIL
        )
    return resp


def lookup(path, name, passkey, toAdd, language, resolution, torrent_id=None):
    if torrent_id:
        torrent = requests.get(f'{path}/torrent/{torrent_id}').json()
    else:
        # Search Torrent
        params = {
            'q': f'{name} {language} {resolution}',
            'order_by': 'downloads'
        }

        torrents = requests.get(f'{path}/torrents', params=params).json()

        if not torrents:
            params = {
                'q': f'{name} {language}',
                'order_by': 'downloads'
            }

            torrents = requests.get(f'{path}/torrents', params=params).json()

        if not torrents:
            params = {
                'q': f'{name}',
                'order_by': 'downloads'
            }

            torrents = requests.get(f'{path}/torrents', params=params).json()

        # Get the ID
        torrent_id = None
        for torrent in torrents:
            if torrent['seeders'] > 0:
                torrent_id = torrent['id']
                break

    if torrent_id and torrent:
        title = safe_filename(torrent['title'])
        # Download and save fake torrent file
        fake_pass = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        params = {'passkey': fake_pass}
        response = requests.get(f'{path}/torrent/{torrent_id}/download', params=params, stream=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        with open(f"{settings.TEMP_DIR}/{title}.torrent", 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        # Open and edit with right passkey
        data = torrent_parser.parse_torrent_file(f"{settings.TEMP_DIR}/{title}.torrent")
        data['announce'] = data['announce'].replace(fake_pass, passkey)
        torrent_parser.create_torrent_file(f"{toAdd}/{title}.torrent", data)
        return title
    return False


def create_or_update_with_log(model, defaults=None, **lookup):
    """
    Create if not exists, or update if changed.
    Logs both to standard logger and Django admin LogEntry.
    """
    defaults = defaults or {}

    obj, created = model.objects.get_or_create(defaults=defaults, **lookup)
    model_name = model.__name__
    obj_str = force_str(obj)

    if created:
        # Python logger
        logger.info(f"Created new {model_name}: {obj_str}")

        # Django admin log
        LogEntry.objects.log_action(
            user_id=1,
            content_type_id=ContentType.objects.get_for_model(model).pk,
            object_id=obj.pk,
            object_repr=obj_str,
            action_flag=ADDITION,
            change_message=f"Created new {model_name}"
        )

        return obj, True

    # --- Handle updates only if something changed ---
    has_changes = False
    changes = {}

    for field, new_value in defaults.items():
        old_value = getattr(obj, field)
        if old_value != new_value:
            setattr(obj, field, new_value)
            changes[field] = {'old': old_value, 'new': new_value}
            has_changes = True

    if has_changes:
        obj.save(update_fields=list(defaults.keys()))

        # Python logger
        logger.info(f"Updated {model_name} '{obj_str}' changes: {changes}")

        # Django admin log
        LogEntry.objects.log_action(
            user_id=1,
            content_type_id=ContentType.objects.get_for_model(model).pk,
            object_id=obj.pk,
            object_repr=obj_str,
            action_flag=CHANGE,
            change_message=f"Updated fields: {changes}"
        )
    else:
        logger.debug(f"No changes detected for {model_name} '{obj_str}'")

    return obj, created


def send_mail(subject, body, from_email, to_email):
    mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')
    to = []
    for mail in to_email:
        to.append({"Email": mail})

    data = {
        'Messages': [
            {
                "From": {
                    "Email": from_email,
                },
                "To": to,
                "Subject": subject,
                "TextPart": body,
                "CustomID": "FetcherNotification"
            }
        ]
    }
    return mailjet.send.create(data=data)


def safe_filename(name):
    # Normalize and remove accents
    nfkd = unicodedata.normalize("NFKD", name)
    name = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Remove unsafe characters
    name = re.sub(r'[^a-zA-Z0-9._\-]', '_', name)
    return name


def print_messages(request, resp):
    for name, result in resp.items():
        if result:
            messages.info(request, f"{name}: {result}")
        else:
            messages.error(request, f"{name}: {result}")
