About
=====

PyBeanstream is a python client for the Beanstream Payment Gateway API. Although it works it may very well have a few bugs, use at your own risk. Feel free to report bugs.

This version was tested with python 2.7.4 and 3.3.1

About Beanstream:
http://www.beanstream.com/public/index.asp


Supported transaction types
===========================

-Pre-auth
-Capture
-Purchase
-Token Purchase
-Refund (or partial refund)
-Void


Running tests:
==============

python setup.py nosetests


Sample Code
===========

Check the tests.py file for test transactions.

Here's a sample transaction:

from pybeanstream.client import BeanClient

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
