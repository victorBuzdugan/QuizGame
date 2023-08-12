import json
import os
import random
import shutil
import logging

import pytest
from quiz import add_question, list_questions, open_json, parse_args, save_json, delete_question
from pytest import MonkeyPatch, CaptureFixture, LogCaptureFixture

TEST_FILE = "questions_test.json"
VALID_QUESTION = [{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}]


def test_parse_args(capsys: CaptureFixture[str]):
    # no args display help (-h)
    with pytest.raises(SystemExit):
        args = parse_args()
    captured = capsys.readouterr()
    assert "usage: pytest [-h] {play,list,add,delete}" in captured.out
    assert "Play the game and optionally specify a level" in captured.out
    assert "List all the questions in the game" in captured.out
    assert "Add a question to the game" in captured.out
    assert "Delete a question from the game" in captured.out

    # wrong args
    with pytest.raises(SystemExit):
        args = parse_args(["wrong"])
    captured = capsys.readouterr()
    assert "usage: pytest [-h] {play,list,add,delete}" in captured.err
    assert "choose from 'play', 'list', 'add', 'delete'" in captured.err
    with pytest.raises(SystemExit):
        args = parse_args(["pla"])
    captured = capsys.readouterr()
    assert "usage: pytest [-h] {play,list,add,delete}" in captured.err
    assert "choose from 'play', 'list', 'add', 'delete'" in captured.err

    # arg: play
    args = parse_args(["play"])
    assert args.action == "play"
    assert args.level == 1
    with pytest.raises(AttributeError):
        args.question_no
    args = parse_args(["play", "-l", "2"])
    assert args.action == "play"
    assert args.level == 2
    with pytest.raises(AttributeError):
        args.question_no
    args = parse_args(["play", "--level", "3"])
    assert args.action == "play"
    assert args.level == 3
    with pytest.raises(AttributeError):
        args.question_no
    with pytest.raises(SystemExit):
        args = parse_args(["play", "-l", "4"])
    captured = capsys.readouterr()
    assert "usage: pytest play [-h] [-l {1,2,3}]" in captured.err
    assert "argument -l/--level: invalid choice" in captured.err
    with pytest.raises(SystemExit):
        args = parse_args(["play", "-l", "a"])
    captured = capsys.readouterr()
    assert "usage: pytest play [-h] [-l {1,2,3}]" in captured.err
    assert "invalid int value" in captured.err
    
    # arg: list
    args = parse_args(["list"])
    assert args.action == "list"
    with pytest.raises(AttributeError):
        args.question_no
    with pytest.raises(AttributeError):
        args.level
    
    # arg: add
    args = parse_args(["add"])
    assert args.action == "add"
    with pytest.raises(AttributeError):
        args.question_no
    with pytest.raises(AttributeError):
        args.level
    
    # arg: delete
    with pytest.raises(SystemExit):
        args = parse_args(["delete"])
    captured = capsys.readouterr()
    assert "usage: pytest delete [-h] question_no" in captured.err
    assert "the following arguments are required: question_no" in captured.err
    args = parse_args(["delete", "3"])
    assert args.action == "delete"
    assert args.question_no == 3
    with pytest.raises(AttributeError):
        args.level
    args = parse_args(["delete", "100"])
    assert args.action == "delete"
    assert args.question_no == 100
    with pytest.raises(AttributeError):
        args.level
    with pytest.raises(SystemExit):
        args = parse_args(["delete", "a"])
    assert "usage: pytest delete [-h] question_no" in captured.err
    assert "the following arguments are required: question_no" in captured.err


def test_open_json(capsys: CaptureFixture[str]):
    # file not found
    with pytest.raises(SystemExit):
        questions = open_json("")
        assert not questions
        assert "File '' not found" in capsys.readouterr().out
        assert "Quit because of fatal error" in capsys.readouterr().out
    
    # decode error
    shutil.copyfile("questions.json", TEST_FILE)
    with open(TEST_FILE, "a") as test_file:
        test_file.write("inccorect format")
    with pytest.raises(SystemExit):
        questions = open_json("")
        assert not questions
        assert f"File {TEST_FILE!r} is not a correct json file" in capsys.readouterr().out
        assert "Quit because of fatal error" in capsys.readouterr().out
    os.remove(TEST_FILE)


def test_open_json_validation_ok(capsys: CaptureFixture[str]):
    questions_data = VALID_QUESTION
    with open(TEST_FILE, "w") as json_file:
        json.dump(questions_data, json_file, indent=2)
    questions = open_json(TEST_FILE)
    assert questions_data[0] in questions
    os.remove(TEST_FILE)


