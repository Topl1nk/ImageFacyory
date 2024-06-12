from node_base import NodeBase

class ExampleNode2(NodeBase):
    def __init__(self):
        super().__init__(name="Example Node 2")
        self.inputs = ["[хуй]"]
        self.outputs = ["Output 1"]
        print("ExampleNode2 created")
