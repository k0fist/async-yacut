from flask import request, jsonify
from http import HTTPStatus

from .error_handlers import InvalidAPIUsage
from .models import URLMap, NOT_FOUND_SHORT_ID, ValidationError
from .settings import app


MISSING_BODY = 'Отсутствует тело запроса'
REQUIRED_URL = '"url" является обязательным полем!'


@app.route('/api/id/', methods=['POST'])
def api_create_id():
    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage(MISSING_BODY)

    if 'url' not in data:
        raise InvalidAPIUsage(REQUIRED_URL)

    original = data['url']
    short = data.get('custom_id')
    if short:
        try:
            URLMap.validate_short_code(short)
        except ValidationError as e:
            raise InvalidAPIUsage(str(e), HTTPStatus.BAD_REQUEST)

    link = URLMap.create(original, short)

    return jsonify(
        url=original,
        short_link=link.public_url
    ), HTTPStatus.CREATED


@app.route('/api/id/<string:short>/', methods=['GET'])
def api_get_url(short):
    link = URLMap.get_link(short)
    if link is None:
        raise InvalidAPIUsage(NOT_FOUND_SHORT_ID, HTTPStatus.NOT_FOUND)

    return jsonify(url=link.original), HTTPStatus.OK
