from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    StringField, SubmitField, URLField, ValidationError as WTValidationError
)
from wtforms.validators import DataRequired, Length, Optional, Regexp, URL

from .models import (
    ALLOWED_SHORT_RE, MAX_LENGTH_ORIGINAL_URL, MAX_LENGTH_SHORT,
    URLMap, DUPLICATE_SHORT
)


TEXT_SUBMIT_URL = 'Создать'
TEXT_SUBMIT_FILES = 'Загрузить'
LONG_ORIGINAL_LINK = 'Длинная ссылка'
REQUIRED_FIELD = 'Обязательное поле'
ENTER_CORRECT_URL = 'Введите корректный URL'
YOUR_OPTION_SHORT = 'Ваш вариант короткой ссылки'
ONLY_LATIN_LETTERS_AND_NUMBERS = 'Только латинские буквы и цифры'
ACCEPTABLE_EXTENSIONS = 'jpg', 'jpeg', 'png', 'gif', 'bmp'
CHOOSING_EXTENSIONS = ('Выберите файлы с расширением '
                       f'{ACCEPTABLE_EXTENSIONS}')


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
        if not field.data:
            return

        if field.data.lower() == 'files':
            raise WTValidationError(DUPLICATE_SHORT)

        if URLMap.get(field.data):
            raise WTValidationError(DUPLICATE_SHORT)


class FilesForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            DataRequired(message=REQUIRED_FIELD),
            FileAllowed(
                ACCEPTABLE_EXTENSIONS,
                message=(
                    CHOOSING_EXTENSIONS
                )
            )
        ]
    )
    submit = SubmitField(TEXT_SUBMIT_FILES)
