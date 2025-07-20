from datetime import datetime

from .settings import db
from .sequence_generator import get_unique_short_id


class URLMap(db.Model):
    __tablename__ = 'link'

    id = db.Column(db.Integer, primary_key=True)
    original = db.Column(db.Text, nullable=True)

    short = db.Column(
        db.String(16),
        nullable=False,
        unique=True,
        default=get_unique_short_id
    )

    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    
