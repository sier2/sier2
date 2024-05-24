#

# A demonstration of gizmos and individual vs batch updates.
#

import param
# import gizmo.gizmo as gizmo
from gizmo import Gizmo, GizmoManager

class Gizmo1(Gizmo):
    """A gizmo that creates pointless outputs.

    This gizmo has no inputs.
    """

    # Use param to specify outputs.
    #
    a_string = param.String(
        label='Alphanumeric',
        regex=r'(?i)^[u|b]\w*$',
        doc='A word string starting with U or B',
        default='u'
    )
    length = param.Number(
        label='String length',
        doc='A floating point number',
        default=-1
    )

    # def __init__(self, **kwargs):
    #     super().__init__(**kwargs)

    def update(self, s):
        """Updates the outputs separately, causing two watch events."""

        self.a_string = s
        self.length = len(s)

    def update_batch(self, s):
        """Updates the outputs in batch, causing a single watch event."""

        self.param.update({'a_string': s, 'length': len(s)})

class Gizmo2(Gizmo):
    """A gizmo that depends on the outputs of Gizmo1."""

    length = param.Number(label='A number', doc='I am given this number', allow_refs=True)
    a_string = param.String(label='A string', doc='I am given this string', allow_refs=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        print(f'Action in {self.__class__.__name__}: {self.a_string=} {self.length=}')

def main():
    """Pretend to be a gizmo manager."""

    # Get gizmo instances and connect them via their params.
    #
    g1 = Gizmo1()
    g2 = Gizmo2()

    GizmoManager.connect(g1, g2, ['a_string', 'length'])

    # Pretend to be a GUI and send some data.
    #
    print('Entering a string in gizmo1 will cause output of two params to gizmo2.')

    print('To see the difference between individual and batch updating,')
    print('strings that start with U will do individual updates,')
    print('B will do a batch update.')
    print()

    while (s:=input('Enter an alphanumeric string [Enter to quit]: ').strip()):
        try:
            g1.param.a_string._validate(s)
            if s[0] in 'Uu':
                g1.update(s)
            else:
                g1.update_batch(s)
        except ValueError as e:
            print(e)

    return g1, g2

if __name__=='__main__':
    g1, g2 = main()
