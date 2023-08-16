# Quiz Game
---
# Description
This is a simple quiz game made in python.

You have to answer 10 questions (*), each having 4 possible answers. The possible answers could be harder or easier based on the game level you selected. At the end of the game you can see your score and the level you selected.

You can list all questions and add or delete a question.

(*) You can modify the number of questions by changing the `ROUNDS` variable in the `project.py` file.

## Play game
Passing no arguments or passing only `play` argument will start the game at level 1:
```
python project.py
python project.py play
```
Passing also `-l` or `--level` will start the game at the level selected (from 1 - easy to 3 - hard):
```python
# start the game at level 2
python project.py play -l 2
# start the game at level 3
python project.py play --level 3
```
For each question you will have 4 possible answers. Only one of them is the correct one. To respond you enter either 1, 2, 3, or 4 corresponding to each displayed answer. You can also enter `quit` to quit the game.

At the end of the game you will be presented with the total score, the level you selected and a message based on your score.

## List questions
```
python project.py list
```
This will list all questions along with an index wich can be used to identify the question when you want to delete it.

## Delete question
```python
python project.py delete <question_no>
# delete question 12
python project.py delete 12
```
To delete a question you need to provide the `delete` argument along with the question index provided by the `list` argument (see previous section).

You will see the question selected for deleting and will have to confirm the deletion with `y` or `yes`.

## Add question
To add a question use the `add` argument:
```python
python project.py add
```
You will have to enter the question, a correct answer and 5 incorrect answers, each one 'harder' then the previous one.

## Game level
Each question has 5 incorrect answers each one 'harder' then the previous one:
`1 < 2 < 3 < 4 < 5`.

When selecting a level you will get (along with the correct answer):
- level 1: answers 1, 2, 3
- level 2: answers 2, 3, 4
- level 3: answers 3, 4, 5

So by selecting level 3 the answer will be harder to guess.

## .json
All questions are saved to a json file (questions.json).

When trying to open or save the game will validate the file using a custom json schema. This ensures that the data is correct.