import hug


@hug.type(extend=hug.types.number)
def hug_timestamp(value):
    """the time in seconds since the epoch as a floating point number"""
    return value
