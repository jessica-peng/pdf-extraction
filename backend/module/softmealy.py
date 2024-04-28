from graphviz import Digraph


class SoftMealy:
    def __init__(self, states, initState, inAlphabet, outAlphabet, transitionFunction, outputFunction, finalStates):
        self.states = states
        self.initState = initState
        self.inAlphabet = inAlphabet
        self.outAlphabet = outAlphabet
        self.transitions = transitionFunction
        self.outputs = outputFunction
        self.finalStates = finalStates
        self.current_state = initState

        self.trFuncDict = dict()
        for (current_state, input_symbol, next_state) in self.transitions:
            if (current_state, input_symbol) in self.trFuncDict:
                temp = self.trFuncDict[current_state, input_symbol] \
                    if isinstance(self.trFuncDict[current_state, input_symbol], list) \
                    else [self.trFuncDict[current_state, input_symbol]]
                self.trFuncDict[current_state, input_symbol] = temp + [next_state]
            else:
                self.trFuncDict[current_state, input_symbol] = next_state

        self.usedState = list()
        for transition in self.transitions:
            state1 = transition[0]
            state2 = transition[2]
            if state1 not in self.usedState:
                self.usedState.append(state1)
            if state2 not in self.usedState:
                self.usedState.append(state2)

    def step(self, input_symbol):
        if self.trFuncDict[self.current_state, input_symbol] is None:
            raise ValueError("Invalid input symbol")

        next_state = self.trFuncDict[self.current_state, input_symbol]
        output = 'O' + next_state
        self.current_state = 'dummy/' + next_state
        return output

    def reset(self, start_state):
        self.current_state = start_state

    def exportDigraph(self):
        # Create a Graphviz Digraph object
        dot = Digraph()

        # Add the nodes to the Digraph
        for state in self.states:
            if state not in self.usedState:
                continue

            if state == self.finalStates:
                dot.node(str(state), label=str(state), shape='doublecircle')
            else:
                if 'dummy' in state:
                    state = state.split('/')[0] + '\n' + state.split('/')[1]
                dot.node(str(state), label=str(state), shape='circle')

        # Add the edges to the Digraph
        for transition in self.transitions:
            # print(transition)
            state = transition[0]
            symbol = transition[1]
            next_state = transition[2]
            if 'dummy' in state:
                state = state.split('/')[0] + '\n' + state.split('/')[1]

            if 'dummy' in next_state:
                next_state = next_state.split('/')[0] + '\n' + next_state.split('/')[1]
            dot.edge(str(state), str(next_state), label=f"{symbol}")
        dot.attr(rankdir='LR')

        # Render the Digraph to a PDF file
        dot.render('softmealy', format='png')

    def next_state(self, current_state):
        next_list = list()
        for (from_state, input_symbol), to_state in self.trFuncDict.items():
            if input_symbol == 'skip':
                continue

            if from_state == current_state:
                next_state = {
                    'input_symbol': input_symbol,
                    'next_state': to_state
                }
                next_list.append(next_state)
        return next_list
