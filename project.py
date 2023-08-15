"""Simple quiz game."""


import json
import logging
import random
from argparse import ArgumentParser, Namespace
from sys import argv, exit
from typing import Annotated, Optional

from validator_collection import errors, validators


def main():
    """Main function."""
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.CRITICAL)

    if argv[1:]:
        logging.debug("Send arguments from CLI: %s", argv[1:])
        args = parse_args(argv[1:])
    else:
        logging.warning("Send no arguments")
        args = parse_args()

    logging.debug("Returned form parsing args: %s", args)
    match args.action:
        case "play":
            logging.debug("Send to play game function: %s", args.level)
            play_game(args.level)
        case "list":
            logging.debug("Sent to list questions function")
            list_questions()
        case "add":
            logging.debug("Sent to add question function")
            add_question()
        case "delete":
            logging.debug(
                "Send to delete question function: %s", args.question_no)
            delete_question(args.question_no)


def parse_args(
        args: Optional[list[str]] = ["play"]) -> Optional[Namespace]:
    """Parse the arguments and return a namespace with options."""
    parser = ArgumentParser(description="A simple quiz game")

    subparsers = parser.add_subparsers(dest='action', required=True)

    parser_play = subparsers.add_parser(
        name="play",
        help="Play the game and optionally specify a level (default 1)")
    parser_play.add_argument(
        "-l", "--level",
        help="Game level: 1(easy) - 3(hard)",
        type=int,
        choices=range(1, 4),
        default="1")

    subparsers.add_parser(
        name="list",
        help="List all the questions in the game")

    subparsers.add_parser(
        name="add",
        help="Add a question to the game")

    parser_delete = subparsers.add_parser(
        name="delete",
        help="Delete a question from the game")
    parser_delete.add_argument(
        "question_no",
        help="Question number to detele (first list questions)",
        type=int)

    return parser.parse_args(args)


def play_game(level: Annotated[int, range(1, 4)]) -> None:
    """Start the game with difficulty set at `level`."""
    logging.info("Start game with level: %s", level)

    ROUNDS = 10

    questions = open_json()
    if len(questions) < ROUNDS:
        exit("Not enough questions")

    score = 0

    def print_score() -> None:
        print(f"\nFinal score: {score}")
        print(f"Difficulty level: {level}/3")
        if score == 10:
            print("Perfect game!!!")
        elif score >= 8:
            print("Good game")
        elif score == 7:
            print("Pretty good game")
        elif score >= 5:
            print("Maybe you can do better")
        elif score >= 3:
            print("Have another try")
        elif score >= 1:
            print("You really should have another try")
        else:
            print("Are you even trying?")

    for round_no in range(1, ROUNDS + 1):
        # print the question
        print(f"\nQuestion {round_no}/{ROUNDS}")
        question = questions.pop(random.randint(0, len(questions) - 1))
        print(question["name"])
        logging.debug(question["name"])
        # print the variants
        variants: list = (question["answ_bad"][level-1:level+2] +
                          [question["answ_good"]])
        random.shuffle(variants)
        for poz, variant in enumerate(variants):
            print(f"({poz + 1}) {variant}")
        # logging correct answer
        logging.debug(variants.index(question["answ_good"]) + 1)

        # get answer from user
        while True:
            answer = input("Your answer (1, 2, 3 or 4): ").lower()
            if answer in {"1", "2", "3", "4", "quit"}:
                if answer == "quit":
                    print_score()
                    exit("Game ended")
                break
            else:
                print("Enter '1', '2', '3' or '4'.\nEnter 'quit' to quit game")

        # check answer
        if variants[int(answer) - 1] == question["answ_good"]:
            score += 1
            print("✅ Good job!")
        else:
            print(f"❗️ Sorry, the correct answer was {question['answ_good']}")
        logging.info("Score: %s", score)

    print_score()


def list_questions() -> None:
    """List all questions indexed."""
    logging.info("List all questions")
    questions = open_json()
    for poz, question in enumerate(questions):
        print(f"{poz + 1:>4} - {question['name']}")
        logging.debug("'%s' %s", question['answ_good'], question['answ_bad'])


