from http import HTTPStatus

from flask import jsonify, request

from .error_handlers import InvalidAPIUsage
from .models import NOT_FOUND_SHORT_ID, URLMap, ValidationError
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

    try:
        mapping = URLMap.create(
            original,
            short,
            validate_short=True
        )
    except (ValidationError, RuntimeError) as e:
        raise InvalidAPIUsage(str(e))

    return jsonify(
        url=original,
        short_link=mapping.public_url
    ), HTTPStatus.CREATED


@app.route('/api/id/<string:short>/', methods=['GET'])
def api_get_url(short):
    mapping = URLMap.get(short)
    if mapping is None:
        raise InvalidAPIUsage(NOT_FOUND_SHORT_ID, HTTPStatus.NOT_FOUND)

    return jsonify(url=mapping.original), HTTPStatus.OK
