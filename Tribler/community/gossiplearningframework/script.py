#
# python Tribler/Main/dispersy.py --script gossiplearningframework-observe
#
# Ensure that the files experiment/gossip_ec_private_key and
# experiment/gossip_ec_master_private_key are available.
#

from hashlib import sha1
from time import time
from os.path import expanduser
import sys

from community import GossipLearningCommunity

from Tribler.Core.dispersy.resolution import PublicResolution
from Tribler.Core.dispersy.crypto import ec_to_private_bin, ec_from_private_pem, ec_from_public_pem, ec_to_public_bin, ec_generate_key
from Tribler.Core.dispersy.script import ScriptBase
from Tribler.Core.dispersy.member import Member
from Tribler.Core.dispersy.dprint import dprint

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

    def setup(self):
        """
        Set up the community.
        """

        self._community = GossipLearningCommunity.create_community(self._my_member)
        address = self._dispersy.socket.get_address()

        # cleanup, TODO
        # community.create_dispersy_destroy_community(u"hard-kill")

        yield 1.0

# TODO: proper logging
# TODO: whole database should not be loaded into memory in this script
# TODO: only works on IRIS
class ExperimentScript(SetupScript):
    def run(self):
        super(ExperimentScript, self).run()
        self._train_database = []
        self._eval_database = []
        self.load_database("iris_setosa_versicolor")
        self.caller(self.pick_instances)
        self.caller(self.print_status)

    def print_status(self):
        """
        This will print the status of the model every 10 seconds.
        """
        member_name = self._kargs["hardcoded_member"]
        mid = int(member_name[1:]) - 1

        logfile = "experiment/logs/%05d_setosa_versicolor.log" % mid
        with open(logfile, "w") as f:
            print >>f, "# timestamp member_id age mae msg_count"
            while True:
                print >>f, int(time()), mid,
                print >>f, self._community._model.age, self.predict(), self._community._msg_count, " ".join([str(x) for x in self._community._model.w])
                f.flush()
#                print self._community._model.w, self._community._model.age, self._community._x
#                sys.stdout.flush()
                yield 10.0 # seconds

        yield 1.0


    def load_database(self, fname):
        """
        Load the whole dataset.
        """
        train_data = []
        eval_data = []

        with open("experiment/db/%s_train.dat" % fname) as f:
            for line in f:
                x = {}

                vals = line[:-1].split()
                y = int(vals[0])
                vals = vals[1:]

                for i in vals:
                    k, v = i.split(":")
                    x[int(k)] = float(v)

                # Suppose there are no missing values. Add the bias term.
                x2 = [1.0]
                for k, v in sorted(x.items()):
                    x2.append(v)

                train_data.append((x2, y))

        with open("experiment/db/%s_eval.dat" % fname) as f:
            for line in f:
                x = {}

                vals = line[:-1].split()
                y = int(vals[0])
                vals = vals[1:]

                for i in vals:
                    k, v = i.split(":")
                    x[int(k)] = float(v)

                # Suppose there are no missing values. Add the bias term.
                x2 = [1.0]
                for k, v in sorted(x.items()):
                    x2.append(v)

                eval_data.append((x2, y))

        print "Database loaded."

        self._train_database = train_data
        self._eval_database = eval_data

    def pick_instances(self):
        """
        Choose one or more instances to be placed on the client based on the member ID.
        """

        member_name = self._kargs["hardcoded_member"]
        mid = int(member_name[1:]) - 1

        # For now, choose only one instance based on the member id.
        data = self._train_database[mid % len(self._train_database)]

        self._community._x = data[0]
        self._community._y = data[1]

        # Initialize the model also.
        self._community._w = [0 for i in range(len(self._community._x))]

        dprint("One instance picked.")
        yield 1.0

    def predict(self):
        """
        Predicts on the whole dataset and outputs the results for further analysis.
        """
        mae = 0
        for (x, y) in self._eval_database:
            ypred = int(self._community._model.predict(x))
            # 0-1 error
            if ypred != y:
                mae += 1
#            print y, ypred, y!=ypred
        mae /= 1.0 * len(self._eval_database)
#        print "#"*10

        return mae

