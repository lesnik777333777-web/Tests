import re

def normalize_names(row):
    """
    Нормализует первые три поля строки (фамилия, имя, отчество).
    Возвращает изменённый список row.
    """
    full_name_parts = ' '.join(row[:3]).split()
    lastname = full_name_parts[0] if len(full_name_parts) > 0 else ''
    firstname = full_name_parts[1] if len(full_name_parts) > 1 else ''
    surname = full_name_parts[2] if len(full_name_parts) > 2 else ''
    row[0] = lastname
    row[1] = firstname
    row[2] = surname
    return row

def normalize_phone(phone_str):
    """
    Приводит телефон к формату +7(XXX)XXX-XX-XX [доб.XXXX].
    """
    if not phone_str:
        return ''
    pattern = r'(\+7|8)?\s*\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})(\s*\(?доб\.?\s*(\d+)\)?)?'
    match = re.search(pattern, phone_str)
    if match:
        code = match.group(1) if match.group(1) else '8'
        if code == '8':
            code = '+7'
        elif code != '+7':
            code = '+7'
        part2 = match.group(2)
        part3 = match.group(3)
        part4 = match.group(4)
        part5 = match.group(5)
        ext = match.group(7) if match.group(7) else ''
        if ext:
            return f'{code}({part2}){part3}-{part4}-{part5} доб.{ext}'
        else:
            return f'{code}({part2}){part3}-{part4}-{part5}'
    return phone_str