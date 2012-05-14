from models import GossipLearningModel

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class P2PegasosModel(GossipLearningModel):

    def __init__(self):
        super(P2PegasosModel, self).__init__()

        # Initial model
        self.w = [0, 0, 0, 0, 0]
        self.age = 0

    def update(self, x, y):
        """Update the model with a new training example."""
        # Set up some variables.
        label = -1.0 if y == 0 else 1.0

        self.age = self.age + 1
        lam = 0.0001
        rate = 1.0 / (self.age * lam)

        is_sv = label * sum([self.w[i] * x[i] for i in range(len(self.w))]) < 1.0
        max_dim = max(len(self.w), len(x))
        for i in range(max_dim):
            if is_sv:
                self.w[i] = (1.0 - 1.0 / self.age) * self.w[i] + rate * label * x[i]
            else:
                self.w[i] = (1.0 - 1.0 / self.age) * self.w[i]

    def predict(self, x):
        """
        Compute the inner product of the hyperplane and the instance as a
        prediction.
        """
        wx = sum([self.w[i] * x[i] for i in range(len(self.w))])
        return 1.0 if wx >= 0.0 else 0.0

    def merge(self, model):
        self.age = max(self.age, model.age)
        self.w = [(self.w[i] + model.w[i]) / 2.0 for i in range(len(self.w))]

