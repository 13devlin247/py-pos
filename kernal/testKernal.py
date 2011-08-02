# -*- coding:utf-8 -*-
import os, sys
p1 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
p2 = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(p1)
sys.path.append(p2)
sys.stdout = sys.stderr
os.environ['DJANGO_SETTINGS_MODULE'] = 'pos.settings' 

import unittest
from barn import BarnOwl

class TestBarnOwl(unittest.TestCase):    
    def testInStock(self):
        owl = BarnOwl()        
        dict = self._build_input_dict()
        inStockResult = owl.InStock(owl.purchase , dict)        
        assert len(inStockResult) == 2
        
    def testOutStock(self):
        pass
        
    def testStockCount(self):
        pass

    def _build_input_dict(self):
        inputDict  = {}
        inputDict[u'do_date'] = u'2011-06-22'
        inputDict[u'do_no'] = u'BC1655'
        inputDict[u'inv_no'] = u'BC1654'
        inputDict[u'salesMode'] = u'cash'
        inputDict[u'item'] = u'NK1280PPL'
        inputDict[u'mode'] = u'purchase'
        inputDict[u'supplier'] = u'Super-Link Station [M) Sdn Bhd'
        inputDict[u'_auth_user_id'] = 1
        
        
        """
        Supplier
        Customer
        Mode
        User
        DO_Date
        Invoice_NO
        DO_NO
        Status
        """
        inputDict[u'111'] = {}
        inputDict[u'111'] [u'serial-2'] = []
        inputDict[u'111'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'111'] [u'serial-1'] = []
        inputDict[u'111'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'111'] [u'serial-0'] = []
        inputDict[u'111'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'111'] [u'cost'] = []
        inputDict[u'111'] [u'cost'].append(u'2000')    
        inputDict[u'111'] [u'quantity'] = []
        inputDict[u'111'] [u'quantity'].append(u'3')            
        
        inputDict[u'110'] = {}
        inputDict[u'110'] [u'serial-2'] = []
        inputDict[u'110'] [u'serial-2'].append(u'NK1280PPL003')
        inputDict[u'110'] [u'serial-1'] = []
        inputDict[u'110'] [u'serial-1'].append(u'NK1280PPL002')
        inputDict[u'110'] [u'serial-0'] = []
        inputDict[u'110'] [u'serial-0'].append(u'NK1280PPL001')    
        inputDict[u'110'] [u'cost'] = []
        inputDict[u'110'] [u'cost'].append(u'2000')    
        inputDict[u'110'] [u'quantity'] = []
        inputDict[u'110'] [u'quantity'].append(u'3')                    
        return inputDict
        
if __name__=="__main__":
    unittest.main()    
    