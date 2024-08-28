from gizmo import Block
import param

class AddOne(Block):
    """A gizmo that adds one to its input."""

    in_a = param.Integer()
    out_a = param.Integer()

    def execute(self):
        self.out_a = self.in_a + 1

a1_gizmo = AddOne()
a1_gizmo.in_a = 3
a1_gizmo.execute()
print(a1_gizmo.out_a)

print(a1_gizmo(in_a=3))
