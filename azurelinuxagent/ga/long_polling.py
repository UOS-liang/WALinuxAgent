import datetime
import threading
import time

from azurelinuxagent.common.interfaces import ThreadHandlerInterface
from azurelinuxagent.common import logger
from azurelinuxagent.common.future import httpclient, ustr


def get_longpolling_handler():
    return LongPollingHandler()


class LongPollingHandler(ThreadHandlerInterface):
    _THREAD_NAME = "LongPollingHandler"

    @staticmethod
    def get_thread_name():
        return LongPollingHandler._THREAD_NAME

    def __init__(self):
        self.longpolling_thread = None
        self.should_run = True

    def run(self):
        self.start()

    def stop(self):
        self.should_run = False
        if self.is_alive():
            self.join()

    def join(self):
        self.longpolling_thread.join()

    def stopped(self):
        return not self.should_run

    def keep_alive(self):
        return False

    def is_alive(self):
        return self.longpolling_thread is not None and self.longpolling_thread.is_alive()

    def start(self):
        self.longpolling_thread = threading.Thread(target=self.daemon)
        self.longpolling_thread.setDaemon(True)
        self.longpolling_thread.setName(self.get_thread_name())
        self.longpolling_thread.start()

    def daemon(self):
        new_request = True
        while new_request:
            try:
                logger.info("[HTTP Request(longPolling)] Timestamp:{0}".format(datetime.datetime.utcnow()))

                timeout = 60
                conn = httpclient.HTTPConnection("168.63.129.16", 32526, timeout=10)
                url = "http://168.63.129.16:32526/longPolling"
                conn.request(method="GET", url=url)
                resp = conn.getresponse()

                while timeout > 0 and resp is None:
                    time.sleep(1)
                    timeout -= 1

                if timeout == 0:
                    logger.warn("[HTTP Request(longPolling)] timed out at : {0}".format(datetime.datetime.utcnow()))
                else:
                    if resp.status != 200 and not 500 <= resp.status <= 599:
                        new_request = False
                    result = "[HTTP Response(longPolling)] Timestamp:{0}; {1} [{2}: {3}] {4}".format(
                        datetime.datetime.utcnow(),
                        url,
                        resp.status,
                        resp.reason,
                        resp.read())
                    logger.info(result)

            except Exception as e:
                logger.error("Failed to fetch from longPolling: {0}".format(ustr(e)))
                new_request = False
