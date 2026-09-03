import csv
import re
from pprint import pprint

# Чтение исходного файла
with open("phonebook_raw.csv", encoding="utf-8") as f:
    rows = csv.reader(f, delimiter=",")
    contacts_list = list(rows)

# Заголовок (первая строка)
header = contacts_list[0]
data_rows = contacts_list[1:]  # остальные строки

# 1. Нормализация ФИО (первые три поля)
def normalize_names(row):
    # Берём первые три элемента, объединяем через пробел и разбиваем по пробелам
    full_name_parts = ' '.join(row[:3]).split()
    # Заполняем поля lastname, firstname, surname
    lastname = full_name_parts[0] if len(full_name_parts) > 0 else ''
    firstname = full_name_parts[1] if len(full_name_parts) > 1 else ''
    surname = full_name_parts[2] if len(full_name_parts) > 2 else ''
    # Возвращаем обновлённую строку (первые три поля заменены)
    row[0] = lastname
    row[1] = firstname
    row[2] = surname
    return row

# 2. Нормализация телефонов
def normalize_phone(phone_str):
    if not phone_str:
        return ''
    # Ищем номер и добавочный
    # Паттерн: возможный код (+7 или 8), затем 10 цифр с разделителями, и опционально добавочный
    pattern = r'(\+7|8)?\s*\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})(\s*\(?доб\.?\s*(\d+)\)?)?'
    match = re.search(pattern, phone_str)
    if match:
        code = match.group(1) if match.group(1) else '8'  # если нет кода, считаем 8
        # Если код 8, заменяем на +7
        if code == '8':
            code = '+7'
        elif code == '+7':
            pass
        else:
            # если что-то другое, приводим к +7 (но обычно только 8 или +7)
            code = '+7'
        part2 = match.group(2)
        part3 = match.group(3)
        part4 = match.group(4)
        part5 = match.group(5)
        ext = match.group(7) if match.group(7) else ''
        if ext:
            formatted = f'{code}({part2}){part3}-{part4}-{part5} доб.{ext}'
        else:
            formatted = f'{code}({part2}){part3}-{part4}-{part5}'
        return formatted
    # Если не удалось распарсить, возвращаем исходную строку (или пустую)
    return phone_str

# Обрабатываем все строки данных
processed_rows = []
for row in data_rows:
    row = normalize_names(row)
    # Телефон находится в индексе 5 (шестой столбец)
    if len(row) > 5:
        row[5] = normalize_phone(row[5])
    processed_rows.append(row)

# 3. Объединение дублей по (фамилия, имя)
contacts_dict = {}
for row in processed_rows:
    key = (row[0], row[1])  # lastname, firstname
    if key not in contacts_dict:
        contacts_dict[key] = row
    else:
        # Объединяем: если какое-то поле пустое, а в новой записи не пустое, заменяем
        existing = contacts_dict[key]
        for i in range(len(row)):
            if i == 0 or i == 1:  # Фамилию и имя не трогаем, они одинаковы
                continue
            if not existing[i] and row[i]:
                existing[i] = row[i]
        # При необходимости можно объединить телефон и email (если они разные, но по условию они должны быть одинаковыми)

# Преобразуем словарь обратно в список, начиная с заголовка
final_contacts = [header] + list(contacts_dict.values())

# Сохраняем результат
with open("phonebook.csv", "w", encoding="utf-8") as f:
    datawriter = csv.writer(f, delimiter=',')
    datawriter.writerows(final_contacts)

# Для проверки выведем результат
pprint(final_contacts)

import pytest
from phonebook_processor import normalize_names, normalize_phone

# -------------------------------------------------------------------
# 1. Тесты для normalize_names
# -------------------------------------------------------------------

@pytest.mark.parametrize("input_row, expected_row", [
    # Стандартное ФИО из трёх частей
    (["Иванов", "Иван", "Иванович", "доп"], ["Иванов", "Иван", "Иванович", "доп"]),
    # ФИО с лишними пробелами внутри
    ([" Петров ", "Петр", ""], ["Петров", "Петр", ""]),
    # Только фамилия и имя
    (["Сидоров", "Сидор"], ["Сидоров", "Сидор", ""]),
    # Только фамилия
    (["Кузнецов"], ["Кузнецов", "", ""]),
    # Пустая строка
    ([], ["", "", ""]),
    # ФИО с отчеством через дефис (не должно ломаться)
    (["Смирнов", "Анна-Мария", "Сергеевна"], ["Смирнов", "Анна-Мария", "Сергеевна"]),
])
def test_normalize_names(input_row, expected_row):
    """Параметризованный тест для нормализации ФИО."""
    result = normalize_names(input_row.copy())  # копируем, чтобы не менять оригинал
    assert result == expected_row


# -------------------------------------------------------------------
# 2. Тесты для normalize_phone
# -------------------------------------------------------------------

