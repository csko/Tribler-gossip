# Written by Pawel Garbacki
# see LICENSE.txt for license information

from Tribler.Core.BitTornado.clock import clock

MIN_CAPACITY = 0.75

class RatePredictor:
    def __init__(self, raw_server, rate_measure, max_rate, probing_period = 2):
        self.raw_server = raw_server
        self.rate_measure = rate_measure
        if max_rate == 0:   
            self.max_rate = 2147483647
        else:
            self.max_rate = max_rate
        self.probing_period = probing_period # in seconds

class ExpSmoothRatePredictor(RatePredictor):
    def __init__(self, raw_server, rate_measure, max_rate, alpha = 0.5, max_period = 30, probing_period = 2):
        RatePredictor.__init__(self, raw_server, rate_measure, max_rate, probing_period)
        self.alpha = alpha
        self.max_period = max_period
        self.value = None
        self.timestamp = None

    def update(self):
        self.raw_server.add_task(self.update, self.probing_period)
        current_value = self.rate_measure.get_rate() / 1000.
        current_time = clock()
        if self.value is None or current_time - self.timestamp > self.max_period:
            self.value = current_value
        else:
            self.value = self.alpha * current_value + (1 - self.alpha) * self.value
            if self.max_rate > 0 and self.value > self.max_rate:
                self.value = self.max_rate
        self.timestamp = current_time

    # exponential smoothing prediction
    def predict(self):
        # self.update()
        if self.value is None:
            return 0
        return self.value

    def has_capacity(self):
#        return False
        # self.update()
        result = None
        if self.value is None:
            result = True
        else:
            result = (1. - float(self.value) / self.max_rate) > MIN_CAPACITY
        return result