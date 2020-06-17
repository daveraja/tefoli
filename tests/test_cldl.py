#------------------------------------------------------------------------------
# Unit tests for the clorm monkey patching
#------------------------------------------------------------------------------
import unittest

from clingo import Number, String, Function, parse_program, Control
from tefoli.cldl import ControlDL

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------

class ClDlTestCase(unittest.TestCase):
    def setUp(self):
        self._aspdlstr='''
a. b.
&diff{ a - b } <= -5.
'''
        self._fa = Function("a")
        self._fb = Function("b")
        self._dla = Function("dl",[self._fa,Number(0)])
        self._dlb = Function("dl",[self._fb,Number(5)])

    def tearDown(self):
        pass

    #--------------------------------------------------------------------------
    # Helper function
    #--------------------------------------------------------------------------
    def add_program(self,ctrl, aspstr):
        with ctrl.builder() as bldr:
            parse_program(aspstr, lambda stmt: bldr.add(stmt))

    #--------------------------------------------------------------------------
    # Test making ControlDL
    #--------------------------------------------------------------------------
    def test_make_control(self):
        ctrl=Control()
        ctrldl=ControlDL(control_=ctrl)
        self.assertTrue(isinstance(ctrldl.control_,Control))
        self.assertEqual(ctrldl.control_,ctrl)

        ctrl=ControlDL()
        self.assertTrue(isinstance(ctrl.control_,Control))


    #--------------------------------------------------------------------------
    # Test ControlDL solving
    #--------------------------------------------------------------------------
    def test_solve_yield(self):
        fa=self._fa ; fb=self._fb
        dla = self._dla ; dlb = self._dlb

        ctrl=ControlDL()
        self.add_program(ctrl,self._aspdlstr)
        ctrl.ground([("base",[])])
        with ctrl.solve(yield_=True) as sh:
            for m in sh:
                self.assertEqual(set([fa,fb]),set(m.symbols(atoms=True)))
                self.assertEqual(set([dla,dlb]), set(m.symbols(dl=True)))
                self.assertEqual(set([fa,fb,dla,dlb]),
                                 set(m.symbols(atoms=True,dl=True)))

    def test_solve_on_model(self):
        fa=self._fa ; fb=self._fb
        dla = self._dla ; dlb = self._dlb

        def on_statistics(a,b):
            nonlocal called2
            called2=True

        def on_model(m):
            nonlocal called1
            called1=True
            self.assertEqual(set([fa,fb]),set(m.symbols(atoms=True)))
            self.assertEqual(set([dla,dlb]), set(m.symbols(dl=True)))
            self.assertEqual(set([fa,fb,dla,dlb]),
                             set(m.symbols(atoms=True,dl=True)))

        ctrl=ControlDL()
        self.add_program(ctrl,self._aspdlstr)
        ctrl.ground([("base",[])])
        called1=False ; called2=False
        ctrl.solve(on_model=on_model,on_statistics=on_statistics)
        self.assertTrue(called1)
        self.assertTrue(called2)

#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
if __name__ == "__main__":
    raise RuntimeError('Cannot run modules')
