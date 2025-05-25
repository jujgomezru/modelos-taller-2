import simpy
import random
import statistics

def get_interarrival_time(distribution_type, mean, rng):
    if distribution_type in [1, 3]:
        return rng.expovariate(1.0 / mean)
    elif distribution_type in [2, 4]:
        return mean
    else:
        return rng.expovariate(1.0 / mean)

def get_service_time(distribution_type, mean, rng):
    if distribution_type in [1, 2]:
        return rng.expovariate(1.0 / mean)
    elif distribution_type in [3, 4]:
        return mean
    else:
        return rng.expovariate(1.0 / mean)

def enqueue(env, data):
    now = env.now
    if data['last_time'] < now:
        delta = now - data['last_time']
        data['area'] += data['current_length'] * delta
        data['last_time'] = now
    data['current_length'] += 1

def dequeue(env, data):
    now = env.now
    if data['last_time'] < now:
        delta = now - data['last_time']
        data['area'] += data['current_length'] * delta
        data['last_time'] = now
    data['current_length'] -= 1

def user_in(env, data):
    now = env.now
    if data['last_time'] < now:
        delta = now - data['last_time']
        data['area'] += data['current_count'] * delta
        data['last_time'] = now
    data['current_count'] += 1

def user_out(env, data):
    now = env.now
    if data['last_time'] < now:
        delta = now - data['last_time']
        data['area'] += data['current_count'] * delta
        data['last_time'] = now
    data['current_count'] -= 1

def finalize_data(data, total_time):
    now = total_time
    if data['last_time'] < now:
        delta = now - data['last_time']
        if 'current_length' in data:
            data['area'] += data['current_length'] * delta
        else:
            data['area'] += data['current_count'] * delta
        data['last_time'] = now
    return data['area'] / total_time if total_time > 0 else 0.0

def customer_process(env, server1, s1_q_data, s1_u_data, s1_delays,
                    server2, s2_q_data, s2_u_data, s2_delays,
                    total_delays, completed,
                    dist_type, mean_service, service_rng):
    # Level 1 processing
    arrival_time1 = env.now
    enqueue(env, s1_q_data)
    req = server1.request()
    yield req
    dequeue(env, s1_q_data)
    user_in(env, s1_u_data)

    delay1 = env.now - arrival_time1
    s1_delays.append(delay1)

    service_time = get_service_time(dist_type, mean_service, service_rng)
    yield env.timeout(service_time)

    user_out(env, s1_u_data)
    server1.release(req)

    # Level 2 processing
    arrival_time2 = env.now
    enqueue(env, s2_q_data)
    req2 = server2.request()
    yield req2
    dequeue(env, s2_q_data)
    user_in(env, s2_u_data)

    delay2 = env.now - arrival_time2
    s2_delays.append(delay2)

    service_time2 = get_service_time(dist_type, mean_service, service_rng)
    yield env.timeout(service_time2)

    user_out(env, s2_u_data)
    server2.release(req2)

    # Record total delay
    total_delays.append(delay1 + delay2)
    completed.append(1)

def arrival_process(env, server1, server2, dist_type, mean_iat,
                   s1_q_data, s1_u_data, s1_delays,
                   s2_q_data, s2_u_data, s2_delays,
                   total_delays, completed,
                   mean_service, iat_rng, service_rng):
    while True:
        iat = get_interarrival_time(dist_type, mean_iat, iat_rng)
        yield env.timeout(iat)
        env.process(customer_process(
            env, server1, s1_q_data, s1_u_data, s1_delays,
            server2, s2_q_data, s2_u_data, s2_delays,
            total_delays, completed,
            dist_type, mean_service, service_rng
        ))

