import pytest

# -------------------------------------------------------------------
# Моё ДЗ "Менторы"
# -------------------------------------------------------------------

class Student:
    def __init__(self, name, surname, gender):
        self.name = name
        self.surname = surname
        self.gender = gender
        self.finished_courses = []
        self.courses_in_progress = []
        self.grades = {}

class Mentor:
    def __init__(self, name, surname):
        self.name = name
        self.surname = surname
        self.courses_attached = []

    def rate_hw(self, student, course, grade):
        if isinstance(student, Student) and course in self.courses_attached and course in student.courses_in_progress:
            if course in student.grades:
                student.grades[course] += [grade]
            else:
                student.grades[course] = [grade]
            # возвращаем True для успешного завершения (удобно для тестов)
            return True
        else:
            return 'Ошибка'

# -------------------------------------------------------------------
# Тесты (3 группы)
# -------------------------------------------------------------------

# Фикстуры для создания объектов с предустановленными курсами
@pytest.fixture
def student_python():
    s = Student('Ruoy', 'Eman', 'male')
    s.courses_in_progress.append('Python')
    return s

@pytest.fixture
def student_java():
    s = Student('Ada', 'Lovelace', 'female')
    s.courses_in_progress.append('Java')
    return s

@pytest.fixture
def mentor_python():
    m = Mentor('Some', 'Buddy')
    m.courses_attached.append('Python')
    return m

@pytest.fixture
def mentor_empty():
    return Mentor('No', 'Courses')


# -------------------- 1. Тесты инициализации --------------------
def test_student_initialization():
    """Проверка корректного создания объекта Student."""
    s = Student('John', 'Doe', 'male')
    assert s.name == 'John'
    assert s.surname == 'Doe'
    assert s.gender == 'male'
    assert s.finished_courses == []
    assert s.courses_in_progress == []
    assert s.grades == {}

def test_mentor_initialization():
    """Проверка корректного создания объекта Mentor."""
    m = Mentor('Jane', 'Smith')
    assert m.name == 'Jane'
    assert m.surname == 'Smith'
    assert m.courses_attached == []


# -------------------- 2. Тесты успешного выставления оценки --------------------
@pytest.mark.parametrize("grades_to_add, expected", [
    ([5], [5]),
    ([8, 9], [8, 9]),
    ([10, 10, 10], [10, 10, 10]),
])
def test_rate_hw_success(student_python, mentor_python, grades_to_add, expected):
    """Параметризованный тест: успешное добавление одной или нескольких оценок."""
    for g in grades_to_add:
        mentor_python.rate_hw(student_python, 'Python', g)
    assert student_python.grades['Python'] == expected

def test_rate_hw_append_to_existing_course(student_python, mentor_python):
    """Проверка, что оценки добавляются в существующий список."""
    mentor_python.rate_hw(student_python, 'Python', 7)
    mentor_python.rate_hw(student_python, 'Python', 8)
    assert student_python.grades['Python'] == [7, 8]

def test_rate_hw_return_value_success(student_python, mentor_python):
    """Проверка, что метод возвращает True при успехе."""
    result = mentor_python.rate_hw(student_python, 'Python', 10)
    assert result is True


# -------------------- 3. Тесты ошибочных ситуаций --------------------
@pytest.mark.parametrize("student, mentor, course, grade, expected_return, expected_grades", [
    # случай 1: студент не имеет нужного курса
    (Student('No', 'Course', 'm'), mentor_python, 'Python', 9, 'Ошибка', {}),
    # случай 2: ментор не прикреплён к курсу
    (student_python, mentor_empty, 'Python', 9, 'Ошибка', {}),
    # случай 3: передан не объект Student (например, строка)
    ('not a student', mentor_python, 'Python', 9, 'Ошибка', {}),
])
def test_rate_hw_errors(student, mentor, course, grade, expected_return, expected_grades, request):
    """
    Параметризованный тест всех ошибочных сценариев.
    Проверяется возвращаемое значение и отсутствие изменений в grades.
    """
    # Для случая с реальным студентом сохраняем его grades до вызова
    if isinstance(student, Student):
        original_grades = student.grades.copy()
    else:
        original_grades = {}

    result = mentor.rate_hw(student, course, grade)

    assert result == expected_return
    if isinstance(student, Student):
        assert student.grades == original_grades  # ничего не добавилось
    else:
        # для не-студента проверяем, что ничего не сломалось
        pass

# Дополнительный тест: курс студента есть, но ментор не привязан — ошибка
def test_rate_hw_mentor_not_attached(student_python, mentor_empty):
    result = mentor_empty.rate_hw(student_python, 'Python', 5)
    assert result == 'Ошибка'
    assert student_python.grades == {}

# Дополнительный тест: студент имеет курс, ментор привязан — успех
def test_rate_hw_full_success(student_python, mentor_python):
    result = mentor_python.rate_hw(student_python, 'Python', 10)
    assert result is True
    assert student_python.grades['Python'] == [10]