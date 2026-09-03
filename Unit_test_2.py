import pytest
from phonebook_processor import normalize_names, normalize_phone

# -------------------------- Тесты normalize_names --------------------------
@pytest.mark.parametrize("input_row, expected_row", [
    (["Иванов", "Иван", "Иванович", "доп"], ["Иванов", "Иван", "Иванович", "доп"]),
    ([" Петров ", "Петр", ""], ["Петров", "Петр", ""]),
    (["Сидоров", "Сидор"], ["Сидоров", "Сидор", ""]),
    (["Кузнецов"], ["Кузнецов", "", ""]),
    ([], ["", "", ""]),
    (["Смирнов", "Анна-Мария", "Сергеевна"], ["Смирнов", "Анна-Мария", "Сергеевна"]),
])
def test_normalize_names(input_row, expected_row):
    result = normalize_names(input_row.copy())
    assert result == expected_row

# -------------------------- Тесты normalize_phone --------------------------
@pytest.mark.parametrize("input_phone, expected_phone", [
    ("+7(495)123-45-67", "+7(495)123-45-67"),
    ("8 495 123 45 67", "+7(495)123-45-67"),
    ("495-123-45-67", "+7(495)123-45-67"),
    ("+7 495 123 45 67 доб. 1234", "+7(495)123-45-67 доб.1234"),
    ("8(495)123-45-67 доб.567", "+7(495)123-45-67 доб.567"),
    ("4951234567 доб. 987", "+7(495)123-45-67 доб.987"),
    ("+7 (495) 123-45-67", "+7(495)123-45-67"),
    ("8 495 1234567", "+7(495)123-45-67"),
    ("", ""),
    ("не номер", "не номер"),
    ("+7(495)123-45-", "+7(495)123-45-"),
])
def test_normalize_phone(input_phone, expected_phone):
    assert normalize_phone(input_phone) == expected_phone

# -------------------------- Тест слияния дублей --------------------------
def test_merge_duplicates():
    rows = [
        ["Иванов", "Иван", "Иванович", "", "+7(495)111-11-11", ""],
        ["Петров", "Петр", "", "Менеджер", "+7(495)222-22-22", "petr@mail.ru"],
        ["Иванов", "Иван", "", "Директор", "", "ivan@company.com"],
        ["Сидоров", "Сидор", "Сидорович", "Инженер", "+7(495)333-33-33", "sidor@mail.ru"],
    ]
    expected = {
        ("Иванов", "Иван"): ["Иванов", "Иван", "Иванович", "Директор", "+7(495)111-11-11", "ivan@company.com"],
        ("Петров", "Петр"): ["Петров", "Петр", "", "Менеджер", "+7(495)222-22-22", "petr@mail.ru"],
        ("Сидоров", "Сидор"): ["Сидоров", "Сидор", "Сидорович", "Инженер", "+7(495)333-33-33", "sidor@mail.ru"],
    }
    contacts_dict = {}
    for row in rows:
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
    assert contacts_dict == expected

# -------------------------- Интеграционный тест --------------------------
def test_full_pipeline():
    header = ["lastname", "firstname", "surname", "organization", "phone", "email"]
    data = [
        ["Иванов", "Иван", "Иванович", "", "8(495)111-11-11", ""],
        ["Петров", "Петр", "", "ООО Ромашка", "+7 495 222-22-22", "petr@mail.ru"],
        ["Иванов", "Иван", "", "ЗАО Фиалка", "495 111-11-11 доб.123", "ivan@fialka.ru"],
        ["Сидоров", "Сидор", "Сидорович", "ИП Сидоров", "8-495-333-33-33", "sidor@mail.ru"],
    ]
    expected = [
        ["Иванов", "Иван", "Иванович", "ЗАО Фиалка", "+7(495)111-11-11 доб.123", "ivan@fialka.ru"],
        ["Петров", "Петр", "", "ООО Ромашка", "+7(495)222-22-22", "petr@mail.ru"],
        ["Сидоров", "Сидор", "Сидорович", "ИП Сидоров", "+7(495)333-33-33", "sidor@mail.ru"],
    ]
    processed = []
    for row in data:
        row = normalize_names(row)
        if len(row) > 5:
            row[5] = normalize_phone(row[5])
        processed.append(row)

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
    assert final_contacts[1:] == expected