def main():
    # Read parameters
    with open('parameters_9.txt', 'r') as f:
        params = f.read().split()
    mean_iat = float(params[0])
    mean_service = float(params[1])
    sim_time = int(float(params[2]))
    dist_type = int(params[3])
    servers_l1 = int(params[4])
    servers_l2 = int(params[5])

    # Setup environment and resources
    env = simpy.Environment()
    server1 = simpy.Resource(env, capacity=servers_l1)
    server2 = simpy.Resource(env, capacity=servers_l2)

    # Initialize data collectors
    s1_q_data = {'last_time': 0, 'current_length': 0, 'area': 0.0}  # Queue length
    s1_u_data = {'last_time': 0, 'current_count': 0, 'area': 0.0}   # Utilization
    s2_q_data = {'last_time': 0, 'current_length': 0, 'area': 0.0}  # Queue length
    s2_u_data = {'last_time': 0, 'current_count': 0, 'area': 0.0}   # Utilization
    s1_delays = []  # Level 1 queue delays
    s2_delays = []  # Level 2 queue delays
    total_delays = []  # Sum of both queue delays
    completed = []

    # Setup random generators
    iat_rng = random.Random()
    service_rng = random.Random()

    # Start processes
    env.process(arrival_process(
        env, server1, server2, dist_type, mean_iat,
        s1_q_data, s1_u_data, s1_delays,
        s2_q_data, s2_u_data, s2_delays,
        total_delays, completed,
        mean_service, iat_rng, service_rng
    ))

    # Run simulation
    env.run(until=sim_time)

    # Calculate statistics
    avg_q1 = finalize_data(s1_q_data, sim_time)
    util1 = finalize_data(s1_u_data, sim_time) / servers_l1
    avg_q2 = finalize_data(s2_q_data, sim_time)
    util2 = finalize_data(s2_u_data, sim_time) / servers_l2

    # Write report
    output_file = f'report_9_{dist_type}.txt'
    with open(output_file, 'w') as f:
        f.write(f"Two-Level Queueing System Report\n")
        f.write(f"="*50 + "\n\n")
        
        # System Configuration
        f.write(f"System Configuration:\n")
        f.write(f"- Mean interarrival time: {mean_iat:.3f} minutes\n")
        f.write(f"- Mean service time: {mean_service:.3f} minutes\n")
        f.write(f"- Level 1 Servers: {servers_l1}\n")
        f.write(f"- Level 2 Servers: {servers_l2}\n")
        f.write(f"- Distribution type: {dist_type} (")
        f.write({
            1: "Exponential/Exponential",
            2: "Constant/Exponential", 
            3: "Exponential/Constant",
            4: "Constant/Constant"
        }.get(dist_type, "Exponential/Exponential") + ")\n\n")
        
        # Combined Delay Statistics
        f.write(f"Combined Delay Statistics (Queue 1 + Queue 2):\n")
        if total_delays:
            f.write(f"- Average total delay: {statistics.mean(total_delays):.3f} minutes\n")
            f.write(f"- Maximum total delay: {max(total_delays):.3f} minutes\n")
            f.write(f"- Minimum total delay: {min(total_delays):.3f} minutes\n")
        else:
            f.write("No customers completed both queues\n")
        f.write("\n")
        
        # Queue 1 Statistics
        f.write(f"Queue 1 Statistics:\n")
        if s1_delays:
            f.write(f"- Average delay: {statistics.mean(s1_delays):.3f} minutes\n")
            f.write(f"- Maximum delay: {max(s1_delays):.3f} minutes\n")
            f.write(f"- Minimum delay: {min(s1_delays):.3f} minutes\n")
        else:
            f.write("- No customers completed Queue 1\n")
        f.write(f"- Average queue length: {avg_q1:.3f}\n")
        f.write(f"- Server utilization: {util1:.3f}\n\n")
        
        # Queue 2 Statistics
        f.write(f"Queue 2 Statistics:\n")
        if s2_delays:
            f.write(f"- Average delay: {statistics.mean(s2_delays):.3f} minutes\n")
            f.write(f"- Maximum delay: {max(s2_delays):.3f} minutes\n")
            f.write(f"- Minimum delay: {min(s2_delays):.3f} minutes\n")
        else:
            f.write("- No customers completed Queue 2\n")
        f.write(f"- Average queue length: {avg_q2:.3f}\n")
        f.write(f"- Server utilization: {util2:.3f}\n\n")
        
        # Simulation Summary
        f.write(f"Simulation Summary:\n")
        f.write(f"- Customers completed: {len(completed)}\n")
        f.write(f"- Simulation duration: {sim_time} minutes\n")

if __name__ == '__main__':
    main()