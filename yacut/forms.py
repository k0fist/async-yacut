from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp, URL

from .models import (
    ALLOWED_SHORT_RE, MAX_LENGTH_ORIGINAL_URL, MAX_LENGTH_SHORT_URL
)


TEXT_SUBMIT_URL = 'Создать'
TEXT_SUBMIT_FILES = 'Загрузить'


class LinksForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            URL(message='Введите корректный URL'),
            Length(max=MAX_LENGTH_ORIGINAL_URL)
        ]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(max=MAX_LENGTH_SHORT_URL),
            Regexp(ALLOWED_SHORT_RE,
                   message='Только латинские буквы и цифры')
        ]
    )
    submit = SubmitField(TEXT_SUBMIT_URL)


class FilesForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            DataRequired(message='Обязательное поле'),
            FileAllowed(
                ('jpg', 'jpeg', 'png', 'gif', 'bmp'),
                message=(
                    'Выберите файлы с расширением '
                    '.jpg, .jpeg, .png, .gif или .bmp'
                )
            )
        ]
    )
    submit = SubmitField(TEXT_SUBMIT_FILES)
