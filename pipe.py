from collections import defaultdict
import subprocess
import time
import uuid


TICK = 0.001
RESOLUTION = 3


def runner(argv, timeout=0):
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)

    t0 = time.time()

    while True:
        exit_code = proc.poll()
        if exit_code is None:
            # Process is still running
            if timeout > 0 and time.time() - t0 >= timeout:
                proc.kill()
                raise Exception('Timeout exceeded')
        else:
            return proc.returncode
        # time.sleep(1)     <-- BAD idea
        yield 20 * TICK


def defcallback(coro_id, result):
    print(f'[{coro_id}] result={result}')


def deferrback(coro_id, error):
    print(f'[{coro_id}] exception={error}')


class Loop:
    def __init__(self):
        self.now = 0
        self.ready_at = defaultdict(list)
        self.coro_ids = {}
        self.number_of_coroutines = 0

    def schedule(self, coro, clbk=defcallback, erbk=deferrback, t=0):
        t = round(t, RESOLUTION)
        if t <= self.now:
            t = self.now

        self.ready_at[t].append((coro, clbk, erbk))
        if coro not in self.coro_ids:
            self.coro_ids[coro] = str(uuid.uuid4())
            self.number_of_coroutines += 1
        if t == 0:
            print(f'[loop] coro {self.coro_ids[coro]} scheduled at t={t}')

    def run(self):
        while self.number_of_coroutines:
            self.now = round(self.now, RESOLUTION)

            while self.ready_at[self.now]:
                coro, clbk, erbk = self.ready_at[self.now].pop(0)
                try:
                    run_next = round(self.now + coro.send(None), RESOLUTION)
                except StopIteration as e:
                    clbk(self.coro_ids[coro], e.value)
                    self.number_of_coroutines -= 1
                except Exception as e:
                    erbk(self.coro_ids[coro], e)
                    self.number_of_coroutines -= 1
                else:
                    self.schedule(coro, clbk, erbk, run_next)
            self.now += TICK
            time.sleep(TICK)


if __name__ == '__main__':
    loop = Loop()

    loop.schedule(runner('sleep 10'.split(), timeout=5))
    loop.schedule(runner('sleep 10'.split()))
    loop.schedule(runner('sleep 10'.split()))
    loop.schedule(runner('sleep 10'.split()))
    loop.schedule(runner('sleep 10'.split()))

    loop.run()
