# classes.py
# This file is part of PyBeanstream.
#
# Copyright(c) 2011 Benoit Clennett-Sirois. All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301  USA

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

API Notes:

Possible CVD responses:
    '1': 'CVD Match',
    '2': 'CVD Mismatch',
    '3': 'CVD Not Verified',
    '4': 'CVD Should have been present',
    '5': 'CVD Issuer unable to process request',
    '6': 'CVD Not Provided'


"""

from suds.client import Client
from suds.transport.http import HttpAuthenticated, HttpTransport
from suds.transport.https import HttpAuthenticated as Https
from xml.etree.ElementTree import Element, tostring
from xml_utils import xmltodict
import os.path
import urllib
import logging
import unicodedata
from datetime import date

WSDL_NAME = 'ProcessTransaction.wsdl'
WSDL_LOCAL_PREFIX = 'BeanStream'
WSDL_URL = 'https://www.beanstream.com/WebService/ProcessTransaction.asmx?WSDL'
API_RESPONSE_BOOLEAN_FIELDS = [
    'trnApproved',
    'avsProcessed',
    'avsPostalMatch',
    'avsAddrMatch',
    ]

# This defines the size forced by each field if fix_string_size is set
# to True when instantiating client.
SIZE_LIMITS = {
    'username': 16,
    'password': 16,
    'merchant_id': 9,
    'serviceVersion': 3, # Not specified, but 3 should work.
    'trnType': 3, # Doc says 2, but doesn't make sense. PAC len == 3.
    'trnCardOwner': 64,
    'trnCardNumber': 20,
    'trnCardCvd': 4,
    'trnExpMonth': 2,
    'trnExpYear': 2,
    'trnOrderNumber': 30,
    'trnAmount': 9,
    'ordEmailAddress': 64,
    'ordName': 64,
    'ordPhoneNumber': 32,
    'ordAddress1': 64,
    'ordAddress2': 64,
    'ordCity': 32,
    'ordProvince': 2,
    'ordPostalCode': 16,
    'ordCountry': 2,
    'termURL': None,
    'vbvEnabled': 1,
    'scEnabled': 1,
    'adjId': 12,
}

def strip_accents(s):
    """ Strips accents from string """
    if type(s) == str:
        s = s.decode('utf-8')
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

def fix_data(data):
    """ Strips accents from data dict strings"""
    for k in data.keys():
        d = data[k]
        if type(d) == unicode or type(d) == str:
            data[k] = strip_accents(d)
        elif type(d) == dict:
            data[k] = fix_data(d)
    return data

class BaseBeanClientException(Exception):
    """Exception Raised By the BeanClient"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)
    
class BeanUserError(BaseBeanClientException):
    """Error that's raised when the API responds with an error caused
    by the data entered by the user.
    It takes 2 parameters:
    -Field list separated by comas if multiple, eg: 'Field1,Field2'
    -Message list separated by comas if multiple, eg: 'Msg1,Msg2'
    """
    def __init__(self, field, messages):
        self.fields = field.split(',')
        self.messages = messages.split(',')
        e = "Field error with request: %s" % field
        super(BeanUserError, self).__init__(e)

class BeanSystemError(BaseBeanClientException):
    """This is raised when an error occurs on Beanstream's side. """
    def __init__(self, r):
        e = "Beanstream System Failure: %s" % r
        super(BeanSystemError, self).__init__(e)

class BeanResponse(object):
    def __init__(self, r, trans_type):
        # Turn dictionary values as object attributes.
        try:
            keys = r.keys()
        except AttributeError:
            raise(BaseBeanClientException("Unintelligible response content: %s" % str(r)))

        for k in keys:
            if k in API_RESPONSE_BOOLEAN_FIELDS:
                assert(r[k][0] in ['0', '1'])
                r[k] = r[k][0] == '1'
            else:
                r[k] = r[k][0]

        self.data = r
        
    def __getattr__(self, name):
        # This is to keep backwards compatibility, I recommend
        # using self.data dictionary, it's a waste to assign
        # all dictionary keys as object attibutes. THis will be
        # removed in the future.
        try:
            return self.data[name]
        except:
            raise AttributeError(name)        

