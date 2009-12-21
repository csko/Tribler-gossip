# Written by Njaal Borch
# see LICENSE.txt for license information

#
# Arno TODO: Merge with Core/Statistics/Status/*
#

import time
import sys

import urllib
import httplib

import XmlPrinter
import xml.dom.minidom

import Status
class LivingLabPeriodicReporter(Status.PeriodicStatusReporter):
    """
    This reporter creates an XML report of the status elements
    that are registered and sends them using an HTTP Post at
    the given interval.  Made to work with the P2P-Next lab.
    """
    
    host = "p2pnext-statistics.comp.lancs.ac.uk"
    path = "/testpost/"
    num_reports = 0
    
    def __init__(self, name, frequency, id, error_handler=None):
        Status.PeriodicStatusReporter.__init__(self, name, frequency, error_handler)
        self.device_id = id


    def newElement(self, doc, name, value):
        """
        Helper function to save some lines of code
        """

        element = doc.createElement(name)
        value = doc.createTextNode(str(value))
        element.appendChild(value)
        
        return element
        
    def report(self):
        """
        Create the report in XML and send it
        """

        # Create the report
        doc = xml.dom.minidom.Document()
        root = doc.createElement("nextsharedata")
        doc.appendChild(root)
        
        # Create the header
        header = doc.createElement("header")
        root.appendChild(header)
        header.appendChild(self.newElement(doc, "deviceid", self.device_id))
        header.appendChild(self.newElement(doc, "timestamp",
                                           long(round(time.time()))))
        
        version = "cs_v1b"
        header.appendChild(self.newElement(doc, "swversion", version))
        

        elements = self.get_elements()
        if len(elements) > 0:
        
            # Now add the status elements
            if len(elements) > 0:
                report = doc.createElement("event")
                root.appendChild(report)

                report.appendChild(self.newElement(doc, "attribute", "statusreport"))
                report.appendChild(self.newElement(doc, "timestamp",
                                                   long(round(time.time()))))
                for element in elements:
                    print element.__class__
                    report.appendChild(self.newElement(doc,
                                                       element.get_name(),
                                                       element.get_value()))

        events = self.get_events()
        if len(events) > 0:
            for event in events:
                report = doc.createElement(event.get_type())
                root.appendChild(report)
                report.appendChild(self.newElement(doc, "attribute", event.get_name()))
                if event.__class__ == Status.EventElement:
                    report.appendChild(self.newElement(doc, "timestamp", event.get_time()))
                elif event.__class__ == Status.RangeElement:
                    report.appendChild(self.newElement(doc, "starttimestamp", event.get_start_time()))
                    
                    report.appendChild(self.newElement(doc, "endtimestamp", event.get_end_time()))
                for value in event.get_values():
                    report.appendChild(self.newElement(doc, "value", value))            

        if len(elements) == 0 and len(events) == 0:
            return # Was nothing here for us
        
        # all done
        xml_printer = XmlPrinter.XmlPrinter(root)
        print >>sys.stderr, xml_printer.to_pretty_xml()
        xml_str = xml_printer.to_xml()

        # Now we send this to the service using a HTTP POST
        self.post(xml_str)

    def post(self, xml_str):
        """
        Post a status report to the living lab using multipart/form-data
        This is a bit on the messy side, but it does work
        """

        #print >>sys.stderr, xml_str
        
        self.num_reports += 1
        
        boundary = "------------------ThE_bOuNdArY_iS_hErE_$"
        headers = {"Host":self.host,
                   "User-Agent":"NextShare status reporter 2009.4",
                   "Content-Type":"multipart/form-data; boundary=" + boundary}

        base = ["--" + boundary]
        base.append('Content-Disposition: form-data; name="NextShareData"; filename="NextShareData"')
        base.append("Content-Type: text/xml")
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
        
        errcode, errmsg, headers = h.getreply()
        #print errcode,errmsg
        
        if errcode != 200:
            if self.error_handler:
                try:
                    self.error_handler(errcode, h.file.read())
                except Exception,e:
                    pass
            else:
                print >>sys.stderr, "Error posting but no error handler:", errcode, h.file.read()
        

if __name__ == "__main__":
    """
    Small test routine to check an actual post (unittest checks locally)
    """

    status = Status.get_status_holder("UnitTest")
    def error_handler(code, message):
        print "Error:",code,message
    reporter = LivingLabPeriodicReporter("Living lab test reporter", 1.0, error_handler)
    status.add_reporter(reporter)
    s = status.create_status_element("TestString", "A test string")
    s.set_value("Hi from Njaal")

    time.sleep(2)

    print "Stopping reporter"
    reporter.stop()

    print "Sent %d reports"%reporter.num_reports
