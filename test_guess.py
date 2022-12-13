from arknights_toolkit.wordle import OperatorWordle

guess = OperatorWordle("./cache/")
while True:
    name = input(">>> ")
    my_res = guess.guess(name, "aaa")
    print(guess.draw(my_res, simple=True))
    if my_res.state != "guessing":
        break
