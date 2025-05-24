import simpy
import random
from statistics import mean

# Read input parameters
with open("mm9smlb.in", "r") as infile:
    params = infile.read().split()
    mean_interarrival = float(params[0])
    mean_service = float(params[1])
    total_simulation_time = int(params[2])

# Initialize SimPy environment
env = simpy.Environment()

# Initialize random streams for interarrival and service times
stream_interarrival = random.Random()
stream_service = random.Random()

# Define resources for the two servers
server1 = simpy.Resource(env, capacity=1)
server2 = simpy.Resource(env, capacity=1)

# Statistics collection
queue1_delays = []
total_queue1_area = 0.0
total_service_time_server1 = 0.0

queue2_delays = []
total_queue2_area = 0.0
total_service_time_server2 = 0.0

num_completed_customers = 0

def customer(env, server1, server2):
    global total_queue1_area, total_service_time_server1, total_queue2_area, total_service_time_server2, num_completed_customers
    arrival_time = env.now

    # Process Server 1
    with server1.request() as req:
        start_wait1 = env.now
        yield req
        end_wait1 = env.now
        wait1 = end_wait1 - start_wait1
        queue1_delays.append(wait1)
        total_queue1_area += wait1

        # Service time for Server 1
        service_time1 = stream_service.expovariate(1.0 / mean_service)
        yield env.timeout(service_time1)
        total_service_time_server1 += service_time1

    # Process Server 2
    with server2.request() as req:
        start_wait2 = env.now
        yield req
        end_wait2 = env.now
        wait2 = end_wait2 - start_wait2
        queue2_delays.append(wait2)
        total_queue2_area += wait2

        # Service time for Server 2
        service_time2 = stream_service.expovariate(1.0 / mean_service)
        yield env.timeout(service_time2)
        total_service_time_server2 += service_time2

    # Completed both services
    num_completed_customers += 1

def arrival_process(env, server1, server2):
    while True:
        interarrival = stream_interarrival.expovariate(1.0 / mean_interarrival)
        yield env.timeout(interarrival)
        env.process(customer(env, server1, server2))

# Setup and run simulation
env.process(arrival_process(env, server1, server2))

# Run until next event exceeds total_simulation_time
while True:
    if not env._queue:  # No more events
        break
    next_event_time = env.peek()
    if next_event_time > total_simulation_time:
        break
    env.step()

actual_end_time = env.now

# Calculate statistics
avg_delay = mean(queue1_delays) if queue1_delays else 0.0
max_delay = max(queue1_delays) if queue1_delays else 0.0
min_delay = min(queue1_delays) if queue1_delays else 0.0

avg_queue_length1 = total_queue1_area / actual_end_time if actual_end_time > 0 else 0.0
utilization_server1 = total_service_time_server1 / actual_end_time if actual_end_time > 0 else 0.0

avg_queue_length2 = total_queue2_area / actual_end_time if actual_end_time > 0 else 0.0
utilization_server2 = total_service_time_server2 / actual_end_time if actual_end_time > 0 else 0.0

# Generate report
with open("mm9smlb.out", "w") as outfile:
    outfile.write("Single-server queueing system using SimPy\n\n")
    outfile.write(f"Mean interarrival time {mean_interarrival:11.3f} minutes\n\n")
    outfile.write(f"Mean service time {mean_service:16.3f} minutes\n\n")
    outfile.write(f"Total simulation time {total_simulation_time:12d} minutes\n\n")

    outfile.write("\nDelays in queue, in minutes:\n")
    if queue1_delays:
        outfile.write(f"Average delay: {avg_delay:.3f}\n")
        outfile.write(f"Maximum delay: {max_delay:.3f}\n")
        outfile.write(f"Minimum delay: {min_delay:.3f}\n")
    else:
        outfile.write("No delays recorded.\n")

    outfile.write("\nQueue length and server utilization:\n")
    outfile.write(f"Queue 1: average length = {avg_queue_length1:.3f}, utilization = {utilization_server1:.3f}\n")
    outfile.write(f"Queue 2: average length = {avg_queue_length2:.3f}, utilization = {utilization_server2:.3f}\n")

    outfile.write(f"\nTime simulation ended: {actual_end_time:.3f} minutes\n")
    outfile.write(f"Number of customers completed both services: {num_completed_customers}\n")