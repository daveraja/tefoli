import sys
import inspect
import functools
from clingo import Model,SolveHandle,Control,Function,Number
from . import theory
from . import wrapper

# ----------------------------------------------------------------------------------------
# Create wrappers around clingo.Model, clingo.SolveHandle, clingo.Control that
# support the DL theory extension.
# ----------------------------------------------------------------------------------------

class ModelDL(Model,metaclass=wrapper.WrapperMetaClass):

    def __init__(self,model,theory):
        self._theory=theory
        wrapper.init_wrapper(self,wrapped_=model)

    @property
    def model_(self): return self._wrapped

    @property
    def theory_(self): return self._theory

    def symbols(self,atoms=False,terms=False,shown=False,csp=False,
                complement=False,dl=False):
        result=[]
        if dl:
            for n,v in self.theory_.assignment(self.model_.thread_id):
                result.append(Function("dl",[n,v]))
        result.extend(self.model_.symbols(atoms,terms,shown,csp,complement))
        return result

class SolveHandleDL(SolveHandle,metaclass=wrapper.WrapperMetaClass):
    def __init__(self,solvehandle,theory):
        self._theory=theory
        wrapper.init_wrapper(self,wrapped_=solvehandle)

    @property
    def solvehandle_(self): return self._wrapped

    @property
    def theory_(self): return self._theory

    #------------------------------------------------------------------------------
    # Overrides
    #------------------------------------------------------------------------------

    def __iter__(self): return self

    def __next__(self): return ModelDL(self._wrapped.__next__(),self._theory)

    def __enter__(self):
        self._wrapped.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self._wrapped.__exit__(exception_type,exception_value,traceback)


class ControlDL(Control,metaclass=wrapper.WrapperMetaClass):
    def __init__(self,*args,**kwargs):
        self._adjust=None
        # Add a theory object or create a clingodl one
        if "theory_" in kwargs and kwargs["theory_"]:
            self._theory=kwargs["theory_"]
            del kwargs["theory_"]
        else:
            self._theory = theory.Theory("clingodl", "clingo-dl")
            self._theory.configure("propagate", "full,1")

        # Add a control object or create one
        if "control_" in kwargs and kwargs["control_"]:
            kwargs["wrapped_"]=kwargs["control_"]
            del kwargs["control_"]

        # Call the proxy initialisation then register the theory
        wrapper.init_wrapper(self,*args,**kwargs)
        self._theory.register(self.control_)

    @property
    def control_(self): return self._wrapped

    @property
    def theory_(self): return self._theory

    @property
    def adjust_(self): return self._adjust

    #------------------------------------------------------------------------------
    # Overrides
    #------------------------------------------------------------------------------
    def solve(self,assumptions=[],on_model=None,on_statistics=None,
              on_finish=None,yield_=False,async_=False):

        # Modify the on_model callback if necessary
        if on_model:
            orig_on_model=on_model
            @functools.wraps(on_model)
            def on_model_wrapper(model):
                self._theory.on_model(model)
                return orig_on_model(ModelDL(model,self._theory))
            on_model = on_model_wrapper
        else:
            on_model=self._theory.on_model

        if on_statistics:
            orig_on_statistics=on_statistics
            @functools.wraps(on_statistics)
            def on_statistics_wrapper(step,accu):
                self._theory.on_statistics(step,accu)
                orig_on_statistics(step,accu)
            on_statistics = on_statistics_wrapper
        else:
            on_statistics=self._theory.on_statistics
        # Call the solve function and handle the result
        result = self.control_.solve(assumptions,on_model,on_statistics,
                                     on_finish,yield_,async_)
        if yield_ or async_:
            return SolveHandleDL(result, self._theory)
        else:
            return result

    def ground(self, *args, **kwargs):
        self.control_.ground(*args,**kwargs)
        self.theory_.prepare(self.control_)

        # Note: this symbol is created upon theory creation right now it is a
        #       bit tricky to get into a state where Propagator.init has been
        #       called for all theory one possibility would be to register a
        #       propgator after all other theories another to lazily build a
        #       lookup table when required
        self._adjust = self.theory_.lookup_symbol(Number(0))

# ----------------------------------------------------------------------------------------
#
# ----------------------------------------------------------------------------------------

class ApplicationDL(object):
    def __init__(self, name):
        self.program_name = name
        self.version = "0.0.1"
        self.__theory = theory.Theory("clingodl", "clingo-dl")

    def register_options(self, options):
        self.__theory.register_options(options)

    def validate_options(self):
        self.__theory.validate_options()
        return True

    def main(self, ctrl, files):
        ctrlDL = ControlDL(control_=ctrl,theory_=self.__theory)

        if not files:
            files.append("-")
        for f in files:
            ctrlDL.load(f)

        # Try to import and run a clingo main function from the __main__
        # module otherwise use a default grounding and solving.
        try:
            from __main__ import main
            main(ctrlDL)
            return
        except (ImportError,NameError):
            pass
        ctrlDL.ground([("base", [])])
        ctrlDL.solve()

#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------
if __name__ == "__main__":
    raise RuntimeError('Cannot run modules')
