import json
import logging
import os
import random
import shutil

import pytest
from pytest import CaptureFixture, LogCaptureFixture, MonkeyPatch

from project import (add_question, delete_question, list_questions, open_json,
                  parse_args, play_game, save_json)

TEST_FILE = "questions_test.json"
VALID_QUESTION = [
    {"name": "Question",
     "answ_good": "Good answer",
     "answ_bad": [
         "Bad answer 1",
         "Bad answer 2",
         "Bad answer 3",
         "Bad answer 4",
         "Bad answer 5"
         ]}
]


def test_parse_args(capsys: CaptureFixture[str]):
    # args display help (-h)
    with pytest.raises(SystemExit):
        args = parse_args(["-h"])
    captured = capsys.readouterr()
    assert "usage: pytest [-h] {play,list,add,delete}" in captured.out
    assert "Play the game and optionally specify a level" in captured.out
    assert "List all the questions in the game" in captured.out
    assert "Add a question to the game" in captured.out
    assert "Delete a question from the game" in captured.out
    with pytest.raises(SystemExit):
        args = parse_args(["--help"])
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

    # arg: play or no args
    args = parse_args()
    assert args.action == "play"
    assert args.level == 1
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
    with open(TEST_FILE, "a", encoding="UTF-8") as test_file:
        test_file.write("inccorect format")
    with pytest.raises(SystemExit):
        questions = open_json("")
        assert not questions
        assert (f"File {TEST_FILE!r} is not a correct json file"
                in capsys.readouterr().out)
        assert "Quit because of fatal error" in capsys.readouterr().out
    os.remove(TEST_FILE)


def test_open_json_validation_ok():
    questions_data = VALID_QUESTION
    with open(TEST_FILE, "w", encoding="UTF-8") as json_file:
        json.dump(questions_data, json_file, indent=2)
    questions = open_json(TEST_FILE)
    assert questions_data[0] in questions
    os.remove(TEST_FILE)


