from suds.client import Client
from suds.transport.http import HttpAuthenticated, HttpTransport
from suds.transport.https import HttpAuthenticated as Https
from xml.etree.ElementTree import Element, tostring
from xml_utils import xmltodict
import os.path
import urllib
import logging

WSDL_NAME = 'ProcessTransaction.wsdl'

WSDL_LOCAL_PREFIX = 'BeanStream'

WSDL_URL = {
    'REMOTE': 'http://www.beanstream.com/soap/ProcessTransaction.wsdl',
    'LOCAL': 'file://%s%s%s'  # Format: % (storage, WSDL_LOCAL_PREFIX, WSDL_NAME)
    }

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

class BeanClient(object):
    def __init__(self,
                 username,
                 password,
                 merchant_id,
                 service_version="1.2",
                 storage='/tmp'):

        # Checks if WSDL file exists in local storage location with
        # name WSDL_LOCAL_PREFIX + WSDL_NAME, else downloads it.
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
        # Downloads the wsdl file to local storage.
        r = urllib.urlopen(WSDL_URL['REMOTE'])
        if r.getcode() == 200:
            f = open(p, 'w')
            c = r.read()
            f.write(c)
            f.close()
        else:
            raise BeanDownloadError(WSDL_URL['REMOTE'])

    def process_transaction(self, service, data):
        # Transforms data to a xml request, calls remote service with
        # supplied data, processes errors and returns an dictionary
        # with response data.
        t = Element('transaction')
        
        for k in data.keys():
            val = data[k]
            if val:
                e = Element(k)
                e.text = data[k]
                t.append(e)

        return xmltodict(getattr(self.suds_client.service, service)(tostring(t)))

    def purchase_request(self,
                         cc_owner_name,
                         cc_cvv,
                         cc_num,
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
