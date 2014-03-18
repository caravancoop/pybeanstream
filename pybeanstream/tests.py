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

from pybeanstream.client import (
    BeanClient, BeanUserError, BeanResponse,
    BeanSystemError, BaseBeanClientException,
)
import unittest
import random
from mock import Mock


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.b = BeanClient('a_username', 'a_password', 'a_merchant_id')
        
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
        self.b = BeanClient('a_username', 'a_password', 'a_merchant_id')
        self.b.suds_client = Mock()
        
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
        """
        Test pre-auth
        """

        # Preparing data
        amount = '0.01'
        order_num = str(random.randint(1000, 1000000))
        cc_num = '4030000010001234'
        cvv = '123'
        exp_month = '05'
        exp_year = '15'

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000671</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>900581</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>0.01</trnAmount><trnDate>3/17/2014 6:37:50 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>PA</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

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
        
        # Now complete request:

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000672</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>900581</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>0.01</trnAmount><trnDate>3/17/2014 6:37:51 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>2</cvdId><cardType>VI</cardType><trnType>PAC</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.complete_request(
                    amount,
                    order_num,
                    adj_id)
        self.assertTrue(result.data['trnApproved'])

    def test_pre_auth_bytes(self):
        """ Tests that a parameters passed to preauth_request method
        can be byte arrays. """

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

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000673</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>714409</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>0.01</trnAmount><trnDate>3/17/2014 6:37:51 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>PA</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.preauth_request(*dat)
        self.assertTrue(result.data['trnApproved'])

        # Executing pre-auth complete
        adj_id = result.data['trnId']

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000674</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>714409</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>0.01</trnAmount><trnDate>3/17/2014 6:37:52 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>2</cvdId><cardType>VI</cardType><trnType>PAC</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.complete_request(
                    amt,
                    order_num,
                    adj_id)
        self.assertTrue(result.data['trnApproved'])

    def test_unintelligible_error(self):
        """ This tests when the API returns an unexpected data
        set. """

        self.assertRaises(
            BaseBeanClientException, BeanResponse, 'asd', 'PA')


    def test_purchase_transaction_visa_approve(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000679</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>138889</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:55 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('4030000010001234', '123', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_visa_approve_2_address_lines(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000680</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>596771</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:56 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('4030000010001234', '123', '05', '15'),
             **{'cust_address_line2': 'rr2'})
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_visa_declined(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>0</trnApproved><trnId>10000681</trnId><messageId>7</messageId><messageText>DECLINE</messageText><trnOrderNumber>554213</trnOrderNumber><authCode></authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:57 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('4003050500040005', '123', '05', '15'))
        self.assertFalse(result.data['trnApproved'])
                
    def test_purchase_transaction_visa_declined_cvd_ok(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned, this is declined for
        lack of available funds."""
        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>0</trnApproved><trnId>10000682</trnId><messageId>7</messageId><messageText>DECLINE</messageText><trnOrderNumber>722130</trnOrderNumber><authCode></authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>101.00</trnAmount><trnDate>3/17/2014 6:37:58 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>VI</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('4504481742333', '123', '05', '15', amount='101.00'))
        self.assertFalse(result.data['trnApproved'])

    def test_purchase_transaction_amex_approve(self):
        """ This tests a standard Purchase transaction with AMEX and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000675</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>458165</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:53 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>AM</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('371100001000131', '1234', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_amex_declined(self):
        """ This tests a failing Purchase transaction with AMEX and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>0</trnApproved><trnId>10000676</trnId><messageId>7</messageId><messageText>DECLINE</messageText><trnOrderNumber>189112</trnOrderNumber><authCode></authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:53 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>AM</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('342400001000180', '1234', '05', '15'))
        self.assertFalse(result.data['trnApproved'])

    def test_purchase_transaction_mastercard_approve(self):
        """ This tests a standard Purchase transaction with mastercard and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>1</trnApproved><trnId>10000677</trnId><messageId>1</messageId><messageText>Approved</messageText><trnOrderNumber>590048</trnOrderNumber><authCode>TEST</authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:54 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>MC</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('5100000010001004', '123', '05', '15'))
        self.assertTrue(result.data['trnApproved'])

    def test_purchase_transaction_mastercard_declined(self):
        """ This tests a failing Purchase transaction with mastercard and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            '<response><trnApproved>0</trnApproved><trnId>10000678</trnId><messageId>7</messageId><messageText>DECLINE</messageText><trnOrderNumber>446429</trnOrderNumber><authCode></authCode><errorType>N</errorType><errorFields></errorFields><responseType>T</responseType><trnAmount>10.00</trnAmount><trnDate>3/17/2014 6:37:55 PM</trnDate><avsProcessed>1</avsProcessed><avsId>N</avsId><avsResult>0</avsResult><avsAddrMatch>0</avsAddrMatch><avsPostalMatch>0</avsPostalMatch><avsMessage>Street address and Postal/ZIP do not match.</avsMessage><cvdId>1</cvdId><cardType>MC</cardType><trnType>P</trnType><paymentMethod>CC</paymentMethod><ref1></ref1><ref2></ref2><ref3></ref3><ref4></ref4><ref5></ref5></response>')

        result = self.b.purchase_request(
            *self.make_list('5100000020002000', '123', '05', '15'))
        self.assertFalse(result.data['trnApproved'])

if __name__ == '__main__':
    unittest.main()
