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

# TODO: proper logging
# TODO: only works on IRIS
class ExperimentScript(SetupScript):
    def run(self):
        super(ExperimentScript, self).run()
        self._train_database = []
        self._eval_database = []
        self.caller(self.load_database)
        self.caller(self.print_status)

    def print_status(self):
        """
        Print the status of the model every 10 seconds.
        """
        member_name = self._kargs["hardcoded_member"]
        mid = int(member_name[1:]) - 1

        logfile = "experiment/logs/%05d_%s.log" % (mid, self._kargs["database"])
        with open(logfile, "w") as f:
            print >>f, "# timestamp member_id age mae msg_count"
            while True:
                print >>f, int(time()), mid,
                print >>f, self._community._model_queue[-1].age, self.predict(), self._community._msg_count, \
                        " ".join([str(x) for x in self._community._model_queue[-1].w])
                f.flush()
#                print self._community._model.w, self._community._model_queue[-1].age, self._community._x
#                sys.stdout.flush()
                yield 10.0 # seconds

        yield 1.0


    def load_database(self):
        """
        Load the whole dataset.
        """
        fname = self._kargs["database"]
        eval_data = []

        member_name = self._kargs["hardcoded_member"]
        num_peers = int(self._kargs["num_peers"])
        mid = int(member_name[1:]) - 1 # 0-indexed

        
        # TODO:
        # if mid >= dblen:
        #       id %= dblen

        self._community._x = []
        self._community._y = []

        num = 0
        with open("experiment/db/%s_train.dat" % fname) as f:
            for line in f:
                # Choose every midth instance, modulo num_peers.
                if num % num_peers == mid:
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

                    self._community._x.append(x2)
                    self._community._y.append(y)
                num += 1

        if __debug__:
            dprint("Instances picked: %d" % len(self._community._x))

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

        self._eval_database = eval_data

    def predict(self):
        """
        Predicts on the whole dataset and outputs the results for further analysis.
        """
        mae = 0
        for (x, y) in self._eval_database:
            ypred = int(self._community._model_queue[-1].predict(x))
            # 0-1 error
            if ypred != y:
                mae += 1
#            print y, ypred, y!=ypred
        mae /= 1.0 * len(self._eval_database)
#        print "#"*10

        return mae

