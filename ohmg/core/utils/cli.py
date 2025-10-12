from typing import Literal


def confirm_continue(
    message: str = "continue?", default: Literal["y", "n"] = "y", do_exit: bool = True
):
    message += " Y/n " if default == "y" else " y/N "
    response = input(message)
    if not response:
        response = default

    choice = True
    if response.lower().startswith("n"):
        choice = False
        if do_exit:
            print("-- cancelling operation")
            exit()
    return choice
