import threading
from streaming_worker import process_source, should_run

active_threads = []
is_streaming = False

def start_all_streams():
    global active_threads, is_streaming
    if is_streaming:
        return False
    is_streaming = True
    active_threads = []
    for i in range(3):  # 3 kaynak
        should_run[i] = True
        t = threading.Thread(target=process_source, args=(i,))
        t.start()
        active_threads.append(t)
    return True

def stop_all_streams():
    global is_streaming
    is_streaming = False
    for i in range(3):
        should_run[i] = False
    return True
