from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp, URL
from .settings import MAX_LENGTH_CUSTOM_URL

MIN_LENGTH = 1


class LinksForm(FlaskForm):
    original_link = URLField(
        'Длинная ссылка',
        validators=[
            DataRequired(message='Обязательное поле'),
            URL(message='Введите корректный URL')
        ]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[
            Optional(),
            Length(max=MAX_LENGTH_CUSTOM_URL),
            Regexp(r'^[A-Za-z0-9]+$',
                   message='Только латинские буквы и цифры')
        ]
    )
    submit = SubmitField('Создать')


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
    submit = SubmitField('Загрузить')