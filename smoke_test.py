import os
import uuid
import httpx
from dotenv import load_dotenv

load_dotenv()


class ApiClient:
    def __init__(self):
        self.api_url = os.getenv('URL')
        self.username = os.getenv('USERNAME_MENTALARTAI')
        self.password = os.getenv('PASSWORD_MENTALARTAI')

    def check_state(self):
        response = httpx.get(f"{self.api_url}api/health")
        if response.status_code == 200:
            print('Сервис работает')
            return True
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return False

    def get_token(self, username=None, password=None):
        if (username or password) is None:
            username = self.username
            password = self.password
        req_body = {'username': username, 'password': password}
        response = httpx.post(f"{self.api_url}api/login/", json=req_body)

        if response.status_code == 200:
            print('Успешная авторизация')
            response_data = response.json()
            access_token = response_data.get('access_token')
            # print(response_data)
            return access_token
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return None


class ApiEndpoints:
    def __init__(self, access_token=None):
        self.access_token = access_token
        self.api_url = os.getenv('URL')

    def registration(self, username, password, role='user', age_confirmed='true', terms_accepted='true'):
        req_body = {'username': username, 'password': password, 'role': role, 'age_confirmed': age_confirmed,
                    'terms_accepted': terms_accepted}
        response = httpx.post(f"{self.api_url}api/users/", json=req_body)

        if response.status_code == 200:
            print('Успешная регистрация')
            return True
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return False

    def login(self, username, password):
        req_body = {'username': username, 'password': password}
        response = httpx.post(f"{self.api_url}api/login/", json=req_body)

        if response.status_code == 200:
            print('Успешная авторизация')
            return True
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return False

    def get_tests(self):
        response = httpx.get(f"{self.api_url}api/tests/")

        if response.status_code == 200:
            print('Тесты успешно получены')
            return True
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return False

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
            response = httpx.post(f"{self.api_url}api/analyze-image/", data=data, files=files, headers=headers)

        finally:
            for file in opened_files:
                file.close()

        if response.status_code == 200:
            print(f'Тест {test_type} успешно пройден')
            return True
        else:
            print(f"Ошибка, код ответа: {response.status_code}, текст ответа: {response.text}")
            return False


class ApiTests:
    def __init__(self):
        self.client = ApiClient()

    def test_smoke_pipeline(self):
        if self.client.check_state():
            access_token = self.client.get_token('test', 'Test1235678!')
            if not access_token:
                apiendpoints = ApiEndpoints()
                if apiendpoints.registration('test', 'Test1235678!'):
                    print("Регистрация выполнена, продолжение выполнения...")
                else:
                    return

            apiendpoints = ApiEndpoints(access_token)
            if apiendpoints.get_tests():
                session_id = str(uuid.uuid4())
                img_list = []
                img_list.append(f".\\images\\26181120-4a4b-4ecd-8fb8-717be52bbeda.png")
                apiendpoints.analyse_image(access_token, session_id, 'full-height-human', img_list)


apitest = ApiTests()
apitest.test_smoke_pipeline()