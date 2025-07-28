import asyncio
import aiohttp
from http import HTTPStatus

from .models import URLMap, ValidationError
from .settings import app
from .forms import LinksForm, FilesForm
from flask import (
    render_template, redirect, current_app, flash
)
from .yandex_disk import upload_file_to_yadisk


API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


@app.route('/', methods=('GET', 'POST'))
def index_view():
    form = LinksForm()
    short_url = None

    if not form.validate_on_submit():
        return render_template(
            'index.html',
            form=form
        )

    original = form.original_link.data.strip()
    short = (form.custom_id.data)

    try:
        link = URLMap.save(original, short)
    except ValidationError as e:
        flash(str(e), 'error')

    short_url = link.public_url

    return render_template(
        'index.html',
        form=form,
        short_url=short_url
    )


@app.route('/files', methods=['GET', 'POST'])
async def files_view():
    form = FilesForm()

    if not form.validate_on_submit():
        return render_template(
            'files.html', form=form
        ), HTTPStatus.OK

    async with aiohttp.ClientSession() as sess:
        tasks = [
            upload_file_to_yadisk(
                sess, uploaded, current_app.config['DISK_TOKEN']
            )
            for uploaded in form.files.data
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    hrefs = []
    filenames = []
    for uploaded, res in zip(form.files.data, results):
        if isinstance(res, Exception):
            flash(f'Ошибка загрузки “{uploaded.filename}”: {res}', 'error')
            continue
        hrefs.append(res)
        filenames.append(uploaded.filename)

    urlmaps = URLMap.bulk_create(hrefs)

    paired = [
        {'filename': fn, 'public_url': um.public_url}
        for fn, um in zip(filenames, urlmaps)
    ]

    return render_template(
        'files.html', form=form, files=paired
    ), HTTPStatus.OK


@app.route('/<string:slug>')
def url_view(slug):
    link = URLMap.get_short(slug)
    return redirect(link.original)
