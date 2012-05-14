from math import exp
from models import GossipLearningModel

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class LogisticRegressionModel(GossipLearningModel):

    def __init__(self):
        super(LogisticRegressionModel, self).__init__()

        # Initial model
        self.w = [0, 0, 0, 0, 0]
        self.age = 0

    def update(self, x, y):
        """Update the model with a new training example."""
        # Set up some variables.
        label = 0.0 if y == 0 else 1.0

        self.age = self.age + 1
        lam = 0.0001
        rate = 1.0 / (self.age * lam)

        # Calculate the probability for this instance.
        prob = self.gx(x)
        err = label - prob

        # Compute the new w value.
        self.w = [(1.0 - rate * lam) * self.w[i] - rate * err * x[i] for i in range(len(self.w))]

    def predict(self, x):
        # Find the most likely class.
        pos = self.gx(x)

        if pos > 0.5:
            return 1
        else:
            return 0

    def gx(self, x):
        """Calculate P(Y=1 | X=x, w) = 1 / (1 + e^(w'x))."""
        # Normalization
        x = [x[i]/sum(x) for i in range(len(x))]

        # Calculate w'x.
        wx = sum([self.w[i] * x[i] for i in range(len(self.w))])

        # exp() can't handle too high or too low parameters
        if wx > 114:
            return 1e-50
        elif wx < -112:
            return 1.0 - 1e-50
        else:
            return 1.0 / (1.0 + exp(wx))

    def merge(self, model):
        self.age = (self.age + model.age) >> 1
        self.w = [(self.w[i] + model.w[i]) / 2.0 for i in range(len(self.w))]

