from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class LinksForm(FlaskForm):
    original_link = StringField(
        'Длинная ссылка',
        validators=[DataRequired(message='Обязательное поле')]
    )
    custom_id = StringField(
        'Ваш вариант короткой ссылки',
        validators=[Length(1, 16), Optional()]
    )
    submit = SubmitField('Создать')


class FilesForm(FlaskForm):
    files = MultipleFileField(
        validators=[
            DataRequired(message='Обязательное поле'),
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                message=(
                    'Выберите файлы с расширением '
                    '.jpg, .jpeg, .png, .gif или .bmp'
                )
            )
        ]
    )
    submit = SubmitField('Загрузить')