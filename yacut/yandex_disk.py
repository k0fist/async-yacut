
import urllib.parse

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


async def upload_file_to_yadisk(aio_sess, uploaded, token):
    """
    Загрузка в Яндекс диск.

    Загружает один файл на Яндекс.Диск через aio_sess и
    возвращает href для скачивания.
    """
    filename = uploaded.filename
    headers = {'Authorization': f'OAuth {token}'}

    async with aio_sess.get(
        UPLOAD_ENDPOINT,
        headers=headers,
        params={'path': f'app:/{filename}', 'overwrite': 'True'}
    ) as r1:
        r1.raise_for_status()
        upload_url = (await r1.json())['href']

    data = uploaded.read()
    async with aio_sess.put(upload_url, data=data) as r2:
        r2.raise_for_status()
        loc = urllib.parse.unquote(r2.headers['Location'])
        disk_path = loc.replace('/disk', '', 1)

    async with aio_sess.get(
        DOWNLOAD_ENDPOINT,
        headers=headers,
        params={'path': disk_path}
    ) as r3:
        r3.raise_for_status()
        download_href = (await r3.json())['href']

    return download_href
