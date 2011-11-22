#
# python Tribler/Main/dispersy.py --script gossiplearningframework-generate-messages
#
# Ensure that the files experiment/gossip_ec_private_key and
# experiment/gossip_ec_master_private_key are available
#

from hashlib import sha1
from time import time
from os.path import expanduser

from community import GossipLearningCommunity

from Tribler.Core.dispersy.resolution import PublicResolution
from Tribler.Core.dispersy.crypto import ec_to_private_bin, ec_from_private_pem
from Tribler.Core.dispersy.script import ScriptBase
from Tribler.Core.dispersy.member import MyMember, Member
from Tribler.Core.dispersy.dprint import dprint

hardcoded_member_public_keys = {'M1': 'x'}

class SetupScript(ScriptBase):
    def run(self):
        self._start_time = time()
        self.caller(self.setup)
        self.caller(self.sync)
        self.caller(self.check_master_identity)
        self.caller(self.check_permissions)
        self.caller(self.check_my_member_identity)

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
            pem = open(expanduser("experiment/gossip_ec_private_key_%s" % member_name), "r").read()
            ec = ec_from_private_pem(pem)
            private_key = ec_to_private_bin(ec)
            my_member = MyMember(hardcoded_public_key, private_key)

            # obtain the master_private_key for the master_member from disk
            pem = open(expanduser("experiment/gossip_ec_master_private_key"), "r").read()
            ec = ec_from_private_pem(pem)
            master_private_key = ec_to_private_bin(ec)

            # insert entries in the dispersy database to join the community
            with self._dispersy_database as database:
                database.execute(u"INSERT INTO community (user, classification, cid, public_key) VALUES(?, ?, ?, ?)", (my_member.database_id, SimpleDispersyTestCommunity.get_classification(), buffer(SimpleDispersyTestCommunity.hardcoded_cid), buffer(SimpleDispersyTestCommunity.hardcoded_master_public_key)))
                database_id = self._dispersy_database.last_insert_rowid
                database.execute(u"INSERT INTO user (mid, public_key) VALUES(?, ?)", (buffer(SimpleDispersyTestCommunity.hardcoded_cid), buffer(SimpleDispersyTestCommunity.hardcoded_master_public_key)))
                database.execute(u"INSERT INTO key (public_key, private_key) VALUES(?, ?)", (buffer(SimpleDispersyTestCommunity.hardcoded_master_public_key), buffer(master_private_key)))
                database.execute(u"INSERT INTO candidate (community, host, port, incoming_time, outgoing_time) SELECT ?, host, port, incoming_time, outgoing_time FROM candidate WHERE community = 0", (database_id,))

            self._community = SimpleDispersyTestCommunity.load_community(SimpleDispersyTestCommunity.hardcoded_cid, SimpleDispersyTestCommunity.hardcoded_master_public_key)

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

class GenerateMessagesScript(SetupScript):
    def run(self):
        super(GenerateMessagesScript, self).run()
        self.caller(self.create_messages)

    def create_messages(self):
        """
        We will create a new last-1-subjective-sync message every 3 minutes.
        """
        while True:
            # create a new last-1-sync message every 6 minutes
            self._community.create_last_1_subjective_sync(u"last-1-subjective-sync; start:%f; at:%f; creator:%s" % (self._start_time, time(), self._community.my_member.mid.encode("HEX")))
            yield 60.0 * 3

        yield 1.0
