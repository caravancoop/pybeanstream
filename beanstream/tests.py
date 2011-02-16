# Copyright(c) 1999 Benoit Clennett-Sirois
#
# Benoit Clennett-Sirois hereby disclaims all copyright interest in
# the program “PyBeanstream”.
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

from classes import *
import unittest
import random
import os

# Important: You must create a file called 'test_settings.py' with the
# following dictionary in it if you want the transaction tests to pass:
#credentials = {
#    username : 'APIUSERNAME',
#    password : 'APIPASSWORD',
#    merchant_id : 'APIMERCHANTID'
#    }

class TestComponents(unittest.TestCase):
    def setUp(self):
        from test_settings import credentials
        self.b = BeanClient(credentials['username'],
                            credentials['password'],
                            credentials['merchant_id'],
                            )
        
    def test_flatten_dict(self):
        sample = {'animal': ['chicken',]}
        sample = flatten_dict(sample)
        self.assertEqual(sample['animal'], 'chicken')

    def test_BeanRequestFieldError(self):
        fields = 'field1,field2'
        messages = 'msg1,msg2'
        e = BeanRequestFieldError(fields, messages)
        self.assertEqual(e.fields[1], 'field2')
        self.assertEqual(e.messages[1], 'msg2')

    def test_download_wsdl(self):
        rand_str = str(random.randint(1000000, 9999999999999))
        name = '_'.join(('test', rand_str))
        path = '/'.join(('/tmp', name))
        self.b.download_wsdl(path)
        self.assertTrue(os.path.exists(path))

    def test_check_for_errors(self):
        r = {'errorType': 'U',
             'errorFields': 'a,b',
             'messageText': 'm,o'}
        self.assertRaises(BeanRequestFieldError,
                          self.b.check_for_errors,
                          r)

        r = {'errorType': 'S'}
        self.assertRaises(BeanBadRequest,
                          self.b.check_for_errors,
                          r)


        r = {'errorType': 'N',
             'trnApproved': '0',
             'cvdId': '2'}
        self.assertRaises(BeanCVDError,
                          self.b.check_for_errors,
                          r)

        r = {'errorType': 'N',
             'trnApproved': '1'}
        self.assertEqual(self.b.check_for_errors(r), None)

class TestApiTransactions(unittest.TestCase):
    def setUp(self):
        from test_settings import credentials
        self.b = BeanClient(credentials['username'],
                       credentials['password'],
                       credentials['merchant_id'])
        
    def make_list(self, cc_num, cvv, exp_m, exp_y):
        # Returns a prepared list with test data already filled in.
        d = ('John Doe',
             cc_num,
             cvv,
             exp_m,
             exp_y,
             '10.00',
             str(random.randint(1000, 1000000)),
             'john.doe@pranana.com',
             'John Doe',
             '5145555555',
             '88 Mont-Royal Est',
             'Montreal',
             'QC',
             'H2T1N6',
             'CA'
             )
        return d

    def test_purchase_transaction_visa_approve(self):
        """ This tests a standard Purchase transaction with VISA and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('4030000010001234', '123', '05', '15'))

        self.assertEqual(result['trnApproved'][0], '1')

    def test_purchase_transaction_visa_declined(self):
        """ This tests a failing Purchase transaction with VISA and verifies
        that the correct response is returned """

        args = self.make_list('4003050500040005', '123', '05', '15')
        self.assertRaises(BeanCVDError, self.b.purchase_request, *args)
                

    def test_purchase_transaction_amex_approve(self):
        """ This tests a standard Purchase transaction with AMEX and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('371100001000131', '1234', '05', '15'))

        self.assertEqual(result['trnApproved'][0], '1')

    def test_purchase_transaction_amex_declined(self):
        """ This tests a failing Purchase transaction with AMEX and verifies
        that the correct response is returned """

        args = self.make_list('342400001000180', '1234', '05', '15')
        self.assertRaises(BeanCVDError, self.b.purchase_request, *args)

    def test_purchase_transaction_mastercard_approve(self):
        """ This tests a standard Purchase transaction with mastercard and verifies
        that the correct response is returned """

        result = self.b.purchase_request(
            *self.make_list('5100000010001004', '123', '05', '15'))

        self.assertEqual(result['trnApproved'][0], '1')

    def test_purchase_transaction_mastercard_declined(self):
        """ This tests a failing Purchase transaction with mastercard and verifies
        that the correct response is returned """

        args = self.make_list('5100000020002000', '123', '05', '15')
        self.assertRaises(BeanCVDError, self.b.purchase_request, *args)

if __name__ == '__main__':
    unittest.main()
