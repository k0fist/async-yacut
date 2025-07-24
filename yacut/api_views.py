from http import HTTPStatus

from flask import jsonify, request

from .error_handlers import InvalidAPIUsage
from .models import URLMap
from .settings import app


MSG_MISSING_BODY = 'Отсутствует тело запроса'
MSG_REQUIRED_URL = '"url" является обязательным полем!'


@app.route('/api/id/', methods=['POST'])
def api_create_id():
    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage(MSG_MISSING_BODY)

    original = data.get('url')
    if not original:
        raise InvalidAPIUsage(MSG_REQUIRED_URL)

    short = data.get('custom_id')

    url = URLMap.create(original, short)

    return jsonify(url=original, short_link=url.public_url), HTTPStatus.CREATED


@app.route('/api/id/<string:short>/', methods=['GET'])
def api_get_url(short):
    url = URLMap.get_short(short)

    return jsonify(url=url.original), HTTPStatus.OK
