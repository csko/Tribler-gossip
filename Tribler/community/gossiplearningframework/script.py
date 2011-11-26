#
# python Tribler/Main/dispersy.py --script gossiplearningframework-observe
#
# Ensure that the files experiment/gossip_ec_private_key and
# experiment/gossip_ec_master_private_key are available.
#

from hashlib import sha1
from time import time
from os.path import expanduser

from community import GossipLearningCommunity

from Tribler.Core.dispersy.resolution import PublicResolution
from Tribler.Core.dispersy.crypto import ec_to_private_bin, ec_from_private_pem, ec_from_public_pem, ec_to_public_bin
from Tribler.Core.dispersy.script import ScriptBase
from Tribler.Core.dispersy.member import MyMember, Member
from Tribler.Core.dispersy.dprint import dprint

hardcoded_member_public_keys = {}

# Load the hardcoded member public keys
NUMPEERS=100

for i in range(1, NUMPEERS+1):
    pem = open(expanduser("experiment/keys/public_M%05d.pem" % i), "r").read()
    ec = ec_from_public_pem(pem)
    hardcoded_member_public_keys['M%d' % i] = ec_to_public_bin(ec)

class SetupScript(ScriptBase):
    def run(self):
        self._start_time = time()
        self.caller(self.setup)
        self.caller(self.sync)
#        self.caller(self.check_master_identity)
#        self.caller(self.check_permissions)
#        self.caller(self.check_my_member_identity)

    def setup(self):
        """
        We either need to join the community or semi-create one.
        """
        # we will use the below member identifier to create messages for our test.  the private key
        # can be found on disk, but will not be submitted to SVN for obvious reasons
        assert "hardcoded_member" in self._kargs, ("give --script-args hardcoded_member=MEMBER", self._kargs)
        assert self._kargs["hardcoded_member"] in hardcoded_member_public_keys, "give --script-args hardcoded_member=MEMBER"

        member_name = self._kargs["hardcoded_member"]
        hardcoded_public_key = hardcoded_member_public_keys[member_name]
        hardcoded_mid = sha1(hardcoded_public_key).digest()

        try:
            dprint("load_hardcoded_community")
            self._community = GossipLearningCommunity.load_hardcoded_community()

        except ValueError, e:
            dprint("failed to load; joining instead [", e, "]")
            # COPIED FROM dispersy/community.py:create_community.  IF ANYTHING CHANGES THERE IT
            # NEEDS TO BE REFLECTED HERE ASWELL

            # obtain the hardcoded_private_key for my_member from disk
            pem = open(expanduser("experiment/keys/public_M%05d.pem" % i), "r").read()
            ec = ec_from_private_pem(pem)
            private_key = ec_to_private_bin(ec)
            my_member = MyMember(hardcoded_public_key, private_key)

            # obtain the master_private_key for the master_member from disk
            pem = open(expanduser("experiment/gossip_ec_master_private_key"), "r").read()
            ec = ec_from_private_pem(pem)
            master_private_key = ec_to_private_bin(ec)

            # insert entries in the dispersy database to join the community
            with self._dispersy_database as database:
                database.execute(u"INSERT INTO community (user, classification, cid, public_key) VALUES(?, ?, ?, ?)", (my_member.database_id, GossipLearningCommunity.get_classification(), buffer(GossipLearningCommunity.hardcoded_cid), buffer(GossipLearningCommunity.hardcoded_master_public_key)))
                database_id = self._dispersy_database.last_insert_rowid
                database.execute(u"INSERT INTO user (mid, public_key) VALUES(?, ?)", (buffer(GossipLearningCommunity.hardcoded_cid), buffer(GossipLearningCommunity.hardcoded_master_public_key)))
                database.execute(u"INSERT INTO key (public_key, private_key) VALUES(?, ?)", (buffer(GossipLearningCommunity.hardcoded_master_public_key), buffer(master_private_key)))
                database.execute(u"INSERT INTO candidate (community, host, port, incoming_time, outgoing_time) SELECT ?, host, port, incoming_time, outgoing_time FROM candidate WHERE community = 0", (database_id,))

            self._community = GossipLearningCommunity.load_community(GossipLearningCommunity.hardcoded_cid, GossipLearningCommunity.hardcoded_master_public_key)

        yield 1.0

    def sync(self):
        """
        Perform a few sync cycles, if we end up creating new identity messages this will increase
        the chance that they will not clash.
        """
        sync_meta = self._community.get_meta_message(u"dispersy-sync")
        wait = 10
        for i in xrange(1, wait + 1):
            messages = [sync_meta.implement(sync_meta.authentication.implement(self._community.my_member),
                                            sync_meta.distribution.implement(self._community.global_time),
                                            sync_meta.destination.implement(),
                                            sync_meta.payload.implement(time_low, time_high, bloom_filter))
                        for time_low, time_high, bloom_filter
                        in self._community.dispersy_sync_bloom_filters]
            self._dispersy.store_update_forward(messages, False, False, True)
            dprint("syncing. ", i, "/", wait, "...")
            yield 1.0
        yield 1.0

    def check_master_identity(self):
        """
        The dispersy-identity message for the master member may already exist.  If we can't find it,
        we can create it.
        """
        meta = self._community.get_meta_message(u"dispersy-identity")
        wait = 30
        for i in xrange(1, wait + 1):
            try:
                self._dispersy_database.execute(u"SELECT id FROM sync WHERE community = ? AND user = ? AND name = ?",
                                                (self._community.database_id, self._community.master_member.database_id, meta.database_id)).next()

            except StopIteration:
                pass

            else:
                dprint("dispersy-identity for the master member is available")
                break

            dprint("requesting dispersy-identity for the master member.  ", i, "/", wait, "...")
            addresses = [candidate.address for candidate in self._dispersy.yield_mixed_candidates(self._community, 10)]
            self._dispersy.create_identity_request(self._community, self._community.master_member.mid, addresses)
            yield 1.0

        else:
            dprint("creating first (or new) dispersy-identity for the master member")
            message = meta.implement(meta.authentication.implement(self._community.master_member),
                                     meta.distribution.implement(self._community.claim_global_time()),
                                     meta.destination.implement(),
                                     meta.payload.implement(("0.0.0.0", 0)))
            self._community.dispersy.store_update_forward([message], True, False, True)

        yield 1.0

    def check_permissions(self):
        """
        One or more dispersy-authorize messages are required to allow my member to create the
        messages for the test.  If we can not obtain the authorize messages we will create them.
        """
        metas = [self._community.get_meta_message(u"last-1-subjective-sync"), self._community.get_meta_message(u"dispersy-destroy-community")]
        sync_meta = self._community.get_meta_message(u"dispersy-sync")
        wait = 30
        for i in xrange(1, wait + 1):
            allowed, proofs = self._community._timeline._check(self._community.my_member, self._community.global_time, [(meta, u"permit") for meta in metas])
            if allowed:
                dprint("my member is allowed to create messages")
                break

            messages = [sync_meta.implement(sync_meta.authentication.implement(self._community.my_member),
                                            sync_meta.distribution.implement(self._community.global_time),
                                            sync_meta.destination.implement(),
                                            sync_meta.payload.implement(time_low, time_high, bloom_filter))
                        for time_low, time_high, bloom_filter
                        in self._community.dispersy_sync_bloom_filters]
            self._dispersy.store_update_forward(messages, False, False, True)
            dprint("syncing. ", i, "/", wait, "...")
            yield 1.0

        else:
            # Used in the 3.5.8 and 3.5.9 test
            #
            # dprint("creating authorizations")
            # permission_triplets = []
            # for message in self._community.get_meta_messages():
            #     if not isinstance(message.resolution, PublicResolution):
            #         for allowed in (u"authorize", u"revoke", u"permit"):
            #             permission_triplets.append((self._community.my_member, message, allowed))
            # if permission_triplets:
            #     self._community.create_dispersy_authorize(permission_triplets, sign_with_master=True)

            wait = 30
            for i in xrange(1, wait + 1):
                dprint("checking for permissions on disk. ", i, "/", wait, "...")
                try:
                    packet = open(expanduser("~/simpledispersytest_permission_packet"), "r").read()
                except:
                    yield 1.0
                else:
                    dprint("use existing permissions from disk")
                    self._community.dispersy.on_incoming_packets([(("130.161.158.222", 6711), packet)])
                    break
            else:
                dprint("creating authorizations")
                permission_triplets = []
                for message in self._community.get_meta_messages():
                    if not isinstance(message.resolution, PublicResolution):
                        for allowed in (u"authorize", u"revoke", u"permit"):
                            for public_key in hardcoded_member_public_keys.itervalues():
                                permission_triplets.append((Member.get_instance(public_key), message, allowed))
                if permission_triplets:
                    message = self._community.create_dispersy_authorize(permission_triplets, sign_with_master=True)
                    open(expanduser("~/simpledispersytest_permission_packet"), "w+").write(message.packet)

        yield 1.0

    def check_my_member_identity(self):
        """
        The dispersy-identity message for my member may already exist.  If we can't find it, we can
        create it.
        """
        meta = self._community.get_meta_message(u"dispersy-identity")
        wait = 30
        for i in xrange(1, wait + 1):
            try:
                self._dispersy_database.execute(u"SELECT id FROM sync WHERE community = ? AND user = ? AND name = ?",
                                                (self._community.database_id, self._community.my_member.database_id, meta.database_id)).next()

            except StopIteration:
                pass

            else:
                dprint("dispersy-identity for my member is available")
                break

            dprint("requesting dispersy-identity for my member.  ", i, "/", wait, "...")
            addresses = [candidate.address for candidate in self._dispersy.yield_mixed_candidates(self._community, 10)]
            self._dispersy.create_identity_request(self._community, self._community.my_member.mid, addresses)
            yield 1.0

        else:
            dprint("creating first (or new) dispersy-identity for my member")
            self._community.create_dispersy_identity()

        yield 1.0

