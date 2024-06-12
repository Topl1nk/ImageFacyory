from node_base import NodeBase

class ExampleNode(NodeBase):
    def __init__(self):
        super().__init__(name="Example Node")
        self.inputs.append("File Input")
        self.inputs.append("Fileфаы Iффыаnpпвut")
        self.inputs.append("Fileфыа Inывпput")
        self.inputs.append("Filфыаe Inpаut")
        self.inputs.append("Filфвe фаInput")
        self.inputs.append("File ффывыаInput")
        self.inputs.append("File фыаInпывput")
        self.inputs.append("Fisdgsdgnфыввыявput")
        self.outputs.append("Processed Oварutput")
        self.outputs.append("Processed Outpварврut")
        self.outputs.append("Proceфыввssed Output")
        self.outputs.append("Proceфыв ssed Output")
        self.outputs.append("Processварed Ouварtput")
        print("ExampleNode created")
