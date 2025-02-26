from typing import Any, List
from src.NFA import NFA

# list of special characters
special_chars = ['|', '*',  '+', '?', '(', ')', '[', ']']

# trying to simulate an abstract syntax tree
# store the elements of the regex, the leafs of the tree
expression = []
# store the operations of the regex, the nodes of the tree
operations = []

# signals if there was a precedent expression
precedent = False

# index of the current character
i = 0

EPSILON = ''

class Regex:
    def thompson(self) -> NFA[int]:
        raise NotImplementedError('the thompson method of the Regex class should never be called')

# you should extend this class with the type constructors of regular expressions and overwrite the 'thompson' method
# with the specific nfa patterns. for example, parse_regex('ab').thompson() should return something like:

# >(0) --a--> (1) -epsilon-> (2) --b--> ((3))

# extra hint: you can implement each subtype of regex as a @dataclass extending Regex

class Character(Regex):
    def __init__(self, char: str):
        self.char = char

    # implement the thompson construction for a character
    def thompson(self) -> NFA[int]:
        q0 = 0
        q1 = 1
        S = {self.char}
        d = {(q0, self.char): {q1}}

        return NFA(S=S, K={q0, q1}, q0=q0, d=d, F={q1})

class Concat(Regex):
    def __init__(self, left: Regex, right: Regex):
        self.left = left
        self.right = right

    # implement the thompson construction for the concatenation of two regexes
    def thompson(self) -> NFA[int]:
        nfa_left = self.left.thompson()
        nfa_right = self.right.thompson().remap_states(lambda x: x + len(nfa_left.K))
        # remap the states of one of the NFAs to avoid conflicts

        S = nfa_left.S.union(nfa_right.S)
        K = nfa_left.K.union(nfa_right.K)

        d = nfa_left.d.copy()
        d.update(nfa_right.d)

        # add epsilon transitions from the final states of the left nfa to the initial state of the right nfa
        for state in nfa_left.F:
            d[(state, EPSILON)] = {nfa_right.q0}

        q0 = nfa_left.q0
        F = nfa_right.F

        return NFA(S=S, K=K, q0=q0, d=d, F=F)

class Union(Regex):
    def __init__(self, left: Regex, right: Regex):
        self.left = left
        self.right = right

    # implement the thompson construction for the union of two regexes
    def thompson(self) -> NFA[int]:
        nfa_left = self.left.thompson()
        nfa_right = self.right.thompson().remap_states(lambda x : x + len(nfa_left.K))  # so that no states repeat in the resulting nfa
        # no need to remap the states anymore, case the new initial and final states will be unique

        S = nfa_left.S.union(nfa_right.S)
        K = nfa_left.K.union(nfa_right.K)

        new_q0 = max(K) + 1
        new_F = max(K) + 2

        K |= {new_q0, new_F} # add the new initial and final states

        d = nfa_left.d.copy()
        d.update(nfa_right.d)

        # add epsilon transitions from the new initial state to the initial states of the left and right nfas
        d[(new_q0, EPSILON)] = {nfa_left.q0, nfa_right.q0}

        # add epsilon transitions from the final states of the left and right nfas to the new final state
        for state in nfa_left.F:
            d[(state, EPSILON)] = {new_F}
        for state in nfa_right.F:
            d[(state, EPSILON)] = {new_F}

        return NFA(S=S, K=K, q0=new_q0, d=d, F={new_F})

class Star(Regex):
    def __init__(self, inner: Regex):
        self.inner = inner

    # implement the thompson construction for the kleene star of a regex
    def thompson(self) -> NFA[int]:
        nfa = self.inner.thompson()

        new_q0 = max(nfa.K) + 1
        new_F = max(nfa.K) + 2

        S = nfa.S | {EPSILON} # add epsilon to the alphabet
        K = nfa.K | {new_q0, new_F}   # add the new initial and final states

        d = nfa.d.copy()
        # add an epsilon transition from the new initial state to the old first state and the new final state
        d[new_q0, EPSILON] = {nfa.q0, new_F}

        # for all the past final states, add epsilon transitions to the old initial state and the new final state
        for state in nfa.F:
            d[state, EPSILON] = {nfa.q0, new_F}

        return NFA(S=S, K=K, q0=new_q0, d=d, F={new_F})


class Plus(Regex):
    def __init__(self, inner: Regex):
        self.inner = inner

    # implement the thompson construction for the plus of a regex
    # similar to kleene star, but the new initial state doesn't have an epsilon transition to the new final state
    def thompson(self) -> NFA[int]:
        # nfa = self.inner.thompson()
        #
        # new_q0 = max(nfa.K) + 1
        # new_F = max(nfa.K) + 2
        #
        # K = nfa.K | {new_q0, new_F}
        #
        # d = nfa.d.copy()
        # d[new_q0, EPSILON] = {nfa.q0}   # add an epsilon transition from the new initial state to the old initial state
        #
        # # for all the past final states, add epsilon transitions to the old initial state and the new final state
        # for state in nfa.F:
        #     d[state, EPSILON] = {new_F, nfa.q0}
        #
        # return NFA(S=nfa.S, K=K, q0=new_q0, d=d, F={new_F})

        return Concat(self.inner, Star(self.inner)).thompson() #using this: r.r* = r*.r = r+ regex identity

        # return self.inner.thompson()