class BeanClient(object):
    def __init__(
        self,
        username,
        password,
        merchant_id,
        service_version="1.3",
        storage='/tmp',
        download=False,
        fix_string_size=True,
        ):
        """
        This is used for client instatiation. Something fancy here:
        If you want to enable pre-auth complete transaction ('PAC'),
        the username and password you want to supply is not the same
        username and password that moneris assigned you. It's the username
        ans password you set-up in order settings in the Moneris control
        panel. See this (at the bottom):
        https://beanstreamsupport.pbworks.com/w/page/26445725/HASH-Validation-and-API-Passcodes
        If download is True, checks if WSDL file exists in local storage location with
        name WSDL_LOCAL_PREFIX + WSDL_NAME, else downloads
        it. Otherwise, will use remote file.
        'fix_string_size' parameter will automatically fix each string
        size to the documented length to avoid problems. If set to
        False, it will send the data regardless of string size.
        """

        # Settings config attributes
        self.fix_string_size = fix_string_size

        # Downloading if requested
        if download:
            p = '/'.join((storage, WSDL_LOCAL_PREFIX + WSDL_NAME))

            if not os.path.exists(p):
                self.download_wsdl(p)
            u = 'file://' + p
        else:
            u = WSDL_URL

        # Instantiate suds client objects.
        self.suds_client = Client(u)
        self.auth_data= {
            'username': username,
            'password': password,
            'merchant_id': merchant_id,
            'serviceVersion': service_version,
            }
        
    def download_wsdl(self, p, url=WSDL_URL):
        """ Downloads the wsdl file to local storage."""
        r = urllib.urlopen(url)
        if r.getcode() == 200:
            f = open(p, 'w')
            c = r.read()
            f.write(c)
            f.close()

    def process_transaction(self, service, data):
        """ Transforms data to a xml request, calls remote service
        with supplied data, processes errors and returns an dictionary
        with response data.
        """

        # Create XML tree
        t = Element('transaction')
        derp = {}
        for k in data.keys():
            val = data[k]
            # Fix data string size
            if self.fix_string_size:
                l = SIZE_LIMITS[k]
                if l:
                    val = val[:l]
            if val:
                derp[k] = data[k]
                e = Element(k)
                e.text = data[k]
                t.append(e)

        # Convert to string
        req = tostring(t)

        # Process transaction
        resp = getattr(self.suds_client.service,
                       service)(req)

        # Convert response
        r = xmltodict(resp)
        return r

    def check_for_errors(self, r):
        """This checks for errors and errs out if an error is
        detected.
        """
        data = r.data
        if 'messageText' in data:
            msg = data['messageText']
        else:
            msg = 'None'
        # Check for badly formatted  request error:
        if data['errorType'] == 'U':
            raise BeanUserError(data['errorFields'], msg)
        # Check for another error I haven't seen yet:
        elif data['errorType'] == 'S':
            raise BeanSystemError(msg)

    def purchase_base_request(self,
                              method,
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
                              term_url='',
                              vbv_enabled='0',
                              sc_enabled='0',
                              cust_address_line2='',
                              ):
        """Call this to create a Purchase. SecureCode / VerifiedByVisa
        is disabled by default.
        All data types should be strings. Year and month must be 2
        characters, if it's an integer lower than 10, format using
        %02d (eg: may should be "05")
        """
        service = 'TransactionProcess'

        transaction_data = {
            'trnType': method,
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
            'scEnabled': sc_enabled,
            }

        if cust_address_line2:
            transaction_data['ordAddress2'] = cust_address_line2

        transaction_data.update(self.auth_data)

        transaction_data = fix_data(transaction_data)

        response = BeanResponse(
            self.process_transaction(service, transaction_data),
            method)

        self.check_for_errors(response)

        return response

    def adjustment_base_request(self,
                              method,
                              amount,
                              order_num,
                              adj_id,
                              ):
        """Call this to create a Payment adjustment.
        All data types should be strings. Year and month must be 2
        characters, if it's an integer lower than 10, format using
        %02d (eg: may should be "05")
        """

        service = 'TransactionProcess'

        transaction_data = {
            'trnType': method,
            'trnOrderNumber': order_num,
            'trnAmount': amount,
            'adjId': adj_id,
            }

        transaction_data.update(self.auth_data)

        transaction_data = fix_data(transaction_data)

        response = BeanResponse(
            self.process_transaction(service, transaction_data),
            method)

        self.check_for_errors(response)

        return response

    def purchase_request(self, *a, **kw):
        """Call this to create a Purchase. SecureCode / VerifiedByVisa
        is disabled by default.
        All data types should be strings. Year and month must be 2
        characters, if it's an integer lower than 10, format using
        %02d (eg: may should be "05")
        """
        method='P'
        return self.purchase_base_request(method, *a, **kw)

    def preauth_request(self, *a, **kw):
        """This does a pre-authorization request.
        """
        #raise NotImplemented('This is not a complete feature.')
        method='PA'
        return self.purchase_base_request(method, *a, **kw)

    def complete_request(self, *a, **kw):
        """This does a pre-auth complete request.
        """
        #raise NotImplemented('This is not a complete feature.')
        method='PAC'
        return self.adjustment_base_request(method, *a, **kw)
