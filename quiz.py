import json
import logging
from argparse import ArgumentParser, Namespace
from sys import argv, exit
from typing import Annotated, Optional
from validator_collection import validators, errors


def main():
    logging.basicConfig(
        format='%(levelname)s: %(message)s',
        level=logging.DEBUG)

    if argv[1:]:
        logging.debug(f"Send arguments from CLI: {argv[1:]}")
        args = parse_args(argv[1:])
    else:
        logging.warning("Send no arguments")
        args = parse_args()

    logging.debug(f"Returned form parsing args: {args}")
    match args.action:
        case "play":
            logging.debug(f"Send to play game function: {args.level}")
            play_game(args.level)
        case "list":
            logging.debug("Sent to list questions function")
            list_questions()
        case "add":
            logging.debug("Sent to add question function")
            add_question()
        case "delete":
            logging.debug(
                f"Send to delete question function: {args.question_no}")
            delete_question(args.question_no)


def parse_args(
        args: Optional[list[str]] = ["-h"]) -> Optional[Namespace]:
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
    
    parser_list = subparsers.add_parser(
        name="list",
        help="List all the questions in the game")
    
    parser_add = subparsers.add_parser(
        name="add",
        help="Add a question to the game")
    
    parser_delete = subparsers.add_parser(
        name="delete",
        help="Delete a question from the game")
    parser_delete.add_argument(
        "question_no",
        help="Question number to detele (first list questions)",
        type=int)
    

    return(parser.parse_args(args))


def play_game(level: Annotated[int, range(1,4)]) -> None:
    """Start the game with difficulty set at `level`."""
    logging.info(f"Start game with level: {level}")


def list_questions() -> None:
    """List all questions indexed."""
    logging.info("List all questions")
    questions = open_json()
    for poz, question in enumerate(questions):
        print(f"{poz + 1:>4} - {question['name']}")
        logging.debug(f"{question['answ_good']!r} {question['answ_bad']}")


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
                logging.debug(f"Empty value for: {input_questions[in_q]!r}")

    logging.debug(f"New question to add: {question}")

    questions = open_json()
    questions.append(question)
    if save_json(questions):
        print("Question added")
        logging.info(f"Added question: {question}")
    else:
        print("Question not added... Try again")


def delete_question(question_no: int) -> None:
    """Delete `question_no` from the file."""
    logging.info(f"Delete question: {question_no}")

    questions = open_json()
    # validate question number and retrieve the index question
    try:
        question_index = validators.integer(
            question_no - 1,
            minimum=0,
            maximum=len(questions) - 1)
    except errors.MinimumValueError:
        logging.debug(f"{question_no} < minimum allowed (0)")
        exit("Minimum question number is 1")
    except errors.MaximumValueError:
        logging.debug(f"{question_no} > maximum allowed ({len(questions)})")
        exit(f"Maximum question number is {len(questions)}")
    
    # confirmation
    confirm = input(f"This will delete question number {question_no}:\n  " +
          questions[question_index]["name"].rstrip("?") +
          "\nAre you sure? (y)es: ")
    if confirm in {"yes", "y"}:
        del questions[question_index]
        if save_json(questions):
            logging.info(f"Deleted question: {question_no}")
            print("Question was deleted")
        else:
            print("Question was not deleted")
    else:
        print("Question was not deleted")


def open_json(filename: str = "questions.json") -> list[dict[str, str|list]]:
    """Open the question json file."""
    logging.info(f"Opening json: {filename}")
    try:
        with open(filename) as json_file:
            questions = json.load(json_file)
        with open("json_schema.json") as schema_file:
            schema = json.load(schema_file)
        validators.json(questions, schema)
        return questions
    except FileNotFoundError as err:
        logging.debug(err)
        logging.critical(f"File {filename!r} not found")
    except json.JSONDecodeError as err:
        logging.debug(err)
        logging.critical(f"File {filename!r} is not a correct json file")
    except errors.JSONValidationError as err:
        logging.debug(err)
        logging.critical(f"There is invalid data in {filename!r}")
    exit("Quit because of fatal error")


def save_json(
        questions: list[dict[str, str|list]],
        filename: str = "questions.json") -> Optional[bool]:
    """Save questions to the json file."""
    logging.info(f"Saving json: {filename}")
    try:
        with open("json_schema.json") as schema_file:
            schema = json.load(schema_file)
        validators.json(questions, schema)
        with open(filename, "w+") as json_file:
            json.dump(questions, json_file, indent=2)
        return True
    except FileNotFoundError as err:
        logging.debug(err)
        logging.warning(f"File {filename!r} not found")
    except json.JSONDecodeError as err:
        logging.debug(err)
        logging.warning(f"File {json_file!r} is not a correct json file")
    except errors.JSONValidationError as err:
        logging.debug(err)
        logging.critical(f"Element was not validated")
    exit("Quit because of fatal error")


if __name__ == "__main__":
    main()