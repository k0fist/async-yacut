import random
from datetime import datetime
from urllib.parse import urlparse

from flask import url_for

from .constants import (
    MAX_LENGTH_ORIGINAL_URL, MAX_LENGTH_SHORT, SHORT_CHARACTERS,
    ALLOWED_SHORT_RE, MAX_SHORT_ATTEMPTS, DEFAULT_SHORT_LENGTH
)
from .settings import db, SHORT_LINK_ENDPOINT
from typing import Optional


IMVALID_SHORT_RE = 'Указано недопустимое имя для короткой ссылки'
INVALID_URL = 'Указан некорректный URL'
DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
NOT_FOUND_SHORT_ID = 'Указанный id не найден'
ERROR_UNIQUE_SHORT = (
    f'Не удалось сгенерировать уникальный короткий код '
    f'за {MAX_SHORT_ATTEMPTS} попыток'
)


class ValidationError(Exception):
    pass


class URLMap(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(
        db.String(MAX_LENGTH_ORIGINAL_URL),
        nullable=True
    )

    short = db.Column(
        db.String(MAX_LENGTH_SHORT),
        nullable=False,
        unique=True
    )

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def _generate_short_id():
        """
        Генерирует уникальный короткий идентификатор длины SHORT_CHARACTERS
        с ограничением числа попыток MAX_SHORT_ATTEMPTS.
        """
        for _ in range(MAX_SHORT_ATTEMPTS):
            short = ''.join(random.choices(
                SHORT_CHARACTERS,
                k=DEFAULT_SHORT_LENGTH
            ))
            if URLMap.get(short) is None:
                return short
        raise RuntimeError(
            ERROR_UNIQUE_SHORT
        )

    @staticmethod
    def create(
        original: str,
        short: Optional[str] = None,
        validate_short: bool = False
    ) -> 'URLMap':

        if validate_short:
            if len(original) > MAX_LENGTH_ORIGINAL_URL:
                raise ValidationError(INVALID_URL)
            parsed = urlparse(original)
            if not (parsed.scheme and parsed.netloc):
                raise ValidationError(INVALID_URL)

        if validate_short and short:
            if len(short) > MAX_LENGTH_SHORT:
                raise ValidationError(IMVALID_SHORT_RE)

            if short.lower() == 'files':
                raise ValidationError(DUPLICATE_SHORT)

            if not ALLOWED_SHORT_RE.fullmatch(short):
                raise ValidationError(IMVALID_SHORT_RE)

            if URLMap.get(short) is not None:
                raise ValidationError(DUPLICATE_SHORT)

        short = short or URLMap._generate_short_id()

        mapping = URLMap(original=original, short=short)
        db.session.add(mapping)
        db.session.commit()
        return mapping

    @staticmethod
    def get(short: str):
        return URLMap.query.filter_by(short=short).first()

    @property
    def public_url(self) -> str:
        return url_for(
            SHORT_LINK_ENDPOINT,
            slug=self.short,
            _external=True
        )

    @staticmethod
    def bulk_create(urls):
        """
        По списку исходных URL генерирует короткие коды
        и сохраняет их через create, возвращает список объектов URLMap.
        """
        return [URLMap.create(url) for url in urls]
