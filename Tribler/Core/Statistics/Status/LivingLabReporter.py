# Written by Njaal Borch
# see LICENSE.txt for license information

import sys
import time
import types
import urllib
import base64
import httplib
import xml.dom.minidom

import cStringIO
import gzip

import Status

STRESSTEST = False
DEBUG = False

class LivingLabReporter:
    """
    This reporter provides the two methods report and post that create
    an XML report of the status elements that are registered and sends
    them using an HTTP Post.

    This class should not be used directly. Instead use the
    LivingLabOnChangeReporter or LivingLabPeriodicReporter.
    """

    host = "p2pnext-statistics.comp.lancs.ac.uk"
    path = "/post/"
    num_reports = 0

    # host = "reporter1.tribler.org"
    # path = "/mirror-post.py"

    def __init__(self):
        self._permid = "anonymous"
        self._version = "-unknown-version-"

    def set_permid(self, permid):
        self._permid = permid

    def set_version(self, version):
        self._version = version

    def newElement(self, doc, name, value):
        """
        Helper function to add a XML entry called NAME with VALUE to the
        document tree DOC.

        When VALUE is a list, tuple, or a dictionary, the subitems are
        added recursively.
        """
        element = doc.createElement(name)

        # populate the element with items from a list?
        if type(value) in (types.GeneratorType, types.ListType, types.TupleType):
            for v in value:
                # each element v in value will be stored in a
                # container called <item>
                element.appendChild(self.newElement(doc, "item", v))
            # n = 0
            # for v in value:
            #     # name the container "n<number>" because the container
            #     # name can not start with a decimal
            #     element.appendChild(self.newElement(doc, "n%d" % n, v))
            #     n += 1

        # populate the element with items from a dictionary?
        elif type(value) is types.DictionaryType:
            for k, v in value.iteritems():
                # name the container "k<key>" because the container
                # name can not start with a decimal
                element.appendChild(self.newElement(doc, "k%s" % k, v))

        # populate the element with items from a string?
        elif type(value) in (types.StringType, types.UnicodeType):
            # use <element>VALUE</element> format
            element.appendChild(doc.createTextNode(value))

            # use <element value=VALUE/> format
            #element.setAttribute("value", value)

        # populate the element from a primitive (int, float, etc.)
        else:
            # use <element>VALUE</element> format
            element.appendChild(doc.createTextNode(str(value)))

            # use <element value=VALUE/> format
            # element.setAttribute("value", str(value))

        return element

    def report(self, element=None):
        """
        Create the report in XML and send it

        ELEMENT is an optional element to report. When none are given
        all available elements are reported.
        """

        if element:
            elements = [element]
        else:
            elements = self.elements

        if len(elements) == 0:
            return 
        
        # Create the report
        doc = xml.dom.minidom.Document()
        root = doc.createElement("nextsharedata")
        doc.appendChild(root)

        # Create the header
        header = doc.createElement("header")
        root.appendChild(header)

        header.appendChild(self.newElement(doc, "deviceid", base64.b64encode(self._permid)))
        header.appendChild(self.newElement(doc, "timestamp", long(round(time.time()))))
        header.appendChild(self.newElement(doc, "report", self.get_name()))
        header.appendChild(self.newElement(doc, "swversion", self._version))

        # set an element to identify this report for stress testing
        if STRESSTEST:
            header.appendChild(self.newElement(doc, "stresstest", True))
        
        # Now add the status elements
        report = doc.createElement("event")
        root.appendChild(report)

        report.appendChild(self.newElement(doc, "attribute", "statusreport"))
        report.appendChild(self.newElement(doc, "timestamp", long(round(time.time()))))
        for element in elements:
            report.appendChild(self.newElement(doc, element.get_name(), element.get_value()))

        # all done
        # import XmlPrinter
        # xml_printer = XmlPrinter.XmlPrinter(root)
        # xml_str = xml_printer.to_pretty_xml()
        # xml_str = xml_printer.to_xml()

        instruction = u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        # xml_str = instruction + u"\n" + root.toprettyxml(encoding="UTF-8")
        xml_str = instruction + root.toxml(encoding="UTF-8")

        # Now we send this to the service using a HTTP POST
        self.post(xml_str)

        # required for stress test
        return xml_str

    @staticmethod
    def compress(s):
        zbuf = cStringIO.StringIO()
        zfile = gzip.GzipFile(mode="wb", fileobj=zbuf, compresslevel=9)
        zfile.write(s)
        zfile.close()
        return zbuf.getvalue()

    def post(self, xml_str):
        """
        Post a status report to the living lab using multipart/form-data
        This is a bit on the messy side, but it does work
        """
        if DEBUG:
            uncompressed_xml_length = len(xml_str)

        self.num_reports += 1
        
        boundary = "------------------ThE_bOuNdArY_iS_hErE_$"
        headers = {"Host":self.host,
                   "User-Agent":"NextShare status reporter 2009.4",
                   "Content-Type":"multipart/form-data; boundary=" + boundary}

        base = ["--" + boundary]
        base.append('Content-Disposition: form-data; name="NextShareData"; filename="NextShareData"')
        base.append("Content-Type: text/xml")

        # compress xml
        xml_str = self.compress(xml_str)
        base.append("Content-Encoding: gzip")

        base.append("")
        base.append(xml_str)
        base.append("--" + boundary + "--")
        base.append("")
        base.append("")
        body = "\r\n".join(base)
        
        h = httplib.HTTP(self.host)
        h.putrequest("POST", self.path)
        h.putheader("Host",self.host)
        h.putheader("User-Agent","NextShare status reporter 2009.4")
        h.putheader("Content-Type", "multipart/form-data; boundary=" + boundary)
        h.putheader("content-length",str(len(body)))
        h.endheaders()
        h.send(body)

        if DEBUG:
            print >> sys.stderr, "***"
            print >> sys.stderr, "LivingLabReporter: post() Sending", uncompressed_xml_length, "bytes of xml data in a +/-", len(body), "bytes post"
            filename = "report-%d.xml" % time.time()
            open(filename, "w").write(body)
            print >> sys.stderr, "Report stored locally in file", filename
            print >> sys.stderr, "***"
        
        errcode, errmsg, headers = h.getreply()
        if DEBUG:
            # print >>sys.stderr, "LivingLabReporter:\n", xml_str
            print >>sys.stderr, "LivingLabReporter:", `errcode`, `errmsg`, "\n", headers, "\n", h.file.read().replace("\\n", "\n")

        if errcode != 200:
            if not self.error_handler is None:
                try:
                    self.error_handler(errcode, h.file.read())
                except Exception,e:
                    pass

