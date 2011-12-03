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
        label = -1.0 if y == 0 else 1.0

        self.age = self.age + 1
        rate = 1.0 / age
        lam = 7

        # Perform the Adaline update: w_{i+1} = w_i + eta * (y - w_i' * x) * x.
        wx = sum([wi * xi for (wi,xi) in zip(self.w, x)])
        self.w = [(1-rate) * w[i] + rate / lam * (label - wx) * x[i] for i in range(len(self.w))]

    def predict(self, x):
      # Calculate w' * x.
      wx = sum([wi * xi for (wi,xi) in zip(self.w, x)])

      # Return sign(w' * x).
      return 1 if wx >= 0 else 0
