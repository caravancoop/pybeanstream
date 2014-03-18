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


import os
import unittest
import json

from mock import Mock

from pybeanstream.client import (
    BeanClient, BeanUserError, BeanResponse,
    BeanSystemError, BaseBeanClientException,
)
from pybeanstream.xml_utils import xmltodict


# Read errors from external file because very long.

EXPECTED_RSP = json.loads(
    open(os.path.join(
        os.path.dirname(__file__), 'results.json')).read())


class TestComponents(unittest.TestCase):
    def setUp(self):
        self.b = BeanClient(
            'a_username', 'a_password', 'a_merchant_id')

    def test_xml_to_dict(self):
        """
        Tests xml_to_dict's remove_whilespace_nodes
        """
        xml = "<xml><a>test</a></xml>"
        self.assertEqual(xmltodict(xml), {'a': ['test']})

        xml = "<xml><a>test</a><b> </b></xml>"
        self.assertEqual(xmltodict(xml), {'a': ['test'], 'b': [None]})

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

    def make_list(self, cc_num, cvv, exp_m, exp_y, amount, order_num):
        # Returns a prepared list with test data already filled in.
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
        order_num = '900581'
        cc_num = '4030000010001234'
        cvv = '123'
        exp_month = '05'
        exp_year = '15'

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_pre_auth_1'])

        # Executing pre-auth
        result = self.b.preauth_request(
            *self.make_list(cc_num,
                            cvv,
                            exp_month,
                            exp_year,
                            amount=amount,
                            order_num=order_num))
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

        # Executing pre-auth complete
        adj_id = result.data['trnId']

        # Now complete request:

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_pre_auth_2'])

        result = self.b.complete_request(
            amount,
            order_num,
            adj_id)
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_pre_auth_bytes(self):
        """ Tests that a parameters passed to preauth_request method
        can be byte arrays. """

        # Preparing data
        amt = '0.01'.encode('ascii')
        order_num = '714409'
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
            EXPECTED_RSP['test_pre_auth_bytes_1'])

        result = self.b.preauth_request(*dat)
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

        # Executing pre-auth complete
        adj_id = result.data['trnId']

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_pre_auth_bytes_2'])

        result = self.b.complete_request(
            amt,
            order_num,
            adj_id)
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_unintelligible_error(self):
        """ This tests when the API returns an unexpected data
        set. """

        self.assertRaises(
            BaseBeanClientException, BeanResponse, 'asd', 'PA')

    def test_purchase_transaction_visa_approve(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_visa_approve'])

        order_num = '138889'
        result = self.b.purchase_request(
            *self.make_list(
                '4030000010001234', '123', '05', '15',
                '10.00', order_num))
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_visa_approve_2_address_lines(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP[
                'test_purchase_transaction_visa_approve_2_address_lines'])

        order_num = '596771'
        result = self.b.purchase_request(
            *self.make_list(
                '4030000010001234', '123', '05', '15',
                '10.00', order_num),
            **{'cust_address_line2': 'rr2'})
        self.assertTrue(result.data['trnApproved'])
        self.assertTrue(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_visa_declined(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_visa_declined'])

        order_num = '554213'
        result = self.b.purchase_request(
            *self.make_list(
                '4003050500040005', '123', '05', '15',
                '10.00', order_num))
        self.assertFalse(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_visa_declined_cvd_ok(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned, this is declined for
        lack of available funds."""
        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_visa_declined_cvd_ok'])

        order_num = '722130'
        result = self.b.purchase_request(
            *self.make_list(
                '4504481742333', '123', '05', '15',
                '101.00', order_num))
        self.assertFalse(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_amex_approve(self):
        """ This tests a standard Purchase transaction with AMEX and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_amex_approve'])

        order_num = '458165'
        result = self.b.purchase_request(
            *self.make_list(
                '371100001000131', '1234', '05', '15',
                '10.00', order_num))
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_amex_declined(self):
        """ This tests a failing Purchase transaction with AMEX and verifies
        that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_amex_declined'])

        order_num = '189112'
        result = self.b.purchase_request(
            *self.make_list(
                '342400001000180', '1234', '05', '15',
                '10.00', order_num))
        self.assertFalse(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_mastercard_approve(self):
        """ This tests a standard Purchase transaction with mastercard and
        verifies that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_mastercard_approve'])

        order_num = '590048'
        result = self.b.purchase_request(
            *self.make_list(
                '5100000010001004', '123', '05', '15',
                '10.00', order_num))
        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_purchase_transaction_mastercard_declined(self):
        """ This tests a failing Purchase transaction with mastercard and
        verifies that the correct response is returned """

        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_purchase_transaction_mastercard_declined'])

        order_num = '446429'
        result = self.b.purchase_request(
            *self.make_list(
                '5100000020002000', '123', '05', '15',
                '10.00', order_num))
        self.assertFalse(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_refund(self):
        """
        Tests refunds
        """
        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_refund'])

        order_num = '567121'
        result = self.b.refund_request(
            amount='0.01',
            order_num=order_num,
            adj_id='10000787')

        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)

    def test_voids(self):
        """
        Tests refunds
        """
        self.b.suds_client.service.TransactionProcess.return_value = (
            EXPECTED_RSP['test_voids'])

        order_num = '243364'
        result = self.b.void_request(
            amount='10.00',
            order_num=order_num,
            adj_id='10000770')

        self.assertTrue(result.data['trnApproved'])
        self.assertEqual(result.data['trnOrderNumber'], order_num)
