import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# -------------------------------------------------------------------
# 1. КОНФИГУРАЦИЯ
# -------------------------------------------------------------------

LOGIN_URL = "https://passport.yandex.ru/auth"
# Данные для тестов берём из переменных окружения (не храним в коде!)
VALID_LOGIN = os.getenv("YANDEX_LOGIN")
VALID_PASSWORD = os.getenv("YANDEX_PASSWORD")
INVALID_LOGIN = "invalid_login"
INVALID_PASSWORD = "wrong_password"

# Пропускаем все тесты, если не заданы валидные учётные данные
pytestmark = pytest.mark.skipif(
    not VALID_LOGIN or not VALID_PASSWORD,
    reason="YANDEX_LOGIN and YANDEX_PASSWORD must be set"
)


# -------------------------------------------------------------------
# 2. FIXTURE: ЗАПУСК И ЗАКРЫТИЕ БРАУЗЕРА
# -------------------------------------------------------------------

@pytest.fixture
def driver():
    """Создаёт экземпляр ChromeDriver и закрывает его после теста."""
    options = webdriver.ChromeOptions()
    # Раскомментируйте для headless-режима (без графического интерфейса)
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    yield driver
    driver.quit()


# -------------------------------------------------------------------
# 3. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# -------------------------------------------------------------------

def login(driver, login, password):
    """
    Выполняет авторизацию на passport.yandex.ru.
    Возвращает True, если удалось войти, иначе False.
    """
    driver.get(LOGIN_URL)

    try:
        # 1. Вводим логин
        login_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "passp-field-login"))
        )
        login_field.send_keys(login)

        # 2. Нажимаем кнопку "Войти" (или нажимаем Enter)
        login_field.submit()

        # 3. Ждём появления поля для пароля
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "passp-field-passwd"))
        )
        password_field.send_keys(password)

        # 4. Отправляем форму
        password_field.submit()

        # 5. Проверяем успешность: ждём редиректа или появления элемента,
        #    который есть только в личном кабинете.
        #    Например, можно проверить URL или наличие кнопки профиля.
        WebDriverWait(driver, 10).until(
            EC.url_contains("passport.yandex.ru") is False
            or EC.presence_of_element_located((By.CLASS_NAME, "user-pic"))
        )
        return True

    except (TimeoutException, NoSuchElementException):
        return False


def is_logged_in(driver):
    """Проверяет, что пользователь успешно авторизован (находится на странице профиля)."""
    # Можно проверять наличие элемента, который виден только после входа
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "user-pic"))
        )
        return True
    except TimeoutException:
        return False


# -------------------------------------------------------------------
# 4. ТЕСТЫ
# -------------------------------------------------------------------

class TestYandexAuthorization:

    # ---------- ПОЗИТИВНЫЙ ТЕСТ ----------
    def test_valid_login(self, driver):
        """Успешный вход с корректными логином и паролем."""
        result = login(driver, VALID_LOGIN, VALID_PASSWORD)
        assert result is True, "Не удалось войти с валидными данными"
        assert is_logged_in(driver), "После входа не найден элемент профиля"

    # ---------- НЕГАТИВНЫЕ ТЕСТЫ (параметризованные) ----------
    @pytest.mark.parametrize("login,password,expected_error", [
        (INVALID_LOGIN, VALID_PASSWORD, "Неверный логин или пароль"),
        (VALID_LOGIN, INVALID_PASSWORD, "Неверный логин или пароль"),
        (INVALID_LOGIN, INVALID_PASSWORD, "Неверный логин или пароль"),
        ("", VALID_PASSWORD, "Логин не может быть пустым"),   # пустой логин
        (VALID_LOGIN, "", "Пароль не может быть пустым"),    # пустой пароль
    ])
    def test_invalid_login(self, driver, login, password, expected_error):
        """Негативные сценарии: неверный логин/пароль, пустые поля."""
        driver.get(LOGIN_URL)

        try:
            # Вводим логин (если он не пустой)
            if login:
                login_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "passp-field-login"))
                )
                login_field.send_keys(login)
                login_field.submit()

            # Вводим пароль (если он не пустой)
            if password:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "passp-field-passwd"))
                )
                password_field.send_keys(password)
                password_field.submit()

            # Проверяем, что появилось сообщение об ошибке
            error_msg = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "passp-form-field__error"))
            )
            assert expected_error in error_msg.text, \
                f"Ожидалось сообщение '{expected_error}', получено '{error_msg.text}'"

        except TimeoutException:
            # Если поле не появилось – значит, тест упал (негативный сценарий не сработал)
            pytest.fail("Не появилось поле для ввода или сообщение об ошибке")