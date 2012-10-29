#
# python Tribler/Main/dispersy.py --script gossiplearningframework-observe
#
# Ensure that the files experiment/gossip_ec_private_key and
# experiment/gossip_ec_master_private_key are available.
#

from hashlib import sha1
from time import time
from os.path import expanduser
from collections import defaultdict
import sys

from community import GossipLearningCommunity

from Tribler.Core.dispersy.resolution import PublicResolution
from Tribler.Core.dispersy.crypto import ec_to_private_bin, ec_from_private_pem, ec_from_public_pem, ec_to_public_bin, ec_generate_key
from Tribler.Core.dispersy.script import ScriptBase
from Tribler.Core.dispersy.member import Member
from Tribler.Core.dispersy.dprint import dprint

import numpy as np

from features import create_features
from dict_vectorizer import DictVectorizer


#hardcoded_member_public_keys = {}

# Load the hardcoded member public keys
#NUMPEERS=100

#for i in range(1, NUMPEERS+1):
#    pem = open(expanduser("experiment/keys/public_M%05d.pem" % i), "r").read()
#    ec = ec_from_public_pem(pem)
#    hardcoded_member_public_keys['M%d' % i] = ec_to_public_bin(ec)

class SetupScript(ScriptBase):
    def run(self):

        self._start_time = time()

        # Generate a new identity.
        ec = ec_generate_key(u"low")
        self._my_member = Member.get_instance(ec_to_public_bin(ec), ec_to_private_bin(ec), sync_with_database=True)

        self.caller(self.setup)

    def join_community(self):

        master_key = "3081a7301006072a8648ce3d020106052b810400270381920004039a2b5690996f961998e72174a9cf3c28032de6e50c810cde0c87cdc49f1079130f7bcb756ee83ebf31d6d118877c2e0080c0eccfc7ea572225460834298e68d2d7a09824f2f0150718972591d6a6fcda45e9ac854d35af1e882891d690b2b2aa335203a69f09d5ee6884e0e85a1f0f0ae1e08f0cf7fbffd07394a0dac7b51e097cfebf9a463f64eeadbaa0c26c0660".decode("HEX")
        master = Member.get_instance(master_key)

        assert self._my_member.public_key
        assert self._my_member.private_key
        assert master.public_key
        assert not master.private_key

        if __debug__:
            dprint("-master- ", master.database_id, " ", id(master), " ", master.mid.encode("HEX"), force=1)
            dprint("-my member- ", self._my_member.database_id, " ", id(self._my_member), " ", self._my_member.mid.encode("HEX"), force=1)

        return GossipLearningCommunity.join_community(master, self._my_member, self._my_member)

    def setup(self):
        """
        Set up the community.
        """

        # join the community with the newly created member
        self._community = self.join_community()
        if __debug__: dprint("Joined community ", self._community._my_member)

#        self._community = GossipLearningCommunity.create_community(self._my_member)
        address = self._dispersy.socket.get_address()
        dprint("Address: ", address)

        # cleanup, TODO
        # community.create_dispersy_destroy_community(u"hard-kill")

        yield 1.0


class RunningScript(SetupScript):
    def run(self):
        super(RunnigScript, self).run()
        self._community._local_database = []
	self._vectorizer = DictVectorizer(sparse=False)

    def user_input(self, label, text):
        # extract features
	x = self._vectorizer.fit_transform(create_features(np.array(text), None))
	# only 2-class problems are available
	y = 1 if label else 0
	# store in local database
	self._community._local_database.append((x, y))

    def predict_input(self, text):
        # extract features
	x = self._vectorizer.transform(create_features(np.array(text), None))
	#predict label
	return self._community.predict(x)