@pytest.mark.parametrize(
    ("questions_data", ), (
    # empty name
    ([{"name": "",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # missing name
    ([{"answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # empty good answer
    ([{"name": "Question",
       "answ_good": "",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # missing good answer
    ([{"name": "Question",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # empty bad answer
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": []
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           ""
           ]
    }], ),
    # missing bad answer
    ([{"name": "Question",
       "answ_good": "Good answer"
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ))
def test_open_json_validation_error(
        capsys: CaptureFixture[str],
        questions_data):
    with open(TEST_FILE, "w", encoding="UTF-8") as json_file:
        json.dump(questions_data, json_file, indent=2)
    with pytest.raises(SystemExit):
        questions = open_json(TEST_FILE)
        assert not questions
        assert (f"There is invalid data in {TEST_FILE!r}"
                in capsys.readouterr().out)
        assert "Quit because of fatal error" in capsys.readouterr().out
    os.remove(TEST_FILE)


def test_save_json(capsys: CaptureFixture[str]):
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
    ([{"name": "",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # missing name
    ([{"answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # empty good answer
    ([{"name": "Question",
       "answ_good": "",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # missing good answer
    ([{"name": "Question",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    # empty bad answer
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": []
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "",
           "Bad answer 5"
           ]
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 1",
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           ""
           ]
    }], ),
    # missing bad answer
    ([{"name": "Question",
       "answ_good": "Good answer"
    }], ),
    ([{"name": "Question",
       "answ_good": "Good answer",
       "answ_bad": [
           "Bad answer 2",
           "Bad answer 3",
           "Bad answer 4",
           "Bad answer 5"
           ]
    }], ),
    ))
def test_save_json_validation_error(
        capsys: CaptureFixture[str],
        questions_data):
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
        assert (f"{random_index + 1} - {questions[random_index]['name']}"
                in captured.out)


def test_add_question(capsys: CaptureFixture, monkeypatch: MonkeyPatch):
    question = VALID_QUESTION[0]
    responses = iter([
        question["name"],
        question["answ_good"],
        question["answ_bad"][0],
        question["answ_bad"][1],
        question["answ_bad"][2],
        question["answ_bad"][3],
        question["answ_bad"][4],
        "yes"
    ])
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


def test_add_question_with_one_retry(
        capsys: CaptureFixture,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    question = VALID_QUESTION[0]
    responses = iter([
        "",
        question["name"],
        question["answ_good"],
        question["answ_good"],
        question["answ_bad"][0],
        question["answ_bad"][1],
        question["answ_bad"][2],
        question["answ_bad"][3],
        question["answ_bad"][4],
        "yes"
    ])
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


def test_delete_question():
    with pytest.raises(SystemExit, match="Minimum question number is 1"):
        delete_question(0)
    with pytest.raises(SystemExit, match="Minimum question number is 1"):
        delete_question(-1)
    questions = open_json()
    with pytest.raises(
            SystemExit,
            match=f"Maximum question number is {len(questions)}"):
        delete_question(len(questions) + 1)


def test_play_game_score_0(
        capsys: CaptureFixture,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    questions = open_json()

    def incorrect_answ(_):
        correct_answ = caplog.record_tuples[-1][-1]
        if correct_answ == "1":
            return "2"
        return str(int(correct_answ) - 1)

    monkeypatch.setattr('builtins.input', incorrect_answ)
    play_game(1)
    captured = capsys.readouterr()
    assert "Start game with level: 1" in caplog.messages
    assert "Score: 0" in caplog.messages
    assert "Score: 1" not in caplog.messages
    assert "Question 10/10" in captured.out
    assert "✅ Good job!" not in captured.out
    assert "❗️ Sorry, the correct answer was " in captured.out
    assert "Final score: 0" in captured.out
    assert "Difficulty level: 1/3" in captured.out
    assert "Are you even trying?" in captured.out
    assert not captured.err
    for log_record in caplog.records:
        if log_record.lineno == 111:
            question_name = log_record.message
            for question in questions:
                if question["name"] == question_name:
                    assert question["answ_good"] in captured.out
                    for bad_answ in question["answ_bad"][:2]:
                        assert bad_answ in captured.out
                    break


def test_play_game(
        capsys: CaptureFixture,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)
    questions = open_json()

    monkeypatch.setattr(
        'builtins.input',
        lambda _: caplog.record_tuples[-1][-1])
    play_game(3)
    captured = capsys.readouterr()
    assert "Start game with level: 3" in caplog.messages
    assert "Score: 10" in caplog.messages
    assert "Question 10/10" in captured.out
    assert "✅ Good job!" in captured.out
    assert "❗️ Sorry, the correct answer was " not in captured.out
    assert "Final score: 10" in captured.out
    assert "Difficulty level: 3/3" in captured.out
    assert "Perfect game!!!" in captured.out
    assert not captured.err
    for log_record in caplog.records:
        if log_record.lineno == 111:
            question_name = log_record.message
            for question in questions:
                if question["name"] == question_name:
                    assert question["answ_good"] in captured.out
                    for bad_answ in question["answ_bad"][2:]:
                        assert bad_answ in captured.out
                    break


def test_play_game_quit(
        capsys: CaptureFixture,
        monkeypatch: MonkeyPatch,
        caplog: LogCaptureFixture):
    caplog.set_level(logging.DEBUG)

    monkeypatch.setattr('builtins.input', lambda _: "quit")
    with pytest.raises(SystemExit, match="Game ended"):
        play_game(2)
    captured = capsys.readouterr()
    assert "Start game with level: 2" in caplog.messages
    assert "Score: 0" not in caplog.messages
    assert "Question 1/10" in captured.out
    assert "Question 2/10" not in captured.out
    assert "✅ Good job!" not in captured.out
    assert "❗️ Sorry, the correct answer was " not in captured.out
    assert "Final score: 0" in captured.out
    assert "Difficulty level: 2/3" in captured.out
    assert "Are you even trying?" in captured.out
