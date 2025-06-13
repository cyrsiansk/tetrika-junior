import inspect

# При решении задачи пришел к тому, что лучше использовать inspect
# Одно лишь прямое получение поля __annotations__ не позволяет проверять случаи отсутствия аннотации.
# Аргумент в таком случае просто отсутствует в dict аннотации

# > Гарантируется, что в декорируемых функциях не будет значений параметров, заданных по умолчанию
# Да, но добавить же не сложно


def strict(func):
    signature = inspect.signature(func)
    parameters = signature.parameters.values()
    types_args = []
    params_kwargs = {}

    for param in parameters:
        if param.annotation == inspect.Parameter.empty:
            raise TypeError(f'Parameter {param.name} has no type annotation')

        if param.default == inspect.Parameter.empty:
            types_args.append(param.annotation)
        else:
            params_kwargs[param.name] = param

    def wrapper(*args, **kwargs):
        for arg, t in zip(args, types_args):
            if not isinstance(arg, t):
                raise TypeError(f'Expected {t}, got {type(arg)}')

        for name, p in params_kwargs.items():
            kwarg = kwargs.get(name, params_kwargs[name].default)
            if not isinstance(kwarg, p.annotation):
                raise TypeError(f'Expected {p.annotation}, got {type(kwarg)}')
        return func(*args, **kwargs)

    return wrapper
