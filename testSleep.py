import os
import signal
from time import sleep


class SleepException(Exception):
    pass


def handler(sig, frame):
    print("handler")
    raise SleepException


signal.signal(signal.SIGUSR1, handler)
print(os.getpid())

while True:
    try:
        sleep(10)
    except KeyboardInterrupt:
        print("keyboard interrupt")
    except SleepException:
        print("interupted error")
