from src.Regex import Regex, parse_regex
from src.NFA import NFA
from functools import reduce

EPSILON = ''

class Lexer:
    def __init__(self, spec: list[tuple[str, str]]) -> None:
        # build a nfa that will contain the nfa of each token
        self.nfa = NFA(set(), set(), 0, {(0, EPSILON): set()}, set())
        self.nfa.K.add(0)
        self.nfa.q0 = 0 # there will be one starting state that leads to the starting states of the nfa of each token
        self.nfa.F = set()
        self.final_states = {}  # map from final states of the nfa to the token they represent
        offset = 1

        # transform every lexeme into a nfa and add it to the nfa of the lexer
        for i in range(len(spec)):
            regex = parse_regex(spec[i][1])
            nfa = regex.thompson().remap_states(lambda x: x + offset)

            offset += len(nfa.K)

            # add the nfa of the token to the nfa of the lexer
            self.nfa.S.update(nfa.S)
            self.nfa.K.update(nfa.K)
            self.nfa.d[(0, EPSILON)].add(nfa.q0)
            self.nfa.d.update(nfa.d)
            self.nfa.F.update(nfa.F)

            # for every final state of the nfa of the token, map it to the token
            for s in nfa.F:
                self.final_states[s] = (spec[i][0], i)

        # transform the nfa of the lexer into a dfa
        # minimizing would mess up the final_states, so we don't do it
        self.dfa = self.nfa.subset_construction()


    def lex(self, word: str) -> list[tuple[str, str]] | None:
        matches = []
        pos = 0

        # simulate the dfa on the given word
        while pos < len(word):
            current_state = self.dfa.q0
            token = ""
            best_match = ""
            remaining = word[pos:]
            built = ""

            # until we reach a final state (followed by sink), keep consuming characters
            while current_state:
                # if we reach a final state, save the token and the match
                if current_state in self.dfa.F:
                    final_states = set(self.final_states) & current_state
                    token = self.final_states[min(final_states)][0]
                    best_match = built

                if remaining:
                    current_state = self.dfa.d.get((current_state, remaining[0]))
                    built += remaining[0]
                    remaining = remaining[1:]
                # if the word was consumed, break
                else:
                    break

            # if no best_match was found, there might be an error
            if not best_match:
                num = word.count('\n', 0, pos)
                char_at = pos - word.rfind('\n', 0, pos)

                if word[pos] not in self.dfa.S:
                    return [("", f"No viable alternative at character {char_at - 1}, line {num}")]
                if pos == len(word) - 1:
                    return [("", f"No viable alternative at character EOF, line {num}")]
                else:
                    return [("", f"No viable alternative at character {char_at}, line {num}")]

            # add the token and the match to the list of matches
            matches.append((token, best_match))
            pos += len(best_match)

        return matches