#!/usr/bin/env python2

from crypto import *
from crypto import _curves
import math
import time
import sys

D="experiment/keys/"
NUMKEYS=100
CURVE=u"very-low" # one of [u"very-low", u"low", u"medium", u"high"]

if __name__ == "__main__":
    def EC_name(curve):
        assert isinstance(curve, int)
        for name in dir(M2Crypto.EC):
            value = getattr(M2Crypto.EC, name)
            if isinstance(value, int) and value == curve:
                return name


    print "Generating keys ",
    for i in range(1,NUMKEYS+1):
        ec = ec_generate_key(CURVE)
        private_pem = ec_to_private_pem(ec)
        public_pem = ec_to_public_pem(ec)
        public_bin = ec_to_public_bin(ec)
        private_bin = ec_to_private_bin(ec)
        with open(D+"public_M%05d.pem" % i, "w") as f:
            print >>f, public_pem.strip()
        with open(D+"private_M%05d.pem" % i, "w") as f:
            print >>f, private_pem.strip()

#        print "pub:", len(public_bin), public_bin.encode("HEX")
#        print "prv:", len(private_bin), private_bin.encode("HEX")
#        print "pub-sha1", sha1(public_bin).digest().encode("HEX")
#        print "prv-sha1", sha1(private_bin).digest().encode("HEX")

        sys.stdout.write(".")
        if i % 50 == 0:
            print
            print "                ",
        sys.stdout.flush()

        ec2 = ec_from_public_pem(public_pem)
        assert ec_verify(ec2, "foo-bar", ec_sign(ec, "foo-bar"))
        ec2 = ec_from_private_pem(private_pem)
        assert ec_verify(ec2, "foo-bar", ec_sign(ec, "foo-bar"))
        ec2 = ec_from_public_bin(public_bin)
        assert ec_verify(ec2, "foo-bar", ec_sign(ec, "foo-bar"))
        ec2 = ec_from_private_bin(private_bin)
        assert ec_verify(ec2, "foo-bar", ec_sign(ec, "foo-bar"))

    print " Done."
