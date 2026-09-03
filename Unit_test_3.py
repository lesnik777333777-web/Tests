import pytest
import sqlite3
import random
from database import Database

# -------------------------- Фикстура с временной БД --------------------------
@pytest.fixture
def db():
    import tempfile
    import os
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    db_path = temp_db.name
    instance = Database(db_path)

    # Заполним тестовыми данными
    cursor = instance.conn.cursor()
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
    instance.conn.commit()

    yield instance

    instance.close()
    os.unlink(db_path)

# -------------------------- Тесты методов Database --------------------------
def test_get_or_create_user_existing(db):
    user = db.get_or_create_user('alice')
    assert user['user_id'] == 1
    assert user['username'] == 'alice'

def test_get_or_create_user_new(db):
    user = db.get_or_create_user('charlie')
    assert user['user_id'] == 3
    assert user['username'] == 'charlie'

def test_add_user_word_success(db):
    result = db.add_user_word(1, 'house', 'дом')
    assert result is True
    words = db.get_user_words(1)
    assert any(w['english_word'] == 'house' and w['russian_word'] == 'дом' for w in words)

def test_add_user_word_duplicate(db):
    db.add_user_word(1, 'tree', 'дерево')
    result = db.add_user_word(1, 'tree', 'дерево')
    assert result is False

def test_get_user_words(db):
    db.add_user_word(1, 'sun', 'солнце')
    db.add_user_word(1, 'moon', 'луна')
    words = db.get_user_words(1)
    assert len(words) >= 2
    assert {'sun', 'moon'}.issubset({w['english_word'] for w in words})

def test_delete_user_word(db):
    db.add_user_word(1, 'star', 'звезда')
    words_before = db.get_user_words(1)
    word_id = next(w['userwords_id'] for w in words_before if w['english_word'] == 'star')
    db.delete_user_word(1, word_id)
    words_after = db.get_user_words(1)
    assert not any(w['english_word'] == 'star' for w in words_after)

def test_get_common_words(db):
    common = db.get_common_words()
    assert len(common) == 5
    assert common[0]['english_word'] == 'apple'

def test_update_stats_correct(db):
    db.update_stats(1, True)
    stats = db.get_stats(1)
    assert stats['correct'] == 6
    assert stats['total'] == 11

def test_update_stats_wrong(db):
    db.update_stats(1, False)
    stats = db.get_stats(1)
    assert stats['correct'] == 5
    assert stats['total'] == 11

def test_get_stats(db):
    stats = db.get_stats(1)
    assert stats['correct'] == 5
    assert stats['total'] == 10

def test_get_all_tables(db):
    tables = db.get_all_tables()
    assert isinstance(tables, list)
    assert 'users' in tables

def test_get_table_schema(db):
    schema = db.get_table_schema('users')
    assert isinstance(schema, list)
    column_names = [row[1] for row in schema]
    assert 'user_id' in column_names and 'username' in column_names

# -------------------------- Тесты логики генерации вопроса --------------------------
def generate_question(words):
    if len(words) < 4:
        return None
    correct = random.choice(words)
    others = [w for w in words if w != correct]
    random.shuffle(others)
    options = [correct] + others[:3]
    random.shuffle(options)
    return {'correct': correct, 'options': options}

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
    question = generate_question(sample_words)
    assert question is not None
    assert len(question['options']) == 4
    assert question['correct'] in question['options']

def test_generate_question_too_few_words():
    words = [{'words_id': 1, 'english_word': 'apple', 'russian_word': 'яблоко'}]
    assert generate_question(words) is None

def test_generate_question_all_options_unique(sample_words):
    question = generate_question(sample_words)
    english_options = [opt['english_word'] for opt in question['options']]
    assert len(english_options) == len(set(english_options))

# -------------------------- Тесты валидации --------------------------
def test_validate_input():
    def is_valid(english, russian):
        return bool(english.strip()) and bool(russian.strip())
    assert is_valid('apple', 'яблоко') is True
    assert is_valid(' ', 'яблоко') is False
    assert is_valid('apple', '') is False
    assert is_valid('', '') is False

def test_normalize_input():
    def normalize(english, russian):
        return english.strip(), russian.strip()
    eng, rus = normalize('  apple  ', '  яблоко  ')
    assert eng == 'apple'
    assert rus == 'яблоко'