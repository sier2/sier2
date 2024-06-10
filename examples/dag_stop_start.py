#

# Demonstrate displaying a dag.
#

from gizmo import Gizmo, Dag, Connection
import param
import threading
import time

class Sleeper(Gizmo):
    """Sleep for a number of seconds specified by the input param.

    Sleeping is done one second at a time, so we can demonstrate disabling a dag.
    When the sleeping finishes, an event is set, and the output param is set.
    """

    time_in = param.Integer(label='sleep time', default=0, doc='Sleep for this many seconds')
    time_out = param.Integer(label='pass it on', default=0, doc='Pass the sleep time along')

    def __init__(self, name, event: threading.Event=None):
        super().__init__(name=name)
        self.event = event
        self.marker = 0

    def execute(self):
        if self.event:
            self.event.set()

        print(f'{self.name} started', flush=True)
        for count in range(self.time_in):
            time.sleep(1)
            print(f'{self.name} seconds slept: {count+1} of {self.time_in}', flush=True)

        self.marker += 1
        self.time_out = self.time_in

    def __str__(self):
        s = f'{self.__class__.__name__} {self.name}'
        return(f'<{s} {self.time_in=} {self.time_out=} {self.marker=}>')

def runner(dag: Dag, sleep_time: int):
    print('Started')
    s0: Sleeper = dag.gizmo_by_name('s0')
    s0.time_out = sleep_time

def main():
    # Use an Event to determine when s2 is executed.
    #
    event = threading.Event()

    # Each Slepper increments a marker that starts at zero.
    # The first Sleeper is used to start the dag.
    # The second Sleeper sets the event.
    #
    s0 = Sleeper(name='s0')
    s1 = Sleeper(name='s1')
    s2 = Sleeper(name='s2', event=event)
    s3 = Sleeper(name='s3')

    dag = Dag()
    dag.connect(s0, s1, Connection('time_out', 'time_in'))
    dag.connect(s1, s2, Connection('time_out', 'time_in'))
    dag.connect(s2, s3, Connection('time_out', 'time_in'))

    # Start the dag in its own thread.
    #
    t = threading.Thread(target=runner, args=(dag, 2))
    t.start()

    # Wait for s2 to start executing, then stop the dag.
    #
    event.wait()
    dag.stop()

    # Wait for the dag thread to finish.
    #
    t.join()

    # Sleepers s1 and s2 have their markers incremented, s3 did not execute.
    #
    print(s1)
    print(s2)
    print(s3)

    # Run the dag again.
    # Because the stopper is still set, nothing will happen.
    #
    runner(dag, 2)
    print(s1)
    print(s2)
    print(s3)

    # Unstop the dag, and run the dag again.
    # All of the Sleepers will have their markers incrmented.
    #
    dag.unstop()
    runner(dag, 2)
    print(s1)
    print(s2)
    print(s3)

if __name__=='__main__':
    main()
