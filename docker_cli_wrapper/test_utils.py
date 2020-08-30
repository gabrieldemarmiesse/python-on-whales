import random
import string


def random_name() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))
