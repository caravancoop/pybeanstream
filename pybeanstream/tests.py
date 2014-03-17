# -*- coding: utf-8 -*-
# tests.py
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

from classes import (
    BeanClient, BeanUserError, BeanResponse,
    BeanSystemError,
)
import unittest
import random

# Important: You must create a file called 'test_settings.py' with the
# following dictionary in it if you want the transaction tests to pass:
#credentials = {
#    'username' : 'APIUSERNAME',
#    'password' : 'APIPASSWORD',
#    'merchant_id' : 'APIMERCHANTID'
#    }

class TestComponents(unittest.TestCase):
    def setUp(self):
        from test_settings import credentials
        self.b = BeanClient(credentials['username'],
                            credentials['password'],
                            credentials['merchant_id'],
                            )
        
    def test_BeanUserErrorError(self):
        fields = 'field1,field2'
        messages = 'msg1,msg2'
        e = BeanUserError(fields, messages)
        self.assertEqual(str(e), 'Field error with request: field1,field2')
        self.assertEqual(e.fields[1], 'field2')
        self.assertEqual(e.messages[1], 'msg2')

    def test_check_for_errors(self):
        r = BeanResponse({'errorType': 'U',
                          'errorFields': 'a,b',
                          'messageText': 'm,o'},
                         'P')
        self.assertRaises(BeanUserError,
                          self.b.check_for_errors,
                          r)
        r = BeanResponse({'errorType': 'S'}, 'P')
        self.assertRaises(BeanSystemError,
                          self.b.check_for_errors,
                          r)
        r = BeanResponse({'errorType': 'N',
                          'trnApproved': '1',
                          'messageText': 'bad'},
                         'P')
        self.assertEqual(self.b.check_for_errors(r), None)

class TestApiTransactions(unittest.TestCase):
    def setUp(self):
        from test_settings import credentials
        self.b = BeanClient(credentials['username'],
                       credentials['password'],
                       credentials['merchant_id'],
                            )
        
    def make_list(self, cc_num, cvv, exp_m, exp_y, amount='10.00', order_num=None):
        # Returns a prepared list with test data already filled in.
        if not order_num:
            order_num = str(random.randint(1000, 1000000))
        d = ('Jérémy Noël',
             cc_num,
             cvv,
             exp_m,
             exp_y,
             amount,
             order_num,
             'john.doe@pranana.com',
             'Jérémy Noël',
             '5145555555',
             '88 Mont-Royal Est',
             'Montreal',
             'QC',
             'H2T1N6',
             'CA',
             )
        return d

    def test_pre_auth(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """
        # Preparing data
        amount = '0.01'
        order_num = str(random.randint(1000, 1000000))
        cc_num = '4030000010001234'
        cvv = '123'
        exp_month = '05'
        exp_year = '15'

        # Executing pre-auth
        result = self.b.preauth_request(
            *self.make_list(cc_num,
                            cvv,
                            exp_month,
                            exp_year,
                            amount=amount,
                            order_num=order_num))
        self.assertTrue(result.data['trnApproved'])

        # Executing pre-auth complete
        adj_id = result.data['trnId']
        result = self.b.complete_request(
                    amount,
                    order_num,
                    adj_id)
        self.assertTrue(result.data['trnApproved'])

    def test_pre_auth_bytes(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """
        # Preparing data
        amt = '0.01'.encode('ascii')
        order_num = str(random.randint(1000, 1000000)).encode('ascii')
        dat = (
            b'Jeremy Noel',
            b'4030000010001234',
            b'123',
            b'05',
            b'15',
            amt,
            order_num,
            b'john.doe@pranana.com',
            b'Jeremy Noel',
            b'5145555555',
            b'88 Mont-Royal Est',
            b'Montreal',
            b'QC',
            b'H2T1N6',
            b'CA',
        )
        result = self.b.preauth_request(*dat)
        self.assertTrue(result.data['trnApproved'])

        # Executing pre-auth complete
        adj_id = result.data['trnId']
        result = self.b.complete_request(
                    amt,
                    order_num,
                    adj_id)
        self.assertTrue(result.data['trnApproved'])

    def test_unintelligible_error(self):
        """ This tests when the API returns an unexpected data
        set. """
        try:
            service = 'TransactionProcess'
            BeanResponse(
                getattr(self.b.suds_client.service,service)('asd'),
                'PA')
        except Exception as e:
            self.assertTrue('Unintelligible response content:' in e.value)

    def test_purchase_transaction_visa_approve(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('4030000010001234', '123', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_visa_approve_2_address_lines(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('4030000010001234', '123', '05', '15'),
             **{'cust_address_line2': 'rr2'})
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_visa_declined(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('4003050500040005', '123', '05', '15'))
        self.assertFalse(result.data['trnApproved'])
                
    def test_purchase_transaction_visa_declined_cvd_ok(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned, this is declined for
        lack of available funds."""
        result = self.b.purchase_request(
            *self.make_list('4504481742333', '123', '05', '15', amount='101.00'))
        self.assertFalse(result.data['trnApproved'])

    def test_purchase_transaction_amex_approve(self):
        """ This tests a standard Purchase transaction with AMEX and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('371100001000131', '1234', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_amex_declined(self):
        """ This tests a failing Purchase transaction with AMEX and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('342400001000180', '1234', '05', '15'))
        self.assertFalse(result.data['trnApproved'])

    def test_purchase_transaction_mastercard_approve(self):
        """ This tests a standard Purchase transaction with mastercard and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('5100000010001004', '123', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_mastercard_declined(self):
        """ This tests a failing Purchase transaction with mastercard and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('5100000020002000', '123', '05', '15'))
        self.assertFalse(result.data['trnApproved'])

if __name__ == '__main__':
    unittest.main()
