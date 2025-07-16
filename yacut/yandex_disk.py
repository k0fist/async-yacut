import urllib.parse
import aiohttp

from .models import get_unique_short_id, URLMap

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


async def upload_file_to_yadisk(uploaded, token):
    """
    Загружает один файл на Яндекс.Диск и возвращает готовый объект URLMap,
    готовый к сохранению в БД.
    """
    filename = uploaded.filename
    headers = {'Authorization': f'OAuth {token}'}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            UPLOAD_ENDPOINT,
            headers=headers,
            params={'path': f'app:/{filename}', 'overwrite': 'True'}
        ) as r1:
            r1.raise_for_status()
            upload_url = (await r1.json())['href']

        data = uploaded.read()
        async with session.put(upload_url, data=data) as r2:
            r2.raise_for_status()
            location = urllib.parse.unquote(r2.headers['Location'])
            disk_path = location.replace('/disk', '', 1)

        async with session.get(
            DOWNLOAD_ENDPOINT,
            headers=headers,
            params={'path': disk_path}
        ) as r3:
            r3.raise_for_status()
            download_href = (await r3.json())['href']

    short_id = get_unique_short_id()
    link = URLMap(
        filename=filename,
        download_url=download_href,
        short=short_id
    )
    return link
