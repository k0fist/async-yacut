from http import HTTPStatus
from flask import (
    render_template, redirect, current_app, flash, abort, session
)

from .models import URLMap, ValidationError
from .forms import LinksForm, FilesForm
from .settings import db, app
from .yandex_disk import upload_and_shorten


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
        mapping = URLMap(original=original, short=short)
        db.session.add(mapping)
        db.session.commit()
    except ValidationError as e:
        flash(str(e))

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

    paired = await upload_and_shorten(
        form.files.data,
        current_app.config['DISK_TOKEN']
    )
    session['uploaded_files'] = paired
    return render_template(
        'files.html', form=form, files=paired
    ), HTTPStatus.OK


@app.route('/<string:slug>')
def url_view(slug):
    mapping = URLMap.get_link(slug)
    if mapping is None:
        abort(404)
    return redirect(mapping.original)
