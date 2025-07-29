import random
from datetime import datetime

from flask import url_for

from .constants import (
    MAX_LENGTH_ORIGINAL_URL, MAX_LENGTH_SHORT, SHORT_ID_CHARACTERS,
    ALLOWED_SHORT_RE, MAX_SHORT_ATTEMPTS, DEFAULT_SHORT_ID_LENGTH
)
from .settings import db, SHORT_LINK_ENDPOINT
from typing import Optional


IMVALID_SHORT_RE = 'Указано недопустимое имя для короткой ссылки'
INVALID_URL = 'Указан некорректный URL'
DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
NOT_FOUND_SHORT_ID = 'Указанный id не найден'
ERROR_UNIQUE_SHORT = ('Не удалось сгенерировать уникальный короткий '
                      'код за {attempts} попыток')


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
        unique=True,
        default=lambda: URLMap._generate_short_id()
    )

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    @staticmethod
    def _generate_short_id():
        """
        Генерирует уникальный короткий идентификатор длины SHORT_ID_CHARACTERS
        с ограничением числа попыток MAX_SHORT_ATTEMPTS.
        """
        for _ in range(MAX_SHORT_ATTEMPTS):
            short = ''.join(random.choices(
                SHORT_ID_CHARACTERS,
                k=DEFAULT_SHORT_ID_LENGTH
            ))
            if URLMap.get_link(short) is None:
                return short
        raise RuntimeError(
            ERROR_UNIQUE_SHORT.format(attempts=MAX_SHORT_ATTEMPTS)
        )

    @staticmethod
    def validate_short_code(code: str) -> None:
        """
        Валидация пользовательского short-кода:
        — не пустой
        — не зарезервирован ("files")
        — только из SHORT_ID_CHARACTERS
        — не длиннее MAX_LENGTH_SHORT
        - уникальное название
        Бросает InvalidAPIUsage с кодом 400, если что не так.
        """

        if len(code) > MAX_LENGTH_SHORT:
            raise ValidationError(IMVALID_SHORT_RE)

        if code.lower() == 'files':
            raise ValidationError(DUPLICATE_SHORT)

        if not ALLOWED_SHORT_RE.fullmatch(code):
            raise ValidationError(IMVALID_SHORT_RE)

        if URLMap.query.filter_by(short=code).first() is not None:
            raise ValidationError(DUPLICATE_SHORT)

    @staticmethod
    def create(original: str, short: Optional[str] = None) -> 'URLMap':

        short_code = short or URLMap._generate_short_id()

        link = URLMap(original=original, short=short_code)
        db.session.add(link)
        db.session.commit()
        return link

    @staticmethod
    def get_link(short: str):
        link = URLMap.query.filter_by(short=short).first()
        return link

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