# quesiton mark
class Maybe(Regex):
    def __init__(self, inner: Regex):
        self.inner = inner

    # implement the thompson construction for the maybe of a regex
    def thompson(self) -> NFA[int]:
        nfa = self.inner.thompson()

        # make the initial state final
        return NFA(S=nfa.S, K=nfa.K, q0=nfa.q0, d=nfa.d, F=nfa.F | {nfa.q0})


class Lowercase(Regex):
    def __init__(self):
        letters = [Character(chr(letter)) for letter in range(ord('a'), ord('z') + 1)]
        self.regex = letters[0]
        for letter in letters[1:]:
            self.regex = Union(self.regex, letter)

    # implement the thompson construction for a lowercase character
    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

class Uppercase(Regex):
    def __init__(self):
        letters = [Character(chr(letter)) for letter in range(ord('A'), ord('Z') + 1)]
        self.regex = letters[0]
        for letter in letters[1:]:
            self.regex = Union(self.regex, letter)

    # implement the thompson construction for an uppercase character
    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

class Digit(Regex):
    def __init__(self):
        digits = [Character(str(digit)) for digit in range(10)]
        self.regex = digits[0]
        for digit in digits[1:]:
            self.regex = Union(self.regex, digit)

    # implement the thompson construction for a digit
    def thompson(self) -> NFA[int]:
        return self.regex.thompson()


def process_char(char:str, regex:str):
    global precedent, expression, operations, i

    # add a concatenation operation if there was a precedent expression
    if precedent:
        operations.append('.')
    precedent = True

    # if the character is a backslash, escape the next character
    if char == '\\' and i < len(regex) - 1:
        i += 1
        char = regex[i]

    expression.append(Character(char))
    i += 1


def process_special_char(char:str, regex:str):
    global precedent, expression, operations, i

    # if the character is an open bracket, add a concatenation operation if there was a precedent expression
    if char == '(':
        if precedent:
            operations.append('.')  # add a concatenation operation if there was a precedent expression

        precedent = False   # no precedent expression after an open bracket
        operations.append('(')
        i += 1
    # if the character is a closing bracket, process the operations and expressions until the last open bracket
    elif char == ')':
        while operations[-1] != '(':
            op = operations.pop()

            right = expression.pop()
            left = expression.pop()

            if op == '.':
                expression.append(Concat(left, right))
            elif op == '|':
                expression.append(Union(left, right))

        operations.pop() # remove the '('
        i += 1
        precedent = True # reset the precedent flag
    # if the character is '|', process the operations and expressions until the last concatenation operation to obtain the nfa on the right side
    elif char == '|':
        while operations and operations[-1] == '.':
            operations.pop()

            right = expression.pop()
            left = expression.pop()

            expression.append(Concat(left, right))

        operations.append('|')
        i += 1
        precedent = False   # no precedent expression after a '|'
    # if the character is '*', '+', or '?', process the last expression
    elif char in ['*', '+', '?']:
        if char == '*':
            expression.append(Star(expression.pop()))
        elif char == '+':
            expression.append(Plus(expression.pop()))
        elif char == '?':
            expression.append(Maybe(expression.pop()))

        i += 1
        precedent = True
    # if the character is '[', process the range
    elif char == '[':
        if precedent:
            operations.append('.')

        closing = regex.find(']', i) # find the closing bracket position

        if closing != -1 and closing - i == 4:
            range = regex[i + 1: closing]

            if range == "a-z":
                expression.append(Lowercase())
            elif range == "A-Z":
                expression.append(Uppercase())
            elif range == "0-9":
                expression.append(Digit())

            i = closing + 1
            precedent = True # following expression concatenates


def parse_regex(regex: str) -> Regex:
    global expression, operations, precedent, i
    # create a Regex object by parsing the string

    # you can define additional classes and functions to help with the parsing process

    # the checker will call this function, then the thompson method of the generated object. the resulting NFA's
    # behaviour will be checked using your implementation form stage 1

    i = 0
    precedent = False
    expression = []
    operations = []

    # iterate over the regex and create the AST
    while i < len(regex):
        if regex[i] == ' ':
            i += 1
            continue

        if regex[i] in special_chars:
            process_special_char(regex[i], regex)
        else:
            process_char(regex[i], regex)

    # process the remaining operations
    while operations:
        op = operations.pop()

        right = expression.pop()
        left = expression.pop()

        if op == '.':
            expression.append(Concat(left, right))
        elif op == '|':
            expression.append(Union(left, right))

    return expression[0]
