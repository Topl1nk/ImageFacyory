class NodeBase:
    def __init__(self, name="Unnamed Node"):
        self.name = name
        self.inputs = []
        self.outputs = []

    def add_input(self, name):
        self.inputs.append(name)

    def add_output(self, name):
        self.outputs.append(name)

    def get_inputs(self):
        return self.inputs

    def get_outputs(self):
        return self.outputs
