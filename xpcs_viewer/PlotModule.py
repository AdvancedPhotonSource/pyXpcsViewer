

class PlotModule(object):
    def __init__(self):
        self.state = 0

    def prepare_data(self, data_model):
        self.state = 1
        pass

    def setup_plot(self):
        pass

    def plot(self):
        pass


class Saxs2D(PlotModule):
