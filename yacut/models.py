import random
import re
import string
from datetime import datetime

from flask import url_for, abort
from sqlalchemy.exc import IntegrityError

from .settings import db, SHORT_LINK_ENDPOINT
from typing import Optional


IMVALID_SHORT_RE = 'Указано недопустимое имя для короткой ссылки'
INVALID_URL = 'Указан некорректный URL'
DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
NOT_FOUND_SHORT_ID = 'Указанный id не найден'
MAX_LENGTH_ORIGINAL_URL = 2048
MAX_LENGTH_SHORT_URL = 16
SHORT_ID_CHARACTERS = string.ascii_letters + string.digits
ALLOWED_SHORT_RE = re.compile(rf'^[{re.escape(SHORT_ID_CHARACTERS )}]+$')
MAX_SHORT_ID_ATTEMPTS = 5
DEFAULT_SHORT_ID_LENGTH = 6


class ValidationError(Exception):
    pass


class URLMap(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(
        db.String(MAX_LENGTH_ORIGINAL_URL),
        nullable=True
    )

    short = db.Column(
        db.String(MAX_LENGTH_SHORT_URL),
        nullable=False,
        unique=True,
        default=lambda: URLMap._generate_short_id()
    )

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def _generate_short_id():
        """
        Генерирует уникальный короткий идентификатор длины SHORT_ID_CHARACTERS
        с ограничением числа попыток MAX_SHORT_ID_ATTEMPTS.
        """
        for _ in range(MAX_SHORT_ID_ATTEMPTS):
            short = ''.join(random.choices(
                SHORT_ID_CHARACTERS,
                k=DEFAULT_SHORT_ID_LENGTH
            ))
            if URLMap.query.filter_by(short=short).first() is None:
                return short
        raise RuntimeError(
            f'Не удалось сгенерировать уникальный короткий код за '
            f'{MAX_SHORT_ID_ATTEMPTS} попыток'
        )

    @staticmethod
    def validate_short_code(code: str) -> None:
        """
        Валидация пользовательского short-кода:
        — не пустой
        — не зарезервирован ("files")
        — только из SHORT_ID_CHARACTERS
        — не длиннее MAX_LENGTH_SHORT_URL
        Бросает InvalidAPIUsage с кодом 400, если что не так.
        """
        if not code:
            raise ValidationError(IMVALID_SHORT_RE)

        if len(code) > MAX_LENGTH_SHORT_URL:
            raise ValidationError(IMVALID_SHORT_RE)

        if code == 'files':
            raise ValidationError(DUPLICATE_SHORT)

        if not ALLOWED_SHORT_RE.fullmatch(code):
            raise ValidationError(IMVALID_SHORT_RE)

    @staticmethod
    def save(original: str, short: Optional[str] = None):

        obj = URLMap(original=original, short=short)

        db.session.add(obj)
        db.session.commit()
        return obj

    @staticmethod
    def create_api(original: str, custom: Optional[str] = None) -> 'URLMap':
        """
        Для API: выполняет валидацию URL + custom, генерирует short
        и сохраняет через save.
        """

        if custom:
            URLMap.validate_short_code(custom)
            short_code = custom
        else:
            short_code = URLMap._generate_short_id()

        try:
            return URLMap.save(original, short_code)
        except IntegrityError:
            raise ValidationError(
                DUPLICATE_SHORT
            )

    @staticmethod
    def get_short(short_code: str):
        """
        Возвращает объект по короткому коду или бросает 404-InvalidAPIUsage.
        """
        link = URLMap.query.filter_by(short=short_code).first()
        if link is None:
            abort(404)
        return link

    @property
    def public_url(self) -> str:
        return url_for(
            SHORT_LINK_ENDPOINT,
            slug=self.short,
            _external=True
        )

    @staticmethod
    def bulk_create(originals):

        created = []
        for original in originals:
            link = URLMap.create_api(original, None)
            created.append(link)
        return created