# TODO: rename: SetupScript/ControllerScript/ExperimentScript?
# TODO: proper logging
# TODO: whole database should not be loaded into memory in this script
# TODO: only works on IRIS
class ObserverScript(SetupScript):
    def run(self):
        super(ObserverScript, self).run()
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
            print >>f, "# timestamp member_id age mae"
            while True:
                print >>f, int(time()), mid,
                print >>f, self._community._message.age, self.predict()
                f.flush()
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

                eval_data.append((x, y))

        with open("experiment/db/%s_eval.dat" % fname) as f:
            for line in f:
                x = {}

                vals = line[:-1].split()
                y = int(vals[0])
                vals = vals[1:]

                for i in vals:
                    k, v = i.split(":")
                    x[int(k)] = float(v)

                train_data.append((x, y))

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

        # Suppose there are no missing values.
        self._community.x = []
        for k, v in sorted(data[0].items()):
            self._community.x.append(v)

        self._community.y = data[1]

        # Initialize the model also.
        self._community.w = [0 for i in range(len(self._community.x))]

        print "One instance picked."
        yield 1.0

    def predict(self):
        """
        Predicts on the whole dataset and outputs the results for further analysis.
        """
        mae = 0
        for (x, y) in self._eval_database:
            ypred = int(self._community.predict(x))
            # 0-1 error
            if ypred != y:
                mae += 1
        mae /= 1.0 * len(self._eval_database)

        return mae

