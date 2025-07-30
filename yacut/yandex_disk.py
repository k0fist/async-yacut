import urllib.parse
import asyncio
import aiohttp
from flask import flash, current_app

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'
ERROR_DOWNLOAD = 'Ошибка загрузки “{filename}”: {href}'


async def _upload_one(sess: aiohttp.ClientSession, file) -> str:
    token = current_app.config['DISK_TOKEN']
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


async def bulk_upload(files):
    async with aiohttp.ClientSession() as sess:
        tasks = [_upload_one(sess, f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    urls = []
    for f, res in zip(files, results):
        if isinstance(res, Exception):
            flash(ERROR_DOWNLOAD.format(
                filename=f.filename, error=res
            ), 'error')
        else:
            urls.append(res)

    return urls