class LivingLabOnChangeReporter(LivingLabReporter, Status.OnChangeStatusReporter):
    """
    This reporter creates an XML report of the status elements that
    are registered and sends them using an HTTP Post whenever an
    element changes. Made to work with the P2P-Next lab.
    """
    def __init__(self, name, error_handler=None):
        LivingLabReporter.__init__(self)
        Status.OnChangeStatusReporter.__init__(self, name, error_handler=error_handler)

class LivingLabPeriodicReporter(LivingLabReporter, Status.PeriodicStatusReporter):
    """
    This reporter creates an XML report of the status elements
    that are registered and sends them using an HTTP Post at
    the given interval.  Made to work with the P2P-Next lab.
    """
    pass

if __name__ == "__main__":
    """
    Small test routine to check an actual post (unittest checks locally)
    """

    def unittest():
        status = Status.get_status_holder("UnitTest")
        def error_handler(code, message):
            print "Error:",code,message
        reporter = LivingLabPeriodicReporter("Living lab test reporter", 1.0, error_handler)
        status.add_reporter(reporter)
        s = status.create_status_element("TestString", "A test string")
        s.set_value("Hi from Njaal")
        s = status.create_status_element("TestEscaping", "A string with quotes")
        s.set_value("...\"foo\"...'bar'...")
        s = status.create_status_element("TestMultiline", "A multiline string")
        s.set_value("Line 1\nLine2\nLine3")
        s = status.create_status_element("TestUnicode", "A unicode string")
        s.set_value(u"\xc4")

        time.sleep(2)

        print "Stopping reporter"
        reporter.stop()

        print "Sent %d reports"%reporter.num_reports

    def stresstest():
        import random

        global STRESSTEST
        STRESSTEST = True

        class LivingLabOnChangeCacheReporter(LivingLabOnChangeReporter):
            def __init__(self, *args, **kargs):
                LivingLabOnChangeReporter.__init__(self, *args, **kargs)
                self.__cache = None

            def report(self, *args, **kargs):
                if self.__cache is None:
                    self.__cache = LivingLabOnChangeReporter.report(self, *args, **kargs)
                else:
                    self.post(self.__cache)

        def error_handler(code, message):
            print "Error:",code

        def generate_dict():
            keys = ("Foo", "Bar", "Moo", "Milk")
            now = time.time()
            d = {}
            for i in xrange(1000):
                d[i] = (now + i, random.choice(keys), random.randint(1000, 99999))
            return d

        def stress(data, size, delay, repeat):
            reporter = LivingLabOnChangeCacheReporter("Living lab stress-test reporter", error_handler=error_handler)
            status = Status.get_status_holder("StressTest")
            status.add_reporter(reporter)
            s = status.create_status_element("TestMixed", "A mixed test width size %d" % size)
            start = time.time()
            sub_start = start
            for i in xrange(1, repeat+1):
                s.set_value(data)
                if not delay is None:
                    time.sleep(delay)

                if i % 100 == 0:
                    delta = time.time() - sub_start
                    print "Reported %5d times." % i, "%d bytes." % size, "%.2f MB/s." % (100*size / delta / 1024 / 1024), "%2.2f reports/s" % (100 / delta)
                    sub_start = time.time()
                
            delta = time.time() - start
            print "> Reported %5d times." % i, "%d bytes." % size, "%.2f MB/s." % (i*size / delta / 1024 / 1024), "%2.2f reports/s" % (i / delta)

        # reporter = LivingLabOnChangeReporter("Living lab stress-test reporter", error_handler=error_handler)
        # status = Status.get_status_holder("StressTest")
        # status.add_reporter(reporter)
        # s = status.create_status_element("TestString", "A string") # 303 bytes
        # s.set_value("Hello World!")
        # s = status.create_status_element("TestEscaping", "A simple list") # 678 bytes
        # s.set_value(range(25))
        # s = status.create_status_element("TestMultiline", "A complex dictionary") # 71213 bytes
        # s.set_value(generate_dict())

        data = generate_dict()
        stress(data, 71213, None, 100000)

    stresstest()
