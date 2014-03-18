# Namespace declaration:
# client.py
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

import unicodedata
from suds.client import Client
from xml.etree.ElementTree import Element, tostring
from pybeanstream.xml_utils import xmltodict


WSDL_NAME = 'ProcessTransaction.wsdl'
WSDL_LOCAL_PREFIX = 'BeanStream'
WSDL_URL = 'https://www.beanstream.com/WebService/ProcessTransaction.asmx?WSDL'

API_RESPONSE_BOOLEAN_FIELDS = [
    'trnApproved',
    'avsProcessed',
    'avsPostalMatch',
    'avsAddrMatch',
    ]

# Default language for transactions. This is either FRE or ENG.
DEFAULT_LANG = 'ENG'

# This defines the size forced by each field if fix_string_size is set
# to True when instantiating client.
SIZE_LIMITS = {
    'username': 16,
    'password': 16,
    'merchant_id': 9,
    'serviceVersion': 3,  # Not specified, but 3 should work.
    'trnType': 3,  # Doc says 2, but doesn't make sense. PAC len == 3.
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
    'trnLanguage': 3,
}


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
            raise(
                BaseBeanClientException(
                    "Unintelligible response content: %s" % str(r)))

        for k in keys:
            if k in API_RESPONSE_BOOLEAN_FIELDS:
                assert(r[k][0] in ['0', '1'])
                r[k] = r[k][0] == '1'
            else:
                r[k] = r[k][0]

        self.data = r


class BeanClient(object):
    def __init__(self,
                 username,
                 password,
                 merchant_id,
                 service_version="1.3",
                 storage='/tmp',
                 fix_string_size=True,
                 wsdl_url=WSDL_URL):
        """
        'fix_string_size' parameter will automatically fix each string
        size to the documented length to avoid problems. If set to
        False, it will send the data regardless of string size.
        """

        # Settings config attributes
        self.fix_string_size = fix_string_size

        # Instantiate suds client objects.
        self.suds_client = Client(wsdl_url)
        self.suds_client.set_options(headers={
            'Content-Type': 'text/xml; charset=utf-8'
            })
        self.auth_data = {
            'username': username,
            'password': password,
            'merchant_id': merchant_id,
            'serviceVersion': service_version,
            }

    def process_transaction(self, service, data):
        """ Transforms data to a xml request, calls remote service
        with supplied data, processes errors and returns an dictionary
        with response data.
        """

        # Create XML tree
        enc = 'utf-8'
        t = Element('transaction', charset=enc)

        for k in data.keys():
            val = data[k]
            # Fix data string size
            if self.fix_string_size:
                l = SIZE_LIMITS[k]
                if l:
                    val = val[:l]
            if val:
                e_text = data[k]
                if type(e_text) == bytes:
                    e_text = e_text.decode(enc)
                e = Element(k)

                e.text = e_text
                t.append(e)

        # Request to string:
        req_str = tostring(t, enc).decode(enc)

        # Convert accents. After discussing w/ BeanStream, it appears
        # the API does not support accented characters.
        req = unicodedata.normalize(
            'NFKD', req_str).encode('ascii', 'ignore').decode(enc)

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
        if not 'errorType' in data:
            if 'errorFields' in data and 'errorMessage' in data:
                raise BeanUserError(data['errorFields'], data['errorMessage'])
            else:
                raise BeanSystemError(msg)
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
                              term_url=' ',
                              vbv_enabled='0',
                              sc_enabled='0',
                              cust_address_line2='',
                              trn_language=DEFAULT_LANG,
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

        if trn_language:
            transaction_data['trnLanguage'] = trn_language

        transaction_data.update(self.auth_data)

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
                                trn_language=DEFAULT_LANG,
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

        if trn_language:
            transaction_data['trnLanguage'] = trn_language

        transaction_data.update(self.auth_data)

        response = BeanResponse(
            self.process_transaction(service, transaction_data),
            method)

        self._response = response

        self.check_for_errors(response)

        return response

    def purchase_request(self, *a, **kw):
        """Call this to create a Purchase. SecureCode / VerifiedByVisa
        is disabled by default.
        All data types should be strings. Year and month must be 2
        characters, if it's an integer lower than 10, format using
        %02d (eg: may should be "05")
        """
        method = 'P'
        return self.purchase_base_request(method, *a, **kw)

    def preauth_request(self, *a, **kw):
        """This does a pre-authorization request.
        """
        method = 'PA'
        return self.purchase_base_request(method, *a, **kw)

    def complete_request(self, *a, **kw):
        """This does a pre-auth complete request.
        """
        method = 'PAC'
        return self.adjustment_base_request(method, *a, **kw)

    def refund_request(self, *a, **kw):
        """This does a refund request.
        """
        method = 'R'
        return self.adjustment_base_request(method, *a, **kw)

    def void_request(self, *a, **kw):
        """This does a void request.

        Voids are only allowed on the same day as the purchase was made.

        Amount must be the full amount.
        """
        method = 'V'
        return self.adjustment_base_request(method, *a, **kw)
