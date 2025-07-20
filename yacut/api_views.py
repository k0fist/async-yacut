from .error_handlers import InvalidAPIUsage
from flask import (
    url_for, jsonify, request
)
import re
from http import HTTPStatus
from urllib.parse import urlparse
from .models import URLMap
from .db_helpers import save_and_commit
from .settings import app, MAX_LENGTH_CUSTOM_URL


@app.route('/api/id/', methods=['POST'])
def api_create_id():
    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage('Отсутствует тело запроса')

    original = data.get('url')
    custom = data.get('custom_id')

    if not original:
        raise InvalidAPIUsage('"url" является обязательным полем!')

    parsed = urlparse(original)
    if not (parsed.scheme and parsed.netloc):
        raise InvalidAPIUsage(
            'Указан некорректный URL',
            HTTPStatus.BAD_REQUEST
        )
    if custom:
        if not re.fullmatch(r'[A-Za-z0-9]+', custom):
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки',
                HTTPStatus.BAD_REQUEST
            )
        if len(custom) > MAX_LENGTH_CUSTOM_URL:
            raise InvalidAPIUsage(
                'Указано недопустимое имя для короткой ссылки'
            )
        link = URLMap(original=original, short=custom)
    else:
        link = URLMap(original=original)

    if not save_and_commit(link):
        raise InvalidAPIUsage(
            'Предложенный вариант короткой ссылки уже существует.',
            HTTPStatus.BAD_REQUEST
        )

    short_url = url_for('url_view', slug=link.short, _external=True)
    return jsonify(url=original, short_link=short_url), HTTPStatus.CREATED


@app.route('/api/id/<string:short_id>/', methods=['GET'])
def api_get_url(short_id):
    link = URLMap.query.filter_by(short=short_id).first()
    if not link:
        raise InvalidAPIUsage('Указанный id не найден', HTTPStatus.NOT_FOUND)

    return jsonify(url=link.original), 200