from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable
from typing import TypeVar

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs
STATE = TypeVar('STATE')
OTHER_STATE = TypeVar('OTHER_STATE')

@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # compute the epsilon closure of a state (you will need this for subset construction)
        # see the EPSILON definition at the top of this file
        closure = set[STATE]()
        stack = [state]

        closure.add(state)

        while stack:
            current_state = stack.pop()

            for next_state in self.d.get((current_state, EPSILON), []):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)

        return closure

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # convert this nfa to a dfa using the subset construction algorithm
        DFA_states = set()
        DFA_transitions = {}
        alphabet = self.S - {EPSILON}
        initial_closure = frozenset(self.epsilon_closure(self.q0))
        sink_state = frozenset()
        DFA_states.add(initial_closure)
        stack = [initial_closure]

        # check if the DFA has a sink state
        sink = False

        while stack:
            current_state = stack.pop()

            # iterate over the alphabet
            for symbol in alphabet:
                next_states = set()

                # iterate over the closure of the current state
                for state in current_state:
                    if (state, symbol) in self.d:
                        next_states.update(self.d.get((state, symbol), []))

                # compute the epsilon closure of the next states
                next_closure = frozenset(
                    state for next_state in next_states for state in self.epsilon_closure(next_state)
                )

                # if there is no next state, go to the sink state
                if not next_closure:
                    next_closure = sink_state
                    sink = True # the DFA has a sink state

                if next_closure not in DFA_states:
                    DFA_states.add(next_closure)
                    stack.append(next_closure)

                DFA_transitions[current_state, symbol] = next_closure

        # add the sink state to the DFA
        if sink:
            DFA_states.add(sink_state)
            for symbol in alphabet: # add the from the sink state to itself
                DFA_transitions[sink_state, symbol] = sink_state

        DFA_final_states = {state for state in DFA_states if any(s in self.F for s in state)}

        return DFA(
            S=alphabet,
            K=DFA_states,
            q0=initial_closure,
            d=DFA_transitions,
            F=DFA_final_states
        )

    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        new_K = {f(state) for state in self.K}
        new_q0 = f(self.q0)
        new_F = {f(state) for state in self.F}
        new_d = {(f(state), symbol): {f(target) for target in targets} for (state, symbol), targets in self.d.items()}

        return NFA(S=self.S, K=new_K, q0=new_q0, d=new_d, F=new_F)
