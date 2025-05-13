# coding: utf-8
import datetime
import requests
import torrent_parser as tp
import time
import re
import secrets
import string

from mailjet_rest import Client

from backoffice.models import *
from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE, ADDITION
from django.contrib.contenttypes.models import ContentType

def get_show():
    final_url = "{0}/{1}/profile".format(settings.USER_URL, settings.USER_ID)
    resp = requests.get(final_url, params=settings.USER_PARAMS, headers=settings.REQUESTS_HEADERS).json()
    result = {}
    pattern = re.compile(r"\(\d{4}\)")
    ct = ContentType.objects.get_for_model(Show.objects.model)
    for show in resp["shows"]:
        id = show['id']
        name = re.sub(pattern, "", show['name'].replace("&", "and")).strip()
        try:
            s = Show.objects.get(tst_id=id)
            s.name = name
        except Show.DoesNotExist:
            s = Show()
            s.tst_id = show['id']
            s.enabled = False
            s.name = name
            LogEntry.objects.log_action(
                    user_id=1,
                    content_type_id=ct.pk,
                    object_id=s.pk,
                    object_repr=str(s),
                    action_flag=ADDITION,
                    change_message="The Show has been add")
        s.save()


def fetch_show(show):
    final_url = "{0}/{1}/data/en".format(settings.SHOW_URL, show.tst_id)
    resp = requests.get(final_url, params=settings.SHOW_PARAMS, headers=settings.REQUESTS_HEADERS).json()
    ct = ContentType.objects.get_for_model(Episode.objects.model)
    if "episodes" in resp:
        for episode in resp["episodes"]:
            id = episode['id']
            try:
                ep = Episode.objects.get(tst_id=id)
            except Episode.DoesNotExist:
                ep = Episode()
                ep.show = show
                ep.season = episode['season_number']
                ep.number = episode['number']
                ep.tst_id = episode['id']
                ep.downloaded = False
                ep.path = '/'
                LogEntry.objects.log_action(
                    user_id=1,
                    content_type_id=ct.pk,
                    object_id=ep.pk,
                    object_repr=str(ep),
                    action_flag=ADDITION,
                    change_message="The episode has been add")

            ep.season = episode['season_number']
            ep.number = episode['number']
            ep.watched = episode['seen']
            try:
                datetime.datetime.strptime(episode['air_date'], '%Y-%m-%d')
                ep.date = episode['air_date']
            except (ValueError, TypeError):
                ep.date = None
            ep.name = episode['name']
            if not ep.date:
                ep.aired = False
            else:
                ep.aired = episode['aired']
            ep.save()

def download_episode(episode_list):
    resp = {}
    if not episode_list:
        return resp
    ct = ContentType.objects.get_for_model(episode_list.model)
    text = "Hello,\nI proudly download:\n"
    for episode in episode_list:
        res = lookup(settings.YGG_PATH, str(episode), settings.YGG_PASSKEY, settings.TO_ADD, settings.PREFERD_LANG, settings.PREFERD_RES)
        time.sleep(1)
        text += ' * ' + str(episode) + ": " + str(res) + "\r\n"
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
        resp[episode] = res
    send_mail(
        'Download resum',
        text,
        settings.FROM_EMAIL,
        settings.TO_EMAIL
    )
    return resp

def lookup(path, name, passkey, toAdd, language, resolution):
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
    print(torrents)
    # Get the ID 
    torrent_id = None
    for torrent in torrents:
        if torrent['seeders'] > 0:
            torrent_id = torrent['id']
            break

    if torrent_id:
        # Download and save fake torrent file
        fake_pass = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

        params = {'passkey': fake_pass}
        response = requests.get(f'{path}/torrent/{torrent_id}/download', params=params, stream=True)
        with open(f"{settings.TEMP_DIR}/{torrent['title']}.torrent", 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        # Open and edit with right passkey
        data = tp.parse_torrent_file(f"{settings.TEMP_DIR}/{torrent['title']}.torrent")
        data['announce'] = data['announce'].replace(fake_pass, passkey)
        tp.create_torrent_file(f"{toAdd}/{torrent['title']}.torrent", data)
        return True
    return False

def send_mail(subject, body, from_email, to_email):
    print(body)
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


def clean_name(string):
    return re.sub(r'\W+', '', string.lower())