@pytest.mark.parametrize(
    ("questions_data", ), (
    # empty name
    ([{"name": "", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # missing name
    ([{"answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # empty good answer
    ([{"name": "Question", "answ_good": "", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # missing good answer
    ([{"name": "Question", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # empty bad answer
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": []}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", ""]}], ),
    # missing bad answer
    ([{"name": "Question", "answ_good": "Good answer"}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4"]}], ),
    ))
def test_open_json_validation_error(capsys: CaptureFixture[str], questions_data):
    with open(TEST_FILE, "w") as json_file:
        json.dump(questions_data, json_file, indent=2)
    with pytest.raises(SystemExit):
        questions = open_json(TEST_FILE)
        assert not questions
        assert f"There is invalid data in {TEST_FILE!r}" in capsys.readouterr().out
        assert "Quit because of fatal error" in capsys.readouterr().out
    os.remove(TEST_FILE)


def test_save_json_validation_ok(capsys: CaptureFixture[str]):
    questions_data = VALID_QUESTION
    assert save_json(questions_data, TEST_FILE)
    assert "Element was not validated" not in capsys.readouterr().out
    assert "Quit because of fatal error" not in capsys.readouterr().out
    questions = open_json(TEST_FILE)
    assert questions_data[0] in questions
    os.remove(TEST_FILE)


@pytest.mark.parametrize(
    ("questions_data", ), (
    # empty name
    ([{"name": "", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # missing name
    ([{"answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # empty good answer
    ([{"name": "Question", "answ_good": "", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # missing good answer
    ([{"name": "Question", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    # empty bad answer
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": []}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", ""]}], ),
    # missing bad answer
    ([{"name": "Question", "answ_good": "Good answer"}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 4", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 5"]}], ),
    ([{"name": "Question", "answ_good": "Good answer", "answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4"]}], ),
    ))
def test_save_json_validation_error(capsys: CaptureFixture[str], questions_data):
    with pytest.raises(SystemExit):
        assert not save_json(questions_data, TEST_FILE) 
        assert "Element was not validated" in capsys.readouterr().out
        assert "Quit because of fatal error" in capsys.readouterr().out
        
        
def test_list_questions(capsys: CaptureFixture[str]):
    list_questions()
    captured = capsys.readouterr()
    questions = open_json()
    for _ in range(10):
        random_index = random.randint(0, len(questions) - 1)
        assert f"{random_index + 1} - {questions[random_index]['name']}" in captured.out


def test_add_question_1(capsys: CaptureFixture, monkeypatch: MonkeyPatch):
    question = VALID_QUESTION[0]
    [{"answ_bad": ["Bad answer 1", "Bad answer 2", "Bad answer 3", "Bad answer 4", "Bad answer 5"]}]
    responses = iter(
        [question["name"], question["answ_good"], question["answ_bad"][0], question["answ_bad"][1], question["answ_bad"][2], question["answ_bad"][3], question["answ_bad"][4], "yes"]
    )
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    add_question()
    captured = capsys.readouterr()
    assert "You need to provide:" in captured.out
    assert "Question added" in captured.out
    assert "That's the correct answer!" not in captured.out
    assert "Question not added... Try again" not in captured.out
    assert not captured.err
    
    questions = open_json()
    assert questions[-1] == question

    # teardown
    delete_question(len(questions))
    captured = capsys.readouterr()
    assert "Question was deleted" in captured.out
    assert "Question was not deleted" not in captured.out
    assert not captured.err


def test_add_question_2(capsys: CaptureFixture, monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    question = VALID_QUESTION[0]
    responses = iter(
        ["", question["name"], question["answ_good"], question["answ_good"], question["answ_bad"][0], question["answ_bad"][1], question["answ_bad"][2], question["answ_bad"][3], question["answ_bad"][4], "yes"]
    )
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    add_question()
    captured = capsys.readouterr()
    assert "You need to provide:" in captured.out
    assert "Allready added this answer!" in captured.out
    assert "Question added" in captured.out
    assert "That's the correct answer!" not in captured.out
    assert "Question not added... Try again" not in captured.out
    assert not captured.err
    assert "Empty value for: 'name'" in caplog.messages

    questions = open_json()
    assert questions[-1] == question

    # teardown
    delete_question(len(questions))
    captured = capsys.readouterr()
    assert "Question was deleted" in captured.out
    assert "Question was not deleted" not in captured.out
    assert not captured.err


def test_delete_question(capsys: CaptureFixture):
    with pytest.raises(SystemExit, match="Minimum question number is 1"):
        delete_question(0)
    with pytest.raises(SystemExit, match="Minimum question number is 1"):
        delete_question(-1)
    questions = open_json()
    with pytest.raises(SystemExit, match=f"Maximum question number is {len(questions)}"):
        delete_question(len(questions) + 1)

    