@pytest.mark.parametrize("input_phone, expected_phone", [
    # Формат с +7 и скобками
    ("+7(495)123-45-67", "+7(495)123-45-67"),
    # Формат с 8 и пробелами
    ("8 495 123 45 67", "+7(495)123-45-67"),
    # Формат без кода
    ("495-123-45-67", "+7(495)123-45-67"),
    # С добавочным номером (разные варианты)
    ("+7 495 123 45 67 доб. 1234", "+7(495)123-45-67 доб.1234"),
    ("8(495)123-45-67 доб.567", "+7(495)123-45-67 доб.567"),
    ("4951234567 доб. 987", "+7(495)123-45-67 доб.987"),
    # Нестандартные разделители
    ("+7 (495) 123-45-67", "+7(495)123-45-67"),
    ("8 495 1234567", "+7(495)123-45-67"),
    # Пустая строка
    ("", ""),
    # Некорректный номер – возвращается как есть
    ("не номер", "не номер"),
    ("+7(495)123-45-", "+7(495)123-45-"),  # не полный номер
])
def test_normalize_phone(input_phone, expected_phone):
    """Параметризованный тест для нормализации телефонов."""
    assert normalize_phone(input_phone) == expected_phone


# -------------------------------------------------------------------
# 3. Тесты для логики объединения дублей
# -------------------------------------------------------------------

def test_merge_duplicates():
    """
    Проверяем, что дублирующиеся записи объединяются корректно.
    Для этого эмулируем работу словаря contacts_dict.
    """
    # Исходные данные (после нормализации имён и телефонов)
    rows = [
        ["Иванов", "Иван", "Иванович", "", "+7(495)111-11-11", ""],
        ["Петров", "Петр", "", "Менеджер", "+7(495)222-22-22", "petr@mail.ru"],
        ["Иванов", "Иван", "", "Директор", "", "ivan@company.com"],  # дубль Иванова
        ["Сидоров", "Сидор", "Сидорович", "Инженер", "+7(495)333-33-33", "sidor@mail.ru"],
    ]

    # Ожидаемый результат после слияния:
    # Для Иванова должны объединиться: отчество из первой записи, должность и email из второй
    expected = {
        ("Иванов", "Иван"): ["Иванов", "Иван", "Иванович", "Директор", "+7(495)111-11-11", "ivan@company.com"],
        ("Петров", "Петр"): ["Петров", "Петр", "", "Менеджер", "+7(495)222-22-22", "petr@mail.ru"],
        ("Сидоров", "Сидор"): ["Сидоров", "Сидор", "Сидорович", "Инженер", "+7(495)333-33-33", "sidor@mail.ru"],
    }

    # Эмулируем объединение (как в основном коде)
    contacts_dict = {}
    for row in rows:
        key = (row[0], row[1])
        if key not in contacts_dict:
            contacts_dict[key] = row
        else:
            existing = contacts_dict[key]
            for i in range(len(row)):
                if i in (0, 1):  # фамилия и имя не трогаем
                    continue
                if not existing[i] and row[i]:
                    existing[i] = row[i]

    # Сравниваем результат с ожиданием
    assert contacts_dict == expected


# -------------------------------------------------------------------
# 4. (Дополнительно) Интеграционный тест на небольшом CSV-подобном списке
# -------------------------------------------------------------------

def test_full_pipeline():
    """
    Проверяем полный цикл обработки: нормализация + слияние.
    Используем фиктивный заголовок и строки.
    """
    header = ["lastname", "firstname", "surname", "organization", "phone", "email"]
    data = [
        ["Иванов", "Иван", "Иванович", "", "8(495)111-11-11", ""],
        ["Петров", "Петр", "", "ООО Ромашка", "+7 495 222-22-22", "petr@mail.ru"],
        ["Иванов", "Иван", "", "ЗАО Фиалка", "495 111-11-11 доб.123", "ivan@fialka.ru"],
        ["Сидоров", "Сидор", "Сидорович", "ИП Сидоров", "8-495-333-33-33", "sidor@mail.ru"],
    ]

    # Ожидаемый финальный результат (после всех преобразований)
    expected = [
        ["Иванов", "Иван", "Иванович", "ЗАО Фиалка", "+7(495)111-11-11 доб.123", "ivan@fialka.ru"],
        ["Петров", "Петр", "", "ООО Ромашка", "+7(495)222-22-22", "petr@mail.ru"],
        ["Сидоров", "Сидор", "Сидорович", "ИП Сидоров", "+7(495)333-33-33", "sidor@mail.ru"],
    ]

    # Выполняем обработку
    processed = []
    for row in data:
        row = normalize_names(row)
        if len(row) > 5:
            row[5] = normalize_phone(row[5])   # phone column index 5
        processed.append(row)

    # Слияние дублей
    contacts_dict = {}
    for row in processed:
        key = (row[0], row[1])
        if key not in contacts_dict:
            contacts_dict[key] = row
        else:
            existing = contacts_dict[key]
            for i in range(len(row)):
                if i in (0, 1):
                    continue
                if not existing[i] and row[i]:
                    existing[i] = row[i]

    final_contacts = [header] + list(contacts_dict.values())

    # Проверяем только данные (заголовок пропускаем)
    assert final_contacts[1:] == expected