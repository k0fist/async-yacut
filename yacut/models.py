import asyncio
import random
import re
import string
from datetime import datetime
from http import HTTPStatus
from urllib.parse import urlparse

import aiohttp
from flask import url_for
from sqlalchemy.exc import IntegrityError

from .settings import db, SHORT_LINK_ENDPOINT
from .error_handlers import InvalidAPIUsage
from .yandex_disk import upload_file_to_yadisk


MSG_IMVALID_SHORT_RE = 'Указано недопустимое имя для короткой ссылки'
MSG_INVALID_URL = 'Указан некорректный URL'
MSG_DUPLICATE_SHORT = 'Предложенный вариант короткой ссылки уже существует.'
MSG_NOT_FOUND_SHORT_ID = 'Указанный id не найден'
MAX_LENGTH_ORIGINAL_URL = 2048
MAX_LENGTH_SHORT_URL = 16
ALPHABET = string.ascii_letters + string.digits
ALLOWED_SHORT_RE = re.compile(rf'^[{re.escape(ALPHABET)}]+$')
MAX_SHORT_ID_ATTEMPTS = 5


class URLMap(db.Model):
    __tablename__ = 'link'

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
    def _generate_short_id(k=6):
        """
        Генерирует уникальный короткий идентификатор длины k из ALPHABET
        с ограничением числа попыток MAX_SHORT_ID_ATTEMPTS.
        """
        for _ in range(MAX_SHORT_ID_ATTEMPTS):
            short = ''.join(random.choices(ALPHABET, k=k))
            exists = db.session.query(
                db.exists().where(URLMap.short == short)
            ).scalar()
            if not exists:
                return short

    @classmethod
    def create(cls, original: str, short: str | None = None):
        """
        Валидация и создание новой ссылки.
        Если short задан — проверяем его, иначе генерим свой.
        При дубликате бросает InvalidAPIUsage(..., 400).
        """
        parsed = urlparse(original)
        if not (parsed.scheme and parsed.netloc):
            raise InvalidAPIUsage(
                MSG_DUPLICATE_SHORT,
                HTTPStatus.BAD_REQUEST)

        if short:
            if short.lower() == 'files':
                raise InvalidAPIUsage(
                    MSG_DUPLICATE_SHORT,
                    HTTPStatus.BAD_REQUEST
                )
            if not ALLOWED_SHORT_RE.fullmatch(short):
                raise InvalidAPIUsage(
                    MSG_IMVALID_SHORT_RE,
                    HTTPStatus.BAD_REQUEST
                )
            if len(short) > MAX_LENGTH_SHORT_URL:
                raise InvalidAPIUsage(
                    MSG_IMVALID_SHORT_RE,
                    HTTPStatus.BAD_REQUEST
                )
            short = short
        else:
            short = cls._generate_short_id()

        obj = cls(original=original, short=short)

        db.session.add(obj)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise InvalidAPIUsage(
                MSG_DUPLICATE_SHORT,
                HTTPStatus.BAD_REQUEST
            )

        return obj

    @classmethod
    def get_short(cls, short_code: str):
        """
        Возвращает объект по короткому коду или бросает 404-InvalidAPIUsage.
        """
        link = cls.query.filter_by(short=short_code).first()
        if not link:
            raise InvalidAPIUsage(
                MSG_NOT_FOUND_SHORT_ID,
                HTTPStatus.NOT_FOUND
            )
        return link

    @property
    def public_url(self) -> str:
        """
        Возвращает внешний URL, по которому доступна эта коротюлька.
        """
        return url_for(
            SHORT_LINK_ENDPOINT,
            slug=self.short,
            _external=True
        )

    @classmethod
    async def bulk_create_from_uploads(cls, files, token):
        """
        Параллельно загружает список `files` на Яндекс.Диск,
        генерирует короткие ссылки и сохраняет их, возвращает список
        словарей {filename, public_url}.
        """
        async with aiohttp.ClientSession() as sess:
            tasks = [
                upload_file_to_yadisk(sess, f, token)
                for f in files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        paired = []
        for uploaded, href in zip(files, results):
            if isinstance(href, Exception):
                continue

            try:
                link = cls.create(href, None)
            except InvalidAPIUsage:
                continue

            paired.append({
                'filename': uploaded.filename,
                'public_url': link.public_url
            })

        return paired