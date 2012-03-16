from models import GossipLearningModel

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class AdalinePerceptronModel(GossipLearningModel):

    def __init__(self):
        super(AdalinePerceptronModel, self).__init__()

        # Initial model
        self.w = [0, 0, 0, 0]
        self.age = 0

    def update(self, x, y):
        """Update the model with a new training example."""
        # Set up some variables.
        x = x[1:] # Remove the bias term.
        label = -1.0 if y == 0 else 1.0 # Remap labels.

        self.age = self.age + 1
        rate = 1.0 / self.age
        lam = 7

        # Perform the Adaline update: w_{i+1} = (1-eta) * w_i + eta/lam * (y - w_i' * x) * x.
        wx = sum([wi * xi for (wi,xi) in zip(self.w, x)])
        self.w = [(1-rate) * self.w[i] + rate / lam * (label - wx) * x[i] for i in range(len(self.w))]

    def predict(self, x):
      x = x[1:] # Remove the bias term.

      # Calculate w' * x.
      wx = sum([wi * xi for (wi,xi) in zip(self.w, x)])

      # Return sign(w' * x).
      return 1 if wx >= 0 else 0
