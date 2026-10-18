def register(name: str) -> Callable[[Statistic], Statistic]:
    """Add a statistic to STATISTICS under `name` and return it unchanged.

    Raises:
        ValueError: Another statistic already uses `name`.
    """
    def decorator(f: Statistic) -> Statistic:
        if name not in STATISTICS:
            STATISTICS[name] = f
            return f
        else:
            raise ValueError(f"{f!r} already existed")
    return decorator

@register("cv2")
def cv2(values: Values) -> float | None:
    number_values = 0
    sum_values = 0.0
    for value in values:
        if value is not None and value != 0:
            number_values += 1
            sum_values += value

    average_values = sum_values / number_values if sum_values > 0 else None

    deviation = 0
    for value in values:
        if value is not None and value != 0:
            deviation += ((value - average_values) ** 2)

    variation = deviation / number_values if number_values > 0 else None

    cv2 = variation / (average_values ** 2) if average_values is not None  and average_values > 0 else None
    print(cv2)
    return cv2

