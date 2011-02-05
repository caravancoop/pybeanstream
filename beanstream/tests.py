from classes import BeanClient, BeanCVDError
import unittest
import random

# Important: You must create a file called 'test_settings.py' with the
# following dictionary in it if you want the transaction tests to pass:
#credentials = {
#    username : 'APIUSERNAME',
#    password : 'APIPASSWORD',
#    merchant_id : 'APIMERCHANTID'
#    }

class TestApiTransactions(unittest.TestCase):
    def setUp(self):
        from test_settings import credentials
        self.b = BeanClient(credentials['username'],
                       credentials['password'],
                       credentials['merchant_id'])
        
    def make_list(self, cc_num, cvv, exp_m, exp_y):
        # Returns a prepared list with test data already filled in.
        d = ('John Doe',
             cvv,
             cc_num,
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
