def add(a=2, b=3):
    return a + b


TOOLS = {"add": add}


def answer(request):
    for name, tool in TOOLS.items():
        if name in request:
            return f"The {name} tool says {tool()}."
    return "I can answer that without a tool."
