import os
import uuid
import httpx
import pytest
from dotenv import load_dotenv
from pathlib import Path
import logging

load_dotenv()
logger = logging.getLogger(__name__)


@pytest.fixture
def get_token():
    def _make_token(username=None, password=None):
        client = ApiClient().client
        req_body = {'username': username, 'password': password}
        response = client.post("login/", json=req_body)

        if response.status_code == 200:
            logger.info('Успешная авторизация')
            response_data = response.json()
            access_token = response_data.get('access_token')
            # print(response_data)
            return access_token
        else:
            logger.error(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return None

    return _make_token


class ApiClient:
    def __init__(self, access_token=None):
        self.access_token = access_token
        headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        self.client = httpx.Client(
            base_url=os.getenv('URL'),
            headers=headers,
            timeout=30.0
        )


class ApiEndpoints:
    def __init__(self, access_token=None):
        self.client = ApiClient(access_token).client

    def check_state(self):
        response = self.client.get("health")
        return True if response.status_code == 200 else None

    def registration(self, username, password, role='user', age_confirmed='true', terms_accepted='true'):
        req_body = {'username': username, 'password': password, 'role': role, 'age_confirmed': age_confirmed,
                    'terms_accepted': terms_accepted}
        response = self.client.post("users/", json=req_body)
        if response.status_code != 200:
            logger.error(f"Ошибка при регистрации, код: {response.status_code}, текст: {response.text}")
        return True if response.status_code == 200 else None

    def login(self, username, password):
        req_body = {'username': username, 'password': password}
        response = self.client.post("login/", json=req_body)
        if response.status_code != 200:
            logger.error(f"Ошибка при авторизации, код: {response.status_code}, текст: {response.text}")
        return True if response.status_code == 200 else None

    def get_tests(self):
        response = self.client.get("tests/")
        if response.status_code != 200:
            logger.error(f"Ошибка при получении тестов, код: {response.status_code}, текст: {response.text}")
        return True if response.status_code == 200 else None

    def analyse_image(self, access_token, session_id, test_type, file_paths):

        data = {
            "session_id": session_id,
            "testType": test_type
        }

        files = []
        opened_files = []

        try:
            for path in file_paths:
                file = open(path, "rb")
                opened_files.append(file)
                files.append(("images", (os.path.basename(path), file, "image/png")))

            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            response = self.client.post("analyze-image/", data=data, files=files, headers=headers)

        finally:
            for file in opened_files:
                file.close()
        if response.status_code != 200:
            logger.error(f"Ошибка при анализе, код: {response.status_code}, текст: {response.text}")
        return True if response.status_code == 200 else None


class TestApi:
    def test_smoke_pipeline(self, get_token):
        apiendpoints = ApiEndpoints()

        assert apiendpoints.check_state() is True, "Сервис недоступен"

        access_token = get_token('test1', 'Test1235678!')
        if not access_token:
            apiendpoints = ApiEndpoints()
            assert apiendpoints.registration('test1', 'Test1235678!') is True, "Регистрация провалена"
            access_token = get_token('test1', 'Test1235678!')

        apiendpoints = ApiEndpoints(access_token)

        assert apiendpoints.get_tests() is True, "Тесты не получены"
        session_id = str(uuid.uuid4())
        img_path = str(Path("uploads") / "26181120-4a4b-4ecd-8fb8-717be52bbeda.png")
        img_list = [img_path]
        assert apiendpoints.analyse_image(access_token, session_id, 'full-height-analysis', img_list) is True, \
            "Анализ изображения провален"

        logger.info("Smoke-test completed")

    def test_negative(self, get_token):
        apiendpoints = ApiEndpoints()

        # Проверка можно ли получить токен по несуществующим данным
        assert get_token('1111', 'Test1235678!') is None, "Токен получен по несуществующим данным"

        # Регистрация с невалидным паролем
        assert apiendpoints.registration('test', 'Test1235678') is None, "Регистрация с паролем без спецсимволов"
        assert apiendpoints.registration('test', 'Test1!') is None, "Регистрация с паролем меньше 8 символов"
        assert apiendpoints.registration('test', 'Test 1!23') is None, "Регистрация с паролем с пробелами"
        assert apiendpoints.registration('test', 'Teст1!23!!') is None, "Регистрация с паролем со смешанной раскладкой"

        access_token = get_token('test', 'Test1235678!')
        if not access_token:
            apiendpoints = ApiEndpoints()
            assert apiendpoints.registration('test', 'Test1235678!') is True, "Регистрация провалена"
            access_token = get_token('test', 'Test1235678!')

        apiendpoints = ApiEndpoints(access_token)
        session_id = str(uuid.uuid4())

        # Отправка изображения с невалидным токеном
        img_path = str(Path("uploads") / "26181120-4a4b-4ecd-8fb8-717be52bbeda.png")
        img_list = [img_path]
        assert apiendpoints.analyse_image("test", session_id, 'full-height-analysis', img_list) is None, \
            "Отправка изображения c невалидным токеном"

        # Отправка изображения c неправильным session id
        assert apiendpoints.analyse_image(access_token, "1234567", 'full-height-analysis', img_list) is None, \
            "Отправка изображения c неправильным session id"

        # Отправка изображения c несуществующим test type
        assert apiendpoints.analyse_image(access_token, session_id, 'test', img_list) is None, \
            "Отправка изображения c несуществующим test type"

        # Отправка пустого списка
        img_list = []
        assert apiendpoints.analyse_image(access_token, session_id, 'full-height-human', img_list) is None, \
            "Отправка изображения c несуществующим test type"

        # Отправка битого изображения
        img_path = str(Path("uploads") / "broken_image.png")
        img_list = [img_path]
        assert apiendpoints.analyse_image(access_token, session_id, 'full-height-analysis', img_list) is None, \
            "Анализ изображения провален"

        logger.info("Negative-test completed")
