from http import HTTPStatus

from .models import URLMap
from .settings import app
from .forms import LinksForm, FilesForm
from flask import (
    render_template, redirect, current_app, session
)
from .error_handlers import InvalidAPIUsage


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
            form=form,
            short_url=short_url
        )

    original = form.original_link.data.strip()
    short = (form.custom_id.data or '').strip()

    try:
        url = URLMap.create(original, short or None)
    except InvalidAPIUsage as e:
        form.custom_id.errors.append(e.message)
    else:
        short_url = url.public_url

    return render_template(
        'index.html',
        form=form,
        short_url=short_url
    )


@app.route('/files', methods=['GET', 'POST'])
async def files_view():
    form = FilesForm()

    if not form.validate_on_submit():
        paired = session.pop('uploaded_files', [])
        return render_template(
            'files.html',
            form=form,
            files=paired
        ), HTTPStatus.OK

    token = current_app.config['DISK_TOKEN']
    paired = await URLMap.bulk_create_from_uploads(form.files.data, token)

    # сохраняем для GET в сессии
    session['uploaded_files'] = paired

    return render_template(
        'files.html',
        form=form,
        files=paired
    ), HTTPStatus.OK


@app.route('/<string:slug>')
def url_view(slug):
    link = URLMap.query.filter_by(short=slug).first_or_404()
    return redirect(link.original)
