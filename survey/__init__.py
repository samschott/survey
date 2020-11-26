import itertools

from . import api
from . import helpers
from . import utils

from . import _colors


__all__ = ('update', 'input', 'password', 'accept', 'reject', 'question',
           'confirm', 'select')


def update(value):

    """
    Update the hint.
    """

    api.update(value)


def input(*args, color = _colors.info, **kwargs):

    """
    Await and return input. Respond immediately ``color`` (light blue).

    Other arguments are passed to :func:`api.edit`.

    .. code-block:: py

        answer = survey.input('How old are you? ', '(age) ')
        print(f'You are {answer} years old!')
    """

    result = api.edit(*args, **kwargs)

    api.respond(color = color)

    return result


def password(*args, rune = '*', color = '\x1b[90m', **kwargs):

    """
    Await and return input. Uses ``rune`` to replace keypresses.

    ``color`` (grey) and other arguments are passed to :func:`input`.

    .. code-block:: py

        answer = survey.password('Secret: ')
        print(f'Singing in with {answer}...')
    """

    ofunnel = kwargs.pop('funnel', None)
    nfunnel = lambda _: rune

    funnel = helpers.combine_functions(ofunnel, nfunnel)

    def view(value):
        return (len(value) * rune,)

    result = input(*args, view = view, color = color, **kwargs, funnel = funnel)

    return result


def accept():

    """
    Respond with green.
    """

    api.respond(color = _colors.done)


def reject():

    """
    Respond with red.
    """

    api.respond(color = _colors.fail)


def question(*args, **kwargs):

    """
    Await and return input. Use ``accept`` or ``reject`` to respond.

    Other arguments are passed to :func:`api.edit`.

    .. code-block:: py

        check = lambda answer: answer.isdigit()
        answer = survey.question('Solve 2+2: ', check = check)
        correct = int(answer) == 4
        (survey.accept if correct else survey.reject)()
    """

    return api.edit(*args, **kwargs)


def confirm(*args,
            sentiments = [
                ('n', 'no', '0', 'false', 'f'),
                ('y', 'yes', '1', 'true', 't')
            ],
            responses = ('No', 'Yes'),
            default = None,
            color = _colors.info,
            **kwargs):

    """
    Await sentiment input and return respective :func:`bool` value.

    :param list[set,set] sentiments:
        Containers of negative and positive options.
    :param list[str,str] responses:
        Negative and positive responses.
    :param bool default:
        Match empty responses to this.

    When ``hint`` is ommited, a suitable one takes its place.

    ``color`` and other arguments except ``view``, ``limit`` and ``check`` are
    passed to :func:`input`.

    .. code-block:: py

        result = survey.confirm('Proceed? ', default = True)
        print('Doing...' if result else 'Skipping...')
    """

    if not 'hint' in kwargs:
        template = helpers.paint('({0}/{1}) ', _colors.hint)
        kwargs['hint'] = utils.hint.confirm(template, default, color = color)

    index = None
    def check(value):
        if value:
            nonlocal index
            value = value.lower()
            for (index, sentiment) in enumerate(sentiments):
                if not value in sentiment:
                    continue
                break
            else:
                return False
        elif default is None:
            return False
        return True

    limit = max(map(len, itertools.chain.from_iterable(sentiments)))

    value = None
    def view(_):
        nonlocal value
        value = default if index is None else bool(index)
        response = responses[value]
        return (response,)

    input(
        *args,
        **kwargs,
        view = view,
        limit = limit,
        check = check,
        color = color
    )

    return value


def select(*args, color = _colors.info, focus = _colors.info, **kwargs):

    """
    Same as :func:`api.select`, except responds immediately using ``color``.

    When ``hint`` is ommited, a suitable one takes its place. The filter value
    will be formatted on the first placeholder (``{0}``).

    ``focus`` as ``color`` and other arguments are passed to :func:`api.select`.

    .. code-block:: py

        options = ('eat', 'sleep', 'code', 'repeat')
        index = survey.select(options, 'Do: ')

        options = ('bacon', 'lettuce', 'tomato', 'malted bread')
        indexes = survey.select(options, 'Use: ', multi = True)
    """

    if not 'hint' in kwargs:
        instructs = ['filter: type', 'move: ↑↓']
        if kwargs.get('multi', False):
            instructs.extend(('pick: → all: →→', 'unpick: ← all: ←←'))
        template = '{0} [' + ' | '.join(instructs) + ']'
        template = helpers.paint(template, _colors.hint)
        kwargs['hint'] = template

    template = kwargs['hint']
    if not template is None:
        (invoke, hint) = utils.hint.select(
            template,
            external = True,
            color = color
        )
        callback = kwargs.get('callback')
        callback = helpers.succeed_functions(invoke, callback)
        kwargs['callback'] = callback
        kwargs['hint'] = hint

    result = api.select(*args, **kwargs, color = focus)

    api.respond(color = color)

    return result
