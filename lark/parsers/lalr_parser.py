from .lalr_analysis import ACTION_SHIFT
from ..common import ParseError

class UnexpectedToken(ParseError):
    def __init__(self, token, expected, seq, index):
        self.token = token
        self.expected = expected
        self.line = getattr(token, 'line', '?')
        self.column = getattr(token, 'column', '?')

        context = ' '.join(['%r(%s)' % (t.value, t.type) for t in seq[index:index+5]])
        message = ("Unexpected input %r at line %s, column %s.\n"
                   "Expected: %s\n"
                   "Context: %s" % (token.value, self.line, self.column, expected, context))

        super(ParseError, self).__init__(message)




class Parser(object):
    def __init__(self, ga, callback):
        self.ga = ga
        self.callbacks = {rule: getattr(callback, rule.alias or rule.origin, None)
                          for rule in ga.rules}

    def parse(self, seq):
        states_idx = self.ga.states_idx

        stack = [(None, self.ga.init_state_idx)]
        i = 0
        res = None

        def get_action(key):
            state = stack[-1][1]
            try:
                return states_idx[state][key]
            except KeyError:
                expected = states_idx[state].keys()
                try:
                    token = seq[i]
                except IndexError:
                    assert key == '$end'
                    token = seq[-1]

                raise UnexpectedToken(token, expected, seq, i)

        def reduce(rule):
            if rule.expansion:
                s = stack[-len(rule.expansion):]
                del stack[-len(rule.expansion):]
            else:
                s = []

            res = self.callbacks[rule]([x[0] for x in s])

            if rule.origin == self.ga.start_symbol and len(stack) == 1:
                return res

            _action, new_state = get_action(rule.origin)
            assert _action == ACTION_SHIFT
            stack.append((res, new_state))

        # Main LALR-parser loop
        while i < len(seq):
            action, arg = get_action(seq[i].type)

            if action == ACTION_SHIFT:
                stack.append((seq[i], arg))
                i+= 1
            else:
                reduce(arg)

        while stack:
            _action, rule = get_action('$end')
            assert _action == 'reduce'
            res = reduce(rule)
            if res:
                break

        assert stack == [(None, self.ga.init_state_idx)], len(stack)
        return res


