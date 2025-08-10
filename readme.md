# Yacut
Yacut - это веб-приложение для укорачивания ваших длинных ссылок!

Включает:

- **API**
- **Графический веб-интерфейс**

Возможности API интерфейс веб-приложения Yacut:
1. Отправлять POST запросы для создание новой короткой ссылкипо эндпоинтам - /api/id/
2. Отправлять GET запросы на получение оригинальной ссылки по указанному короткому идентификатору по эндпоинтам /api/id/{short_id}/

Автор проекта [Муллагалиев Вадим](https://github.com/k0fist)

## Техно-стек

### Язык и среда выполнения
- **Python 3.11**  
- Управление зависимостями — `pip`, `venv`
### Веб-фреймворк и расширения
- **Flask**  
  - Flask-WTF (веб-формы и валидация)  
  - Flask-SQLAlchemy (ORM)  
  - Flask-Migrate (миграции БД)  
  - Flask-RESTful или Flask-Smorest (для API) 
### Асинхронность
- **aiohttp** — асинхронные запросы к Яндекс.Диску  
- **asyncio** — организация параллельных задач 
### База данных
- **SQLite**


### Как запустить проект Yacut:

1. Клонировать репозиторий и перейти в него в командной строке:

    ```bash
    git@github.com:k0fist/async-yacut.git
    cd async-yacut
    ```

2. Создать и активировать виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/Scripts/activate   # или venv/bin/activate на Linux
   ```
3. Установить зависимости:
   ```bash
   pip install -r requirements.txt
   ```

4. Создать в директории проекта файл .env с пятью переменными окружения:

    ```
    FLASK_APP=yacut
    FLASK_ENV=development
    SECRET_KEY=your_secret_key
    DB=sqlite:///db.sqlite3
    DISK_TOKEN=secret
    ```

5. Создать базу данных и применить миграции:

    ```
    flask db upgrade
    ```

6. Запустить проект:

    ```
    flask run
    ```
