from subprocess import Popen, PIPE
from queue import Queue
from threading import Thread

from jupyter_cpp_wrapperkernel.constants import CHANNEL_STDERR, CHANNEL_STDOUT


class KernelSubprocess(Popen):
    def __init__(self, cmd, print, stdin=None):
        super().__init__(cmd, stdin=stdin, stdout=PIPE, stderr=PIPE, bufsize=0)

        self.print = print

        self._stdout_queue = Queue()
        self._stdout_thread = Thread(target=KernelSubprocess._enqueue_output, args=(self.stdout, self._stdout_queue))
        self._stdout_thread.daemon = True
        self._stdout_thread.start()

        self._stderr_queue = Queue()
        self._stderr_thread = Thread(target=KernelSubprocess._enqueue_output, args=(self.stderr, self._stderr_queue))
        self._stderr_thread.daemon = True
        self._stderr_thread.start()

    @staticmethod
    def _enqueue_output(stream, queue):
        for line in iter(lambda: stream.read(4096), b''):
            queue.put(line)
        stream.close()

    def _write_contents(self):
        def deque_all(queue):
            res = b''
            size = queue.qsize()
            while size != 0:
                res += queue.get_nowait()
                size -= 1
            return res

        stderr_contents = deque_all(self._stderr_queue)
        if stderr_contents:
            self.print(stderr_contents.decode(), CHANNEL_STDERR)

        stdout_contents = deque_all(self._stdout_queue)
        if stdout_contents:
            self.print(stdout_contents.decode(), CHANNEL_STDOUT)
        
    def join(self):
        while self.poll() is None:
            self._write_contents()

        self._stdout_thread.join()
        self._stderr_thread.join()

        self._write_contents()