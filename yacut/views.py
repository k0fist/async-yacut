from http import HTTPStatus

from flask import abort, flash, redirect, render_template, session

from .forms import FilesForm, LinksForm
from .models import URLMap, ValidationError
from .settings import app
from .yandex_disk import bulk_upload


@app.route('/', methods=('GET', 'POST'))
def index_view():
    form = LinksForm()

    if not form.validate_on_submit():
        return render_template(
            'index.html',
            form=form
        )

    original = form.original_link.data.strip()
    short = form.custom_id.data

    try:
        mapping = URLMap.create(original=original, short=short)
    except (ValidationError, RuntimeError) as e:
        flash(str(e))
        return render_template('index.html', form=form)

    short_url = mapping.public_url

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
            'files.html', form=form, files=paired
        ), HTTPStatus.OK

    hrefs = await bulk_upload(form.files.data)
    mappings = URLMap.bulk_create(hrefs)

    paired = [
        {'filename': f.filename, 'public_url': m.public_url}
        for f, m in zip(form.files.data, mappings)
    ]

    return render_template(
        'files.html', form=form, files=paired
    ), HTTPStatus.OK


@app.route('/<string:slug>')
def url_view(slug):
    mapping = URLMap.get(slug)
    if mapping is None:
        abort(HTTPStatus.NOT_FOUND)
    return redirect(mapping.original)
