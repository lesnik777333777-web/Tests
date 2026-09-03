import streamlit as st
import database
import random

# ===========================
# 1. НАСТРОЙКА СТРАНИЦЫ
# ===========================
st.set_page_config(
    page_title="LinguaForge - программа для изучения английского языка",
    page_icon="📚",
    layout="wide"
)

# ===========================
# 2. ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ===========================
db = database.Database()

# ===========================
# 3. САЙДБАР (Вход / Выход)
# ===========================
with st.sidebar:
    st.header("🔐 Вход")

    if "user_id" in st.session_state:
        st.success(f"Вы вошли как: {st.session_state.username}")
        if st.button("🚪 Выйти"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        username = st.text_input("Введите Ваше имя: ")
        login_button = st.button("Войти")

        if login_button:
            if not username.strip():
                st.warning("Имя не может быть пустым!")
            else:
                user = db.get_or_create_user(username)
                st.session_state.user_id = user["user_id"]
                st.session_state.username = user["username"]
                st.success("Добро пожаловать!")
                st.rerun()

# ===========================
# 4. ЗАГОЛОВОК И ПРИВЕТСТВИЕ
# ===========================
st.title("LinguaForge")
st.markdown("""
Привет 👋 Давай попрактикуемся в английском языке.
Тренировки можешь проходить в удобном для себя темпе.

У тебя есть возможность использовать тренажёр как конструктор
и собирать свою собственную базу для обучения.

Инструменты:
- добавить слово ➕
- удалить слово 🗑️

Ну что, начнём ⬇️
""")

# ===========================
# ОСНОВНОЙ КОНТЕНТ (только для вошедших)
# ===========================
if "user_id" in st.session_state:
    st.subheader(f"Привет, {st.session_state.username}! 👋")

    # ---------- БЛОК ДОБАВЛЕНИЯ СЛОВА ----------
    st.divider()
    with st.form("add_word_form"):
        st.subheader("➕ Добавить своё слово")
        english = st.text_input("Слово на английском:")
        russian = st.text_input("Перевод на русском:")
        submitted = st.form_submit_button("Добавить")

    if submitted:
        if not english.strip() or not russian.strip():
            st.warning("⚠️ Оба поля должны быть заполнены!")
        else:
            success = db.add_user_word(
                st.session_state.user_id,
                english.strip(),
                russian.strip()
            )
            if success:
                st.success(f"✅ Слово '{english}' добавлено!")
                st.rerun()
            else:
                st.error("❌ Такое слово уже есть в твоём словаре!")

    # Счётчик слов
    common_words = db.get_common_words()
    user_words = db.get_user_words(st.session_state.user_id)
    total_words = len(common_words) + len(user_words)
    st.info(f"📚 Ты изучаешь **{total_words}** слов (общих: {len(common_words)}, личных: {len(user_words)})")

    # ---------- БЛОК УДАЛЕНИЯ ЛИЧНЫХ СЛОВ ----------
    if user_words:
        st.subheader("📝 Твои личные слова")
        for word in user_words:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{word['english_word']}** — {word['russian_word']}")
            with col2:
                if st.button("🗑️ Удалить", key=f"del_{word['userwords_id']}"):
                    db.delete_user_word(st.session_state.user_id, word['userwords_id'])
                    st.success(f"Слово '{word['english_word']}' удалено!")
                    st.rerun()
    else:
        st.info("У тебя пока нет личных слов. Добавь первое слово выше! ☝️")

    # ---------- 📈 ЭТАП 7: СТАТИСТИКА ----------
    st.divider()
    st.subheader("📈 Твоя статистика")
    stats = db.get_stats(st.session_state.user_id)

    col1, col2, col3 = st.columns(3)
    col1.metric(label="✅ Правильных ответов", value=stats['correct'])
    col2.metric(label="🎯 Всего попыток", value=stats['total'])

    if stats['total'] > 0:
        accuracy = (stats['correct'] / stats['total']) * 100
        col3.metric(label="📊 Точность", value=f"{accuracy:.1f}%")
    else:
        col3.metric(label="📊 Точность", value="0.0%")

    # ---------- 🏋️ ТРЕНИРОВКА ----------
    st.divider()
    st.subheader("🏋️ Тренировка")

    # 1. Показываем результат прошлого ответа
    if "feedback" in st.session_state:
        if st.session_state.feedback == "correct":
            st.success("✅ Правильно! Отличная работа!")
        else:
            st.error("❌ Неправильно, попробуй ещё раз!")
        del st.session_state.feedback

    # 2. Генерируем вопрос, если его нет
    if "current_question" not in st.session_state:
        words = db.get_common_words()
        if len(words) >= 4:
            correct_word = random.choice(words)
            wrong_words = [w for w in words if w['words_id'] != correct_word['words_id']]
            random.shuffle(wrong_words)
            options = [correct_word] + wrong_words[:3]
            random.shuffle(options)
            st.session_state.current_question = {
                "correct": correct_word,
                "options": options
            }
        else:
            st.warning("Для тренировки нужно минимум 4 слова в базе!")

    # 3. Отрисовываем вопрос и кнопки
    if "current_question" in st.session_state:
        question = st.session_state.current_question
        st.markdown(f"### Переведите слово: **{question['correct']['russian_word'].upper()}**")

        options = question['options']

        def check_answer(option):
            is_correct = option['english_word'] == question['correct']['english_word']
            # ★ ЭТАП 7: обновляем статистику после каждого ответа
            db.update_stats(st.session_state.user_id, is_correct)
            if is_correct:
                st.session_state.feedback = "correct"
                del st.session_state.current_question
            else:
                st.session_state.feedback = "wrong"
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.button(options[0]['english_word'], key="btn_0", use_container_width=True):
                check_answer(options[0])
            if st.button(options[2]['english_word'], key="btn_2", use_container_width=True):
                check_answer(options[2])
        with col2:
            if st.button(options[1]['english_word'], key="btn_1", use_container_width=True):
                check_answer(options[1])
            if st.button(options[3]['english_word'], key="btn_3", use_container_width=True):
                check_answer(options[3])

    # ---------- 🗄️ ЭТАП 8: СХЕМА БАЗЫ ДАННЫХ ----------
    st.divider()
    st.subheader("🗄️ Схема базы данных")
    st.caption("Здесь показана структура всех таблиц в базе данных приложения.")

    tables = db.get_all_tables()
    for table in tables:
        st.markdown(f"#### 📋 Таблица: `{table}`")
        schema = db.get_table_schema(table)
        st.dataframe(schema, use_container_width=True, hide_index=True)

    # ---------- СПИСОК ОБЩИХ СЛОВ ----------
    st.divider()
    st.subheader(f"📊 Всего слов в общей базе: {len(common_words)}")
    if common_words:
        st.write("Список всех общих слов:")
        st.table(common_words)
    else:
        st.info("В базе пока нет слов.")

else:
    st.info("👉 Пожалуйста, представьтесь в боковой панели, чтобы начать.")

db.close()

import pytest
import sqlite3
from database import Database  # предполагается, что класс лежит в database.py
import random

# -------------------------------------------------------------------
# 1. ФИКСТУРА ДЛЯ ТЕСТОВОЙ БАЗЫ ДАННЫХ (in-memory)
# -------------------------------------------------------------------

@pytest.fixture
def db():
    """Создаёт экземпляр Database с временной БД в памяти."""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE common_words (
            words_id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_word TEXT UNIQUE NOT NULL,
            russian_word TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE user_words (
            userwords_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            english_word TEXT NOT NULL,
            russian_word TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, english_word)
        )
    ''')
    cursor.execute('''
        CREATE TABLE user_stats (
            user_id INTEGER PRIMARY KEY,
            correct INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()

    db_instance = Database(connection=conn)


    import tempfile
    import os
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    db_instance = Database(db_path)  # ваш конструктор

    # Заполняем начальными данными для тестов
    cursor = db_instance.conn.cursor()
    # Добавим несколько общих слов
    cursor.executemany('''
        INSERT INTO common_words (english_word, russian_word)
        VALUES (?, ?)
    ''', [
        ('apple', 'яблоко'),
        ('cat', 'кот'),
        ('dog', 'собака'),
        ('book', 'книга'),
        ('car', 'машина')
    ])
    cursor.executemany('''
        INSERT INTO users (username) VALUES (?)
    ''', [('alice',), ('bob',)])
    cursor.executemany('''
        INSERT INTO user_stats (user_id, correct, total)
        VALUES (?, ?, ?)
    ''', [(1, 5, 10), (2, 3, 4)])
    conn.commit()

    yield db_instance

    # Чистка после тестов
    db_instance.close()
    os.unlink(db_path)


# -------------------------------------------------------------------
# 2. ТЕСТЫ ДЛЯ DATABASE (CRUD + СТАТИСТИКА)
# -------------------------------------------------------------------

def test_get_or_create_user_existing(db):
    """Получение существующего пользователя."""
    user = db.get_or_create_user('alice')
    assert user['user_id'] == 1
    assert user['username'] == 'alice'

def test_get_or_create_user_new(db):
    """Создание нового пользователя."""
    user = db.get_or_create_user('charlie')
    assert user['user_id'] == 3
    assert user['username'] == 'charlie'

def test_add_user_word_success(db):
    """Успешное добавление личного слова."""
    result = db.add_user_word(1, 'house', 'дом')
    assert result is True
    words = db.get_user_words(1)
    assert any(w['english_word'] == 'house' and w['russian_word'] == 'дом' for w in words)

def test_add_user_word_duplicate(db):
    """Попытка добавить дубликат слова для того же пользователя."""
    db.add_user_word(1, 'tree', 'дерево')
    result = db.add_user_word(1, 'tree', 'дерево')
    assert result is False

def test_get_user_words(db):
    """Получение списка личных слов пользователя."""
    db.add_user_word(1, 'sun', 'солнце')
    db.add_user_word(1, 'moon', 'луна')
    words = db.get_user_words(1)
    assert len(words) >= 2
    assert {'sun', 'moon'}.issubset({w['english_word'] for w in words})

def test_delete_user_word(db):
    """Удаление личного слова."""
    db.add_user_word(1, 'star', 'звезда')
    words_before = db.get_user_words(1)
    word_id = next(w['userwords_id'] for w in words_before if w['english_word'] == 'star')
    db.delete_user_word(1, word_id)
    words_after = db.get_user_words(1)
    assert not any(w['english_word'] == 'star' for w in words_after)

def test_get_common_words(db):
    """Получение списка общих слов."""
    common = db.get_common_words()
    assert len(common) == 5
    assert common[0]['english_word'] == 'apple'

def test_update_stats_correct(db):
    """Обновление статистики при правильном ответе."""
    db.update_stats(1, True)
    stats = db.get_stats(1)
    assert stats['correct'] == 6
    assert stats['total'] == 11

def test_update_stats_wrong(db):
    """Обновление статистики при неправильном ответе."""
    db.update_stats(1, False)
    stats = db.get_stats(1)
    assert stats['correct'] == 5
    assert stats['total'] == 11

def test_get_stats(db):
    """Получение статистики пользователя."""
    stats = db.get_stats(1)
    assert stats['correct'] == 5
    assert stats['total'] == 10

def test_get_all_tables(db):
    """Получение списка всех таблиц (проверяем, что метод существует и возвращает список)."""
    tables = db.get_all_tables()
    assert isinstance(tables, list)
    # Ожидаем, что есть хотя бы users, common_words, user_words, user_stats
    assert 'users' in tables

def test_get_table_schema(db):
    """Получение схемы таблицы."""
    schema = db.get_table_schema('users')
    assert isinstance(schema, list)  # или DataFrame
    # Проверяем, что есть колонки
    column_names = [row[1] for row in schema] if isinstance(schema, list) else schema.columns.tolist()
    assert 'user_id' in column_names and 'username' in column_names


# -------------------------------------------------------------------
# 3. ТЕСТЫ ЛОГИКИ ГЕНЕРАЦИИ ВОПРОСА (ВЫНЕСЕНО В ОТДЕЛЬНУЮ ФУНКЦИЮ)
# -------------------------------------------------------------------

def generate_question(words):
    """
    Вспомогательная функция, которая имитирует генерацию вопроса.
    Возвращает словарь с правильным словом и 4 вариантами (включая правильный).
    """
    if len(words) < 4:
        return None
    correct = random.choice(words)
    others = [w for w in words if w != correct]
    random.shuffle(others)
    options = [correct] + others[:3]
    random.shuffle(options)
    return {
        'correct': correct,
        'options': options
    }

# Тесты для этой функции
@pytest.fixture
def sample_words():
    return [
        {'words_id': 1, 'english_word': 'apple', 'russian_word': 'яблоко'},
        {'words_id': 2, 'english_word': 'cat', 'russian_word': 'кот'},
        {'words_id': 3, 'english_word': 'dog', 'russian_word': 'собака'},
        {'words_id': 4, 'english_word': 'book', 'russian_word': 'книга'},
        {'words_id': 5, 'english_word': 'car', 'russian_word': 'машина'},
    ]

def test_generate_question_success(sample_words):
    """Проверка, что генерируется вопрос с 4 вариантами."""
    question = generate_question(sample_words)
    assert question is not None
    assert len(question['options']) == 4
    assert question['correct'] in question['options']

def test_generate_question_too_few_words():
    """При недостатке слов возвращается None."""
    words = [{'words_id': 1, 'english_word': 'apple', 'russian_word': 'яблоко'}]
    assert generate_question(words) is None

def test_generate_question_all_options_unique(sample_words):
    """Все варианты должны быть уникальными."""
    question = generate_question(sample_words)
    english_options = [opt['english_word'] for opt in question['options']]
    assert len(english_options) == len(set(english_options))

# Проверка ответа (сравнение с правильным)
def test_check_answer_correct(sample_words):
    question = generate_question(sample_words)
    correct = question['correct']
    # Проверяем, что при выборе правильного варианта возвращается True
    assert correct['english_word'] == question['correct']['english_word']  # всегда True
    # Мы можем написать отдельную функцию check_answer, которая принимает выбранный вариант и правильный
    def check_answer(selected, correct):
        return selected == correct['english_word']
    # Проверяем
    for opt in question['options']:
        if opt == correct:
            assert check_answer(opt['english_word'], correct) is True
        else:
            assert check_answer(opt['english_word'], correct) is False


# -------------------------------------------------------------------
# 4. ТЕСТЫ ВАЛИДАЦИИ ВВОДА
# -------------------------------------------------------------------

def test_validate_input():
    """Проверка, что пустые строки не проходят валидацию."""
    def is_valid(english, russian):
        return bool(english.strip()) and bool(russian.strip())
    assert is_valid('apple', 'яблоко') is True
    assert is_valid(' ', 'яблоко') is False
    assert is_valid('apple', '') is False
    assert is_valid('', '') is False

def test_normalize_input():
    """Проверка обрезки пробелов."""
    def normalize(english, russian):
        return english.strip(), russian.strip()
    eng, rus = normalize('  apple  ', '  яблоко  ')
    assert eng == 'apple'
    assert rus == 'яблоко'