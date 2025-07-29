import urllib.parse
import asyncio
import aiohttp
from flask import flash
from typing import List, Dict

from .models import URLMap

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


async def _upload_one(sess: aiohttp.ClientSession, file, token: str) -> str:

    headers = {'Authorization': f'OAuth {token}'}

    async with sess.get(
        UPLOAD_ENDPOINT,
        headers=headers,
        params={'path': f'app:/{file.filename}', 'overwrite': 'True'}
    ) as r1:
        r1.raise_for_status()
        upload_url = (await r1.json())['href']

    data = file.read()
    async with sess.put(upload_url, data=data) as r2:
        r2.raise_for_status()

        loc = urllib.parse.unquote(r2.headers['Location'])
        disk_path = loc.replace('/disk', '', 1)

    async with sess.get(
        DOWNLOAD_ENDPOINT,
        headers=headers,
        params={'path': disk_path}
    ) as r3:
        r3.raise_for_status()
        return (await r3.json())['href']


async def upload_and_shorten(
    files: List,
    token: str
) -> List[Dict[str, str]]:

    results = []
    async with aiohttp.ClientSession() as sess:
        tasks = [_upload_one(sess, f, token) for f in files]
        hrefs = await asyncio.gather(*tasks, return_exceptions=True)

    for f, href in zip(files, hrefs):
        if isinstance(href, Exception):
            flash(f'Ошибка загрузки “{f.filename}”: {href}', 'error')
            continue

        obj = URLMap.create(href, None)
        results.append({
            'filename': f.filename,
            'public_url': obj.public_url
        })

    return results
