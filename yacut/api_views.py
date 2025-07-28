from http import HTTPStatus
from flask import jsonify, request
from urllib.parse import urlparse

from .error_handlers import InvalidAPIUsage
from .models import URLMap, NOT_FOUND_SHORT_ID, ValidationError, INVALID_URL
from .settings import app


MISSING_BODY = 'Отсутствует тело запроса'
REQUIRED_URL = '"url" является обязательным полем!'


@app.route('/api/id/', methods=['POST'])
def api_create_id():
    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage(MISSING_BODY, HTTPStatus.BAD_REQUEST)

    original = data.get('url')
    if not original:
        raise InvalidAPIUsage(REQUIRED_URL, HTTPStatus.BAD_REQUEST)

    parsed = urlparse(original)
    if not (parsed.scheme and parsed.netloc):
        raise InvalidAPIUsage(INVALID_URL, HTTPStatus.BAD_REQUEST)

    short = data.get('custom_id')
    try:
        url = URLMap.create_api(original, short)
    except ValidationError as error:
        raise InvalidAPIUsage(
            str(error),
            HTTPStatus.BAD_REQUEST
        )

    return jsonify(url=original, short_link=url.public_url), HTTPStatus.CREATED


@app.route('/api/id/<string:short>/', methods=['GET'])
def api_get_url(short):
    try:
        URLMap.validate_short_code(short)
    except ValidationError:
        raise InvalidAPIUsage(
            NOT_FOUND_SHORT_ID,
            HTTPStatus.NOT_FOUND
        )
    url = URLMap.get_short(short)
    return jsonify(url=url.original), HTTPStatus.OK
