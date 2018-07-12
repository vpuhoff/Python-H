
import redis
import time
import json
import signal
import time
import sys

RedisClient = redis.StrictRedis("localhost", db=1)

def my_handler(message):
    print ('MY HANDLER: ', message['data'])


def exit_gracefully(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    sys.exit(1)
    signal.signal(signal.SIGINT, exit_gracefully)

Channel='Docs'

if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)

    Receiver.subscribe(**{Channel: my_handler})
    thread = Receiver.run_in_thread(sleep_time=0.101,daemon=True)
    while True:
        time.sleep(3)
        if 'stopped' in str(thread):
            print('Reconnect...')
            try:
                RedisClient = None
                RedisClient = redis.StrictRedis("localhost", db=1)
                Receiver= None
                Receiver = RedisClient.pubsub(ignore_subscribe_messages=True)
                Receiver.subscribe(**{Channel: my_handler})
                thread._delete()
                thread = None
                print('Reconnect... OK')
                thread = Receiver.run_in_thread(sleep_time=0.101,daemon=True)
            except:
                print('Reconnect failed...')

        print(thread)
        