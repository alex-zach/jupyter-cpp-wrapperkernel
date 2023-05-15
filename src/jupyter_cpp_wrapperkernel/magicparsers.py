def list_parser(value, prev):
    return prev + [el.strip() for el in value.split(',')]

def last_value_parser(value, prev):
    return value