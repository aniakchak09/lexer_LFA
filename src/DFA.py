from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
# import pandas as pd
from typing import TypeVar
from functools import reduce

STATE = TypeVar('STATE')
OTHER_STATE = TypeVar('OTHER_STATE')


@dataclass
class DFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], STATE]
    F: set[STATE]

    def accept(self, word: str) -> bool:
        # simulate the dfa on the given word. return true if the dfa accepts the word, false otherwise
        current_state = self.q0
        for symbol in word:
            if (current_state, symbol) in self.d:
                current_state = self.d[(current_state, symbol)]
            else:
                return False
        return current_state in self.F

    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'DFA[OTHER_STATE]':
        # Remap states, initial state, and final states
        new_K = {f(state) for state in self.K}
        new_q0 = f(self.q0)
        new_F = {f(state) for state in self.F}
        new_d = {(f(state), symbol): f(target) for (state, symbol), target in self.d.items()}

        return DFA(S=self.S, K=new_K, q0=new_q0, d=new_d, F=new_F)
        # optional, but might be useful for subset construction and the lexer to avoid state name conflicts.
        # this method generates a new dfa, with renamed state labels, while keeping the overall structure of the
        # automaton.

        # for example, given this dfa:

        # > (0) -a,b-> (1) ----a----> ((2))
        #               \-b-> (3) <-a,b-/
        #                   /     ⬉
        #                   \-a,b-/

        # applying the x -> x+2 function would create the following dfa:

        # > (2) -a,b-> (3) ----a----> ((4))
        #               \-b-> (5) <-a,b-/
        #                   /     ⬉
        #                   \-a,b-/


    def minimize(self) -> 'DFA[STATE]':
        self = self.remap_states(lambda x: x)
        states = list(self.K)

        matrix = [[0 for _ in range(len(self.K))] for _ in range(len(self.K))]
        stack = []

        for i in range(len(self.K)):
            for j in range(i):
                if (states[i] in self.F and states[j] not in self.F) or (states[i] not in self.F and states[j] in self.F):
                    matrix[i][j] = 1
                    stack.append((i, j))

        while stack:
            i, j = stack.pop()

            for symbol in self.S:
                predecessors_i = set()
                predecessors_j = set()

                for state in self.K:
                    if self.d.get((state, symbol)) == states[i]:
                        predecessors_i.add(state)
                    if self.d.get((state, symbol)) == states[j]:
                        predecessors_j.add(state)

                if predecessors_i != set() and predecessors_j != set():
                    for state_i in predecessors_i:
                        for state_j in predecessors_j:
                            if matrix[states.index(state_i)][states.index(state_j)] == 0 or matrix[states.index(state_j)][
                                states.index(state_i)] == 0:
                                matrix[states.index(state_i)][states.index(state_j)] = 1
                                matrix[states.index(state_j)][states.index(state_i)] = 1
                                stack.append((states.index(state_i), states.index(state_j)))

        # if two states are equivalent, we keep only one of them, renaiming the other to the name of the first one
        state_mapping = {state: state for state in states}
        for i in range(len(self.K)):
            for j in range(i):
                if matrix[i][j] == 0:
                    state_mapping[states[j]] = state_mapping[states[i]]

        # Create new sets of states, transitions, and final states
        new_K = set(state_mapping.values())
        new_q0 = state_mapping[self.q0]
        new_F = {state_mapping[state] for state in self.F}
        new_d = {}
        for (state, symbol), target in self.d.items():
            new_d[(state_mapping[state], symbol)] = state_mapping[target]

        return DFA(S=self.S, K=new_K, q0=new_q0, d=new_d, F=new_F)

