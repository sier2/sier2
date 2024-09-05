#

# Demonstrate finding blocks that have compatible outputs.
# An output is compatible with this blocks inputs by type.
#
# **** NOT WORKING YET ****
#

from sier2 import Block, Dag
import param

class ThisGizmo(Block):
    # Inputs.
    #
    intp = param.Integer(label='An integer')
    strp = param.Integer(label='A string')
    dfp = param.DataFrame(label='A dataframe')

class Gizmo1(Block):
    # Outputs.
    #
    dfp = param.DataFrame(label='A dataframe')
    intp = param.Integer(label='An integer')
    strp = param.Integer(label='A string')

class Gizmo2(Block):
    # Outputs.
    #
    dataframep = param.DataFrame(label='A dataframe')
    numberp = param.Integer(label='An integer')
    boolp = param.Boolean(label='A boolean')

class Gizmo3(Block):
    # Outputs.
    #
    nump = param.Integer(label='An integer')
    boolp = param.Boolean(label='A boolean')

class Gizmo4(Block):
    # Outputs.
    #
    boolp = param.Boolean(label='A boolean')

if __name__=='__main__':
    thisg = ThisGizmo()

    g1 = Gizmo1()
    g2 = Gizmo2()
    g3 = Gizmo3()

    from pprint import pprint
    pprint(Dag.compatible_outputs(thisg, g1))

    pprint(Dag.compatible_outputs(thisg, g2))

    pprint(Dag.compatible_outputs(thisg, g3))
