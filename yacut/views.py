import asyncio
import aiohttp
from http import HTTPStatus

from .models import URLMap
from .settings import app
from .forms import LinksForm, FilesForm
from .yandex_disk import upload_file_to_yadisk
from flask import (
    render_template, flash, redirect, current_app, session
)
from .sequence_generator import get_unique_short_id
from .db_helpers import save_and_commit


API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


@app.route('/', methods=('GET', 'POST'))
def index_view():
    form = LinksForm()
    url = None
    if form.validate_on_submit():
        original = form.original_link.data.strip()
        custom = (form.custom_id.data or '').strip()
        if custom:
            if custom.lower() == 'files':
                form.custom_id.errors.append(
                    'Предложенный вариант короткой ссылки уже существует.'
                )
                return render_template('links.html', form=form)

            if URLMap.query.filter_by(short=custom).first():
                form.custom_id.errors.append(
                    'Предложенный вариант короткой ссылки уже существует.'
                )
                return render_template('links.html', form=form)
            url = URLMap(original=original, short=custom)
        else:
            url = URLMap(original=original)

        if not save_and_commit(url):
            flash('Не удалось сохранить ссылку, попробуйте ещё раз.', 'error')
            url = None

    return render_template('links.html', form=form, url=url)


@app.route('/files', methods=['GET', 'POST'])
async def files_view():
    form = FilesForm()

    if form.validate_on_submit():
        token = current_app.config['DISK_TOKEN']
        paired = []

        async with aiohttp.ClientSession() as aio_sess:
            tasks = [
                upload_file_to_yadisk(aio_sess, uploaded, token)
                for uploaded in form.files.data
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        for uploaded, res in zip(form.files.data, results):
            if isinstance(res, Exception):
                flash(f'Ошибка загрузки: {res}', 'error')
            else:
                href = res
                short_id = get_unique_short_id()
                link = URLMap(original=href, short=short_id)
                if save_and_commit(link):
                    paired.append((uploaded.filename, link.short))
                else:
                    flash(
                        f'Код {short_id} уже занят, '
                        f'файл "{uploaded.filename}" не сохранён.',
                        'error'
                    )

        session['uploaded_files'] = paired
        return render_template(
            'files.html', form=form, files=paired
        ), HTTPStatus.OK

    paired = session.pop('uploaded_files', [])
    return render_template(
        'files.html', form=form, files=paired
    ), HTTPStatus.OK

@app.route('/<string:slug>')
def url_view(slug):
    link = URLMap.query.filter_by(short=slug).first_or_404()
    return redirect(link.original)
