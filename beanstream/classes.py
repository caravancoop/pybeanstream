# Copyright(c) 1999 Benoit Clennett-Sirois
#
# Benoit Clennett-Sirois hereby disclaims all copyright interest in
# the program "PyBeanstream".
#
# This file is part of PyBeanstream.
#
# PyBeanstream is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyBeanstream is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyBeanstream.  If not, see http://www.gnu.org/licenses/

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
from datetime import date

WSDL_NAME = 'ProcessTransaction.wsdl'
WSDL_LOCAL_PREFIX = 'BeanStream'
WSDL_URL = 'http://www.beanstream.com/soap/ProcessTransaction.wsdl'
API_RESPONSE_BOOLEAN_FIELDS = [
    'trnApproved',
    'avsProcessed',
    'avsPostalMatch',
    'avsAddrMatch',
    ]

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
        for k in r.keys():
            if k in API_RESPONSE_BOOLEAN_FIELDS:
                assert(r[k][0] in ['0', '1'])
                setattr(self, k, r[k][0] == '1')
            else:
                setattr(self, k, r[k][0])

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

        return r

    def check_for_errors(self, r):
        """This checks for errors and errs out if an error is
        detected.
        """
        # Check for badly formatted  request error:
        if r.errorType == 'U':
            raise BeanUserError(r.errorFields,
                                r.messageText)
        # Check for another error I haven't seen yet:
        elif r.errorType == 'S':
            raise BeanSystemError(str(r))


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
                              term_url=None,
                              vbv_enabled='0',
                              sc_enabled='0',
                              cust_address_line2=None,
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

        response = BeanResponse(
            self.process_transaction(service, transaction_data),
            method)

        self.check_for_errors(response)

        return response

    def adjustment_base_request(self,
                              method,
                              cc_owner_name,
                              cc_num,
                              cc_cvv,
                              cc_exp_month,
                              cc_exp_year,
                              amount,
                              order_num,
                              adj_id,
                              hash_value=None,
                              hash_expiry=None,
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
            'adjId': adj_id,
            }

        if hash_value:
            transaction_data['hashValue'] = hash_value
            
        if hash_expiry:
            transaction_data['hashExpiry'] = hash_expiry
            
        transaction_data.update(self.auth_data)

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
        raise NotImplemented('This is not a complete feature.')
        method='PA'
        return self.purchase_base_request(method, *a, **kw)

    def complete_request(self, *a, **kw):
        """This does a pre-auth complete request.
        """
        raise NotImplemented('This is not a complete feature.')
        method='PAC'
        return self.adjustment_base_request(method, *a, **kw)
