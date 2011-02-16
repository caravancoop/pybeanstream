=== About ===

PyBeanstream is a python client for the Beanstream Payment Gateway API. Although it works it may very well have a few bugs, use at your own risk. Feel free to report bugs.

About Beanstream:
http://www.beanstream.com/public/index.asp


=== Supported transaction types ===

Right now the only supported transaction types are "Purchase" Transactions, although it can very well be extended to support more.


=== Mandatory Sample Code ===

Check the tests.py file for test transactions.

Here's a sample transaction:

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
