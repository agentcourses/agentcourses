from datetime import datetime


def tell_time():
    return datetime.now().strftime("%H:%M")


TOOLS = {"time": tell_time}
