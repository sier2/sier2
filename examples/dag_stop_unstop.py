#

# Demonstrate displaying a dag.
#

from sier2 import Block, Dag, Connection
import param
import threading
import time

class Sleeper(Block):
    """Sleep for a number of seconds specified by the input param.

    Sleeping is done one second at a time, so we can demonstrate disabling a dag.
    When the sleeping finishes, an event is set, and the output param is set.
    """

    in_time = param.Integer(label='sleep time', default=0, doc='Sleep for this many seconds')
    out_time = param.Integer(label='pass it on', default=0, doc='Pass the sleep time along')

    def __init__(self, name, event: threading.Event=None):
        super().__init__(name=name)
        self.event = event
        self.marker = 0

    def execute(self):
        if self.event:
            self.event.set()

        print(f'{self.name} started', flush=True)
        for count in range(self.in_time):
            time.sleep(1)
            print(f'{self.name} seconds slept: {count+1} of {self.in_time}', flush=True)

        self.marker += 1
        self.out_time = self.in_time

    def __str__(self):
        s = f'{self.__class__.__name__} {self.name}'
        return(f'<{s} {self.in_time=} {self.out_time=} {self.marker=}>')

def runner(dag: Dag, sleep_time: int):
    print('Starting ...')
    s0: Sleeper = dag.block_by_name('s0')
    s0.out_time = sleep_time
    dag.execute()

def main():
    # Use an Event to determine when s2 is executed.
    #
    event = threading.Event()

    # Each Sleeper increments a marker that starts at zero.
    # The first Sleeper is used to start the dag.
    # The second Sleeper sets the event.
    #
    s0 = Sleeper(name='s0')
    s1 = Sleeper(name='s1')
    s2 = Sleeper(name='s2', event=event)
    s3 = Sleeper(name='s3')

    dag = Dag(doc='Example: stopping and unstopping a dag', title='stopping and unstoppping a dag')
    dag.connect(s0, s1, Connection('out_time', 'in_time'))
    dag.connect(s1, s2, Connection('out_time', 'in_time'))
    dag.connect(s2, s3, Connection('out_time', 'in_time'))

    print('Start the dag in its own thread.')
    t = threading.Thread(target=runner, args=(dag, 2))
    t.start()

    print('Wait for s2 to start executing, then stop the dag.')
    event.wait()
    dag.stop()

    print('Wait for the dag thread to finish.')
    t.join()

    print('Sleepers s1 and s2 have their markers incremented, s3 did not execute.')
    print(s1, s1.marker==1)
    print(s2, s2.marker==1)
    print(s3, s3.marker==0)

    print('Run the dag again.')
    print('Because the stopper is still set, nothing will happen.')
    runner(dag, 2)
    print(s1, s1.marker==1)
    print(s2, s2.marker==1)
    print(s3, s3.marker==0)

    print('Unstop the dag, and run the dag again.')
    print('All of the Sleepers will have their markers incremented.')
    dag.unstop()
    runner(dag, 2)
    print(s1, s1.marker==2)
    print(s2, s2.marker==2)
    print(s3, s3.marker==1)

if __name__=='__main__':
    main()
