%--------------------------------------------------------------
% Simple example of a clingo-dl program with python integration
%--------------------------------------------------------------

1 { a(1); a(2) }.
b(X) :- a(X).
%c(@blah(X)) :- a(X).

&diff{ a(X) - b(X) } <= -5 :- a(X).

#script(python)

def blah(num):
    return num.number+2

def main(ctrl):
    ctrl.ground([("base",[])])
    with ctrl.solve(yield_=True) as sh:
        for m in sh:
            pass
            print("MODEL: {}".format(m.symbols(atoms=True,dl=True)))
            print("MODEL: {}".format(m.symbols(atoms=True)))
#end.
