### Как запустить проект Yacut:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone 
```

```
cd yacut
```

Cоздать и активировать виртуальное окружение:

```
python -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

Установить зависимости из файла requirements.txt:

```
python -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Создать в директории проекта файл .env с пятью переменными окружения:

```
FLASK_APP=yacut
FLASK_ENV=development
SECRET_KEY=your_secret_key
DB=sqlite:///db.sqlite3
DISK_TOKEN=secret
```

Создать базу данных и применить миграции:

```
flask db upgrade
```

Запустить проект:

```
flask run
```
