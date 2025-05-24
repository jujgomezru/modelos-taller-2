import simpy
import numpy as np
import matplotlib.pyplot as plt

def factory_run(env, repairers, spares):
    global cost
    cost = 0.0
    for i in range(50):
        env.process(operate_machine(env, repairers, spares))

    while True:
        # This cost calculation happens every 8 time units
        # Assuming repairers.capacity is the number of repairers available
        # and spares.capacity is the initial capacity of spares, not current level
        cost += 3.75 * 8 * repairers.capacity + 30 * spares.capacity
        yield env.timeout(8.0)

def operate_machine(env, repairers, spares):
    global cost
    while True:
        yield env.timeout(generate_time_to_failure())
        t_broken = env.now
        print(f'{t_broken:.2f} machine broke')

        # A machine needs a spare to be replaced.
        # This yield should ideally block until a spare is available.
        yield spares.get(1) 
        t_replaced = env.now
        print(f'{t_replaced:.2f} machine replaced')
        cost += 20 * (t_replaced - t_broken) # Cost for downtime

        # Start the repair process for the broken part/machine
        # The repair process will eventually put a spare back into the container.
        env.process(repair_machine(env, repairers, spares))


def repair_machine(env, repairers, spares):
    # Request a repairer to fix the broken part
    with repairers.request() as request:
        yield request # Wait for a repairer to become available
        yield env.timeout(generate_repair_time()) # Simulate repair time
        yield spares.put(1) # Once repaired, the part becomes a spare again
    print(f'{env.now:.2f} repair complete')


def generate_time_to_failure():
    # Adjusted for faster simulation output
    return np.random.uniform(10, 30) # Reduced failure time for demonstration

def generate_repair_time():
    return np.random.uniform(4, 10)

obs_times = []
obs_costs = []
obs_spares = []

def observe(env, spares):
    global cost # Ensure you access the global cost variable
    while True:
        obs_times.append(env.now)
        obs_costs.append(cost)
        obs_spares.append(spares.level)
        yield env.timeout(1.0) # Observe every 1.0 time unit

np.random.seed(0) # For reproducibility
env = simpy.Environment()
repairers = simpy.Resource(env, capacity = 3)
# Initial spares capacity and initial level set to 20
spares = simpy.Container(env, init = 20, capacity = 20) 

env.process(factory_run(env, repairers, spares))
env.process(observe(env, spares))
env.run(until=8*5*52) # Run for 8 hours/day * 5 days/week * 52 weeks/year = 2080 hours

# Plotting
plt.figure(figsize=(10, 6)) # Create a new figure for spares level
plt.step(obs_times, obs_spares, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('Spares level')
plt.title('Spares Level Over Time')
plt.grid(True)

plt.figure(figsize=(10, 6)) # Create another new figure for cost
plt.step(obs_times, obs_costs, where='post')
plt.xlabel('Time (hours)')
plt.ylabel('Cost Incurred')
plt.title('Total Cost Incurred Over Time')
plt.grid(True)

plt.show() # This is the crucial line to display your plots!