"""
Right now this only support Purchase transactions.
Dependencies: suds
Example usage:

from beanstream.classes import BeanClient

d = ('John Doe',
     '371100001000131',
     '1234',
     '05',
     '15',
     '10.00',
     '123456789',
     'john.doe@pranana.com',
     'John Doe',
     '5145555555',
     '88 Mont-Royal Est',
     'Montreal',
     'QC',
     'H2T1N6',
     'CA'
     )

b = BeanClient('MY_USERNAME',
               'MY_PASSWORD',
               'MY_MERCHANT_ID')

response = b.purchase_request(*d)

assert(response['trnApproved'] == '1')

"""

from suds.client import Client
from suds.transport.http import HttpAuthenticated, HttpTransport
from suds.transport.https import HttpAuthenticated as Https
from xml.etree.ElementTree import Element, tostring
from xml_utils import xmltodict
import os.path
import urllib
import logging
from datetime import date

WSDL_NAME = 'ProcessTransaction.wsdl'
WSDL_LOCAL_PREFIX = 'BeanStream'
WSDL_URL = 'http://www.beanstream.com/soap/ProcessTransaction.wsdl'
CVD_ERRORS = {
    '2': 'CVD Mismatch',
    '3': 'CVD Not Verified',
    '4': 'CVD Should have been present',
    '5': 'CVD Issuer unable to process request',
    '6': 'CVD Not Provided'
    }

def flatten_dict(d):
    """This transforms a dictionary in the format of {'k': ['v',]} to
    {'k': 'v'}
    To do: Can this be simplified with map?
    """

    n = {}
    for k in d.keys():
        n[k] = d[k][0]
    return n

class BaseBeanClientException(Exception):
    """Exception Raised By the BeanClient"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
    
class BeanDownloadError(BaseBeanClientException):
    def __init__(self, url):
        e = "Wrong status code when trying to get WSDL file at: %s"
        super(BeanDownloadError, self).__init__(e % url)

class BeanRequestFieldError(BaseBeanClientException):
    """Error that's raised when the API responds with a field error.
    It takes 2 parameters:
    -Field list separated by comas if multiple, eg: 'Field1,Field2'
    -Message list separated by comas if multiple, eg: 'Msg1,Msg2'
    """

    def __init__(self, field, messages):
        self.fields = field.split(',')
        self.messages = messages.split(',')
        e = "Field error with request: %s" % field
        super(BeanRequestFieldError, self).__init__(e)

class BeanBadRequest(BaseBeanClientException):
    def __init__(self):
        e = "Request Failure"
        super(BeanBadRequest, self).__init__(e)

class BeanCVDError(BaseBeanClientException):
    def __init__(self, cvd_id, err):
        e = "CVD Failure: %s" % err
        self.cvd_id = cvd_id
        super(BeanCVDError, self).__init__(e)

class BeanRequestFailure(BaseBeanClientException):
    def __init__(self, err):
        e = "Request Failed: %s " % err
        super(BeanRequestFailure, self).__init__(e)

class BeanUnimplementedError(BaseBeanClientException):
    def __init__(self, feature):
        e = "This feature is not implemented: %s" % feature
        super(BeanUnimplementedError, self).__init__(e)

class BeanClient(object):
    def __init__(self,
                 username,
                 password,
                 merchant_id,
                 service_version="1.2",
                 storage='/tmp'):
        """ Checks if WSDL file exists in local storage location with
        name WSDL_LOCAL_PREFIX + WSDL_NAME, else downloads it."""

        p = '/'.join((storage, WSDL_LOCAL_PREFIX + WSDL_NAME))

        if not os.path.exists(p):
            self.download_wsdl(p)

        # Instantiate suds client objects.
        u = 'file://' + p
        self.suds_client = Client(u)
        self.auth_data= {
            'username': username,
            'password': password,
            'merchant_id': merchant_id,
            'serviceVersion': service_version
            }

    def download_wsdl(self, p):
        """ Downloads the wsdl file to local storage."""

        r = urllib.urlopen(WSDL_URL)
        if r.getcode() == 200:
            f = open(p, 'w')
            c = r.read()
            f.write(c)
            f.close()
        else:
            raise BeanDownloadError(WSDL_URL)

    def process_transaction(self, service, data):
        """ Transforms data to a xml request, calls remote service
        with supplied data, processes errors and returns an dictionary
        with response data."""

        t = Element('transaction')
        
        for k in data.keys():
            val = data[k]
            if val:
                e = Element(k)
                e.text = data[k]
                t.append(e)

        r = xmltodict(getattr(self.suds_client.service,
                              service)(tostring(t)))

        r = flatten_dict(r)

        self.check_for_errors(r)

        return r

    def check_for_errors(self, r):
        """This checks for errors and errs out if an error is
        detected.
        """

        # Check for badly formatted  request error:
        if r['errorType'] == 'U':
            raise BeanRequestFieldError(r['errorFields'],
                                        r['messageText'])
        # Check for another error I haven't seen yet:
        elif r['errorType'] == 'S':
            raise BeanBadRequest()

        # Check for normal response:
        elif r['errorType'] == 'N':
            if r['trnApproved'] == '1':
                return None
            elif r['cvdId'] != 1:
                raise BeanCVDError(CVD_ERRORS[r['cvdId']], CVD_ERRORS[r['messageText']])
            else:
                raise BaseBeanClientException('Transaction not approved not sure why')

        # Any other error (Shouldn't happen)
        else:
            raise BaseBeanClientException('This should not be raised.')

    def purchase_request(self,
                         cc_owner_name,
                         cc_num,
                         cc_cvv,
                         cc_exp_month,
                         cc_exp_year,
                         amount,
                         order_num,
                         cust_email,
                         cust_name,
                         cust_phone,
                         cust_address_line1,
                         cust_city,
                         cust_province,
                         cust_postal_code,
                         cust_country,
                         term_url=None,
                         vbv_enabled='0',
                         sc_enabled='0',
                         cust_address_line2=None,
                         ):
        """Call this to create a Purchase. SecureCode / VerifiedByVisa
        is disabled by default.
        """

        service = 'TransactionProcess'

        transaction_data = {
            'trnType': 'P',
            'trnCardOwner': cc_owner_name,
            'trnCardNumber': cc_num,
            'trnCardCvd': cc_cvv,
            'trnExpMonth': cc_exp_month,
            'trnExpYear': cc_exp_year,
            'trnOrderNumber': order_num,
            'trnAmount': amount,
            'ordEmailAddress': cust_email,
            'ordName': cust_name,
            'ordPhoneNumber': cust_phone,
            'ordAddress1': cust_address_line1,
            'ordAddress2': ' ',
            'ordCity': cust_city,
            'ordProvince': cust_province,
            'ordPostalCode': cust_postal_code,
            'ordCountry': cust_country,
            'termURL': term_url,
            'vbvEnabled': vbv_enabled,
            'scEnabled': sc_enabled
            }

        if cust_address_line2:
            transaction_data['ordAddress2'] = cust_address_line2

        transaction_data.update(self.auth_data)

        response = self.process_transaction(service, transaction_data)

        return response
