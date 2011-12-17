from Tribler.community.gossiplearningframework.payload import GossipMessage

if __debug__:
    from Tribler.Core.dispersy.dprint import dprint

class GossipLearningModel(GossipMessage):

    def __init__(self):
        pass

    def update(self):
        raise NotImplementedError('update')

    def update(self):
        raise NotImplementedError('predict')
