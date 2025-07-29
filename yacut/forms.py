from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    StringField, SubmitField, URLField, ValidationError as WTValidationError
)
from wtforms.validators import DataRequired, Length, Optional, Regexp, URL

from .models import (
    ALLOWED_SHORT_RE, MAX_LENGTH_ORIGINAL_URL, MAX_LENGTH_SHORT, URLMap
)


TEXT_SUBMIT_URL = 'Создать'
TEXT_SUBMIT_FILES = 'Загрузить'
LONG_ORIGINAL_LINK = 'Длинная ссылка'
REQUIRED_FIELD = 'Обязательное поле'
ENTER_CORRECT_URL = 'Введите корректный URL'
YOUR_OPTION_SHORT = 'Ваш вариант короткой ссылки'
ONLY_LATIN_LETTERS_AND_NUMBERS = 'Только латинские буквы и цифры'
ACCEPTABLE_EXTENSIONS = 'jpg', 'jpeg', 'png', 'gif', 'bmp'


class LinksForm(FlaskForm):
    original_link = URLField(
        LONG_ORIGINAL_LINK,
        validators=[
            DataRequired(message=REQUIRED_FIELD),
            URL(message=ENTER_CORRECT_URL),
            Length(max=MAX_LENGTH_ORIGINAL_URL)
        ]
    )
    custom_id = StringField(
        YOUR_OPTION_SHORT,
        validators=[
            Optional(),
            Length(max=MAX_LENGTH_SHORT),
            Regexp(
                ALLOWED_SHORT_RE,
                message=ONLY_LATIN_LETTERS_AND_NUMBERS
            )
        ]
    )
    submit = SubmitField(TEXT_SUBMIT_URL)

    def validate_custom_id(self, field):
        if field.data:
            try:
                URLMap.validate_short_code(field.data)
            except Exception as e:
                raise WTValidationError(str(e))


class FilesForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            DataRequired(message=REQUIRED_FIELD),
            FileAllowed(
                (ACCEPTABLE_EXTENSIONS),
                message=(
                    'Выберите файлы с расширением '
                    f'{ACCEPTABLE_EXTENSIONS}'
                )
            )
        ]
    )
    submit = SubmitField(TEXT_SUBMIT_FILES)
