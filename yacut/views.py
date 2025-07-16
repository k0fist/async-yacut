import asyncio
import re

from .models import URLMap
from yacut.settings import app, db
from .forms import LinksForm, FilesForm
from .yandex_disk import upload_file_to_yadisk
from flask import (
    abort, render_template, flash, redirect,
    url_for, current_app, session, jsonify, request
)
from sqlalchemy.exc import IntegrityError
from .error_handlers import InvalidAPIUsage


API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
UPLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_ENDPOINT = f'{API_HOST}{API_VERSION}/disk/resources/download'


@app.route('/', methods=['GET', 'POST'])
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

        db.session.add(url)
        db.session.commit()
    return render_template('links.html', form=form, url=url)


@app.route('/files', methods=['GET', 'POST'])
async def files_view():
    form = FilesForm()

    if form.validate_on_submit():
        token = current_app.config['DISK_TOKEN']
        tasks = [
            upload_file_to_yadisk(uploaded, token)
            for uploaded in form.files.data
        ]
        links = await asyncio.gather(*tasks, return_exceptions=True)

        created = []
        for res in links:
            if isinstance(res, Exception):
                flash(f'Ошибка загрузки: {res}', 'error')
            else:
                db.session.add(res)
                created.append(res.short)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('Ошибка при сохранении в БД.', 'error')

        session['uploaded_slugs'] = created
        files = []
        if created:
            files = URLMap.query \
                .filter(URLMap.short.in_(created)) \
                .order_by(URLMap.timestamp.desc()) \
                .all()
        return render_template('files.html', form=form, files=files), 200

    slugs = session.pop('uploaded_slugs', [])
    files = []
    if slugs:
        files = URLMap.query \
            .filter(URLMap.short.in_(slugs)) \
            .order_by(URLMap.timestamp.desc()) \
            .all()
    return render_template('files.html', form=form, files=files), 200


@app.route('/<string:slug>')
def url_view(slug):
    link = URLMap.query.filter_by(short=slug).first_or_404()
    if link.is_web():
        return redirect(link.original)
    if link.is_file():
        return redirect(link.download_url)
    abort(404)


@app.route('/api/id/', methods=['POST'])
def api_create_id():
    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage('Отсутствует тело запроса')
    original = data.get('url')
    custom = data.get('custom_id')

    if not original:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    if custom:
        if not re.fullmatch(r'[A-Za-z0-9]+', custom):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if len(custom) > 16:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        if URLMap.query.filter_by(short=custom).first():
            raise InvalidAPIUsage(
                'Предложенный вариант короткой ссылки уже существует.'
            )
        link = URLMap(original=original, short=custom)
    else:
        link = URLMap(original=original)

    db.session.add(link)
    db.session.commit()

    short_url = url_for('url_view', slug=link.short, _external=True)
    return jsonify(url=original, short_link=short_url), 201


@app.route('/api/id/<string:short_id>/', methods=['GET'])
def api_get_url(short_id):
    link = URLMap.query.filter_by(short=short_id).first()
    if not link or not link.is_web():
        raise InvalidAPIUsage('Указанный id не найден', 404)

    return jsonify(url=link.original), 200
