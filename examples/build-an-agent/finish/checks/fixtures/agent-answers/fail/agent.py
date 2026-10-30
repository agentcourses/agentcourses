def add(a=2, b=3):
    return a + b


TOOLS = {"add": add}


def answer(request):
    if "add" in request:
        return add()
