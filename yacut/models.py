from datetime import datetime
import string
import random

from yacut.settings import db


def get_unique_short_id(k=6):
    """
    Генерирует случайный идентификатор длины k из [A–Z, a–z, 0–9]
    и гарантирует его уникальность в таблице URLMap.
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        short_id = ''.join(random.choices(alphabet, k=k))
        exists = db.session.query(
            db.exists().where(URLMap.short == short_id)
        ).scalar()
        if not exists:
            return short_id


class URLMap(db.Model):
    __tablename__ = 'link'

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(256), nullable=True)
    download_url = db.Column(db.Text, nullable=True)

    short = db.Column(
        db.String(16),
        nullable=False,
        unique=True,
        default=get_unique_short_id
    )

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def is_web(self):
        return self.original is not None

    def is_file(self):
        return self.download_url is not None

    def to_dict(self):
        return dict(
            id=self.id,
            original=self.original,
            filename=self.filename,
            download_url=self.download_url,
            short=self.short,
            timestamp=self.timestamp
        )

    def from_dict(self, data):
        for field in ['original', 'filename', 'download_url', 'short']:
            if field in data:
                setattr(self, field, data[field])
