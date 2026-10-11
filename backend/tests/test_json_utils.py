import pytest

from app.ai.json_utils import parse_quiz_json


GOOD = '{"questions":[{"question":"Q1?","options":["a","b","c","d"],"correct_index":1,"explanation":"e","difficulty":"easy","topic":"t","competency":"c","source_label":"S1"}]}'


def test_plain_json():
    q = parse_quiz_json(GOOD)
    assert len(q.questions) == 1
    assert q.questions[0].correct_index == 1


def test_fenced():
    q = parse_quiz_json("```json\n" + GOOD + "\n```")
    assert q.questions[0].question == "Q1?"


def test_trailing_text():
    q = parse_quiz_json(GOOD + "\nThanks!")
    assert q.questions[0].options[0] == "a"


def test_trailing_comma():
    messy = '{"questions":[{"question":"Q1?","options":["a","b","c","d"],"correct_index":0,"explanation":"e","difficulty":"medium","topic":"t","competency":"c","source_label":"S1",},],}'
    q = parse_quiz_json(messy)
    assert q.questions[0].difficulty == "medium"


def test_wrong_option_count():
    bad = '{"questions":[{"question":"Q","options":["a","b"],"correct_index":0,"explanation":"e","difficulty":"easy","topic":"t","competency":"c","source_label":"S1"}]}'
    with pytest.raises(Exception):
        parse_quiz_json(bad)


def test_bad_index():
    bad = '{"questions":[{"question":"Q","options":["a","b","c","d"],"correct_index":9,"explanation":"e","difficulty":"easy","topic":"t","competency":"c","source_label":"S1"}]}'
    with pytest.raises(Exception):
        parse_quiz_json(bad)


def test_duplicate_options():
    bad = '{"questions":[{"question":"Q","options":["a","a","c","d"],"correct_index":0,"explanation":"e","difficulty":"easy","topic":"t","competency":"c","source_label":"S1"}]}'
    with pytest.raises(Exception):
        parse_quiz_json(bad)
