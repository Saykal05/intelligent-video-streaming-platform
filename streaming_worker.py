import time

# A control list to be used as a stop signal
should_run = [True, True, True]

def process_source(index):
    while should_run[index]:
        print(f"Processing source {index}...")
        time.sleep(1)  # The actual work would happen here (e.g., video processing)
