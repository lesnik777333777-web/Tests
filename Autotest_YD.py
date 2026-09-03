import os
import requests
import pytest

# -------------------------------------------------------------------
# 1. КОНФИГУРАЦИЯ
# -------------------------------------------------------------------

BASE_URL = "https://cloud-api.yandex.net/v1/disk"
TOKEN = os.getenv("YANDEX_TOKEN")  # токен должен быть передан через переменную окружения

# Если токен не задан, тесты пропускаются
pytestmark = pytest.mark.skipif(not TOKEN, reason="YANDEX_TOKEN not set")

HEADERS = {
    "Authorization": f"OAuth {TOKEN}",
    "Content-Type": "application/json"
}


# -------------------------------------------------------------------
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# -------------------------------------------------------------------

def create_folder(path):
    """Создать папку на Яндекс.Диске."""
    url = f"{BASE_URL}/resources"
    params = {"path": path}
    response = requests.put(url, headers=HEADERS, params=params)
    return response

def delete_folder(path):
    """Удалить папку (для очистки после тестов)."""
    url = f"{BASE_URL}/resources"
    params = {"path": path, "permanently": True}
    response = requests.delete(url, headers=HEADERS, params=params)
    return response

def folder_exists(path):
    """Проверить, существует ли папка."""
    url = f"{BASE_URL}/resources"
    params = {"path": path}
    response = requests.get(url, headers=HEADERS, params=params)
    return response.status_code == 200


# -------------------------------------------------------------------
# 3. ТЕСТЫ
# -------------------------------------------------------------------

class TestYandexDiskCreateFolder:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Фикстура для создания уникальной папки перед тестом и удаления после."""
        self.folder_name = f"test_folder_{os.urandom(4).hex()}"
        self.folder_path = f"/{self.folder_name}"
        yield
        # После теста удаляем папку, если она существует
        if folder_exists(self.folder_path):
            delete_folder(self.folder_path)

    # ---------- ПОЗИТИВНЫЙ ТЕСТ ----------
    def test_create_folder_success(self):
        """Успешное создание папки – код 201, папка появляется в списке."""
        response = create_folder(self.folder_path)

        # 1. Проверка статуса (согласно документации Яндекса – 201)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        # 2. Проверка, что папка действительно создалась
        assert folder_exists(self.folder_path), "Folder was not found after creation"

        # 3. (Опционально) тело ответа содержит путь
        assert response.json().get("href") is not None

    # ---------- НЕГАТИВНЫЕ ТЕСТЫ (параметризованные) ----------
    @pytest.mark.parametrize("scenario", [
        {
            "name": "duplicate_folder",
            "path": "/existing_folder",
            "expected_status": 409,
            "expected_reason": "Conflict"
        },
        {
            "name": "invalid_path",
            "path": "invalid_path_without_slash",
            "expected_status": 400,
            "expected_reason": "Bad Request"
        },
        {
            "name": "empty_path",
            "path": "",
            "expected_status": 400,
            "expected_reason": "Bad Request"
        },
        # Можно добавить тест без токена, но в нашей конфигурации он пропускается,
        # поэтому создадим отдельный тест ниже
    ])
    def test_create_folder_negative(self, scenario):
        """Негативные сценарии создания папки."""
        # Для теста дублирования создаём папку заранее
        if scenario["name"] == "duplicate_folder":
            create_folder("/existing_folder")  # создаём папку

        response = create_folder(scenario["path"])
        assert response.status_code == scenario["expected_status"], \
            f"Expected {scenario['expected_status']}, got {response.status_code}"
        assert scenario["expected_reason"] in response.text, \
            f"Expected error reason '{scenario['expected_reason']}' not in response"

    # ---------- ТЕСТ БЕЗ ТОКЕНА (отдельно, так как он пропускается выше) ----------
    def test_create_folder_no_token(self, monkeypatch):
        """Попытка создания без токена – ожидаем 401."""
        monkeypatch.delenv("YANDEX_TOKEN", raising=False)
        headers_no_auth = HEADERS.copy()
        headers_no_auth.pop("Authorization", None)
        url = f"{BASE_URL}/resources"
        params = {"path": "/no_token_folder"}
        response = requests.put(url, headers=headers_no_auth, params=params)
        assert response.status_code == 401
        assert "Unauthorized" in response.text