def add_question() -> None:
    """Add a question to the file."""
    logging.info("Add a question")
    print("You need to provide:",
          "  - a question",
          "  - 1 correct answer",
          "  - 3 incorrect easy answers",
          "  - 1 incorrect medium answer",
          "  - 1 incorrect hard answer", sep="\n")

    question = {"name": "", "answ_good": "", "answ_bad": []}
    input_questions = {
        "Question: ": "name",
        "Correct answer: ": "answ_good",
        "First incorrect easy answer: ": "answ_bad",
        "Second incorrect easy answer: ": "answ_bad",
        "Third incorrect easy answer: ": "answ_bad",
        "Incorrect medium answer: ": "answ_bad",
        "Incorrect hard answer: ": "answ_bad"
    }
    for in_q in input_questions:
        while True:
            try:
                answer = validators.string(input(in_q).strip())
                if input_questions[in_q] == "answ_bad":
                    if (answer == question["answ_good"] or
                            answer in question["answ_bad"]):
                        print("Allready added this answer!")
                        continue
                    question[input_questions[in_q]].append(answer)
                else:
                    question[input_questions[in_q]] = answer
                break
            except errors.EmptyValueError:
                logging.debug("Empty value for: '%s'", input_questions[in_q])

    logging.debug("New question to add: %s", question)

    questions = open_json()
    questions.append(question)
    if save_json(questions):
        print("Question added")
        logging.info("Added question: %s", question)
    else:
        print("Question not added... Try again")


def delete_question(question_no: int) -> None:
    """Delete `question_no` from the file."""
    logging.info("Delete question: %s", question_no)

    questions = open_json()
    # validate question number and retrieve the index question
    try:
        question_index = validators.integer(
            question_no - 1,
            minimum=0,
            maximum=len(questions) - 1)
    except errors.MinimumValueError:
        logging.debug("%s < minimum allowed (0)", question_no)
        exit("Minimum question number is 1")
    except errors.MaximumValueError:
        logging.debug("%s > maximum allowed (%s)", question_no, len(questions))
        exit(f"Maximum question number is {len(questions)}")

    # confirmation
    confirm = input(f"This will delete question number {question_no}:\n  " +
                    questions[question_index]["name"].rstrip("?") +
                    "\nAre you sure? (y)es: ")
    if confirm in {"yes", "y"}:
        del questions[question_index]
        if save_json(questions):
            logging.info("Deleted question: %s", question_no)
            print("Question was deleted")
        else:
            print("Question was not deleted")
    else:
        print("Question was not deleted")


def open_json(filename: str = "questions.json") -> list[dict[str, str | list]]:
    """Open the question json file."""
    logging.info("Opening json: %s", filename)
    try:
        with open(filename, encoding="UTF-8") as json_file:
            questions = json.load(json_file)
        with open("json_schema.json", encoding="UTF-8") as schema_file:
            schema = json.load(schema_file)
        validators.json(questions, schema)
        return questions
    except FileNotFoundError as err:
        logging.debug(err)
        logging.critical("File '%s' not found", filename)
    except json.JSONDecodeError as err:
        logging.debug(err)
        logging.critical("File '%s' is not a correct json file", filename)
    except errors.JSONValidationError as err:
        logging.debug(err)
        logging.critical("There is invalid data in '%s'", filename)
    exit("Quit because of fatal error")


def save_json(
        questions: list[dict[str, str | list]],
        filename: str = "questions.json") -> Optional[bool]:
    """Save questions to the json file."""
    logging.info("Saving json: %s", filename)
    try:
        with open("json_schema.json", encoding="UTF-8") as schema_file:
            schema = json.load(schema_file)
        validators.json(questions, schema)
        with open(filename, "w+", encoding="UTF-8") as json_file:
            json.dump(questions, json_file, indent=2)
        return True
    except FileNotFoundError as err:
        logging.debug(err)
        logging.warning("File '%s' not found", filename)
    except json.JSONDecodeError as err:
        logging.debug(err)
        logging.warning("File '%s' is not a correct json file", json_file)
    except errors.JSONValidationError as err:
        logging.debug(err)
        logging.critical("Element was not validated")
    exit("Quit because of fatal error")


if __name__ == "__main__":
    main()
