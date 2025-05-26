import simpy
import random
import statistics
from collections import defaultdict

class SimuladorSecuencial:
    def __init__(self, env, mean_interarrival, mean_service, 
                 servers_level1, servers_level2, distribution_type):
        self.env = env
        self.mean_interarrival = mean_interarrival
        self.mean_service = mean_service
        self.distribution_type = distribution_type
        self.server1 = simpy.Resource(env, capacity=servers_level1)
        self.server2 = simpy.Resource(env, capacity=servers_level2)
        self.queue1_delays = []
        self.queue2_delays = []
        self.system_times = []
        self.queue1_lengths = []
        self.queue2_lengths = []
        self.server1_busy = []
        self.server2_busy = []
        self.num_completed = 0
        self.num_arrivals = 0
        self.queue1_entry_times = {}
        self.queue2_entry_times = {}
        self.env.process(self.customer_generator())
        self.env.process(self.monitor_queues())
        self.env.process(self.monitor_servers())
    
    def get_interarrival_time(self):
        if self.distribution_type in [1, 3]:
            return random.expovariate(1.0 / self.mean_interarrival)
        else:
            return self.mean_interarrival
    
    def get_service_time(self):
        if self.distribution_type in [1, 2]:
            return random.expovariate(1.0 / self.mean_service)
        else:
            return self.mean_service
    
    def customer_generator(self):
        while True:
            yield self.env.timeout(self.get_interarrival_time())
            
            arrival_time = self.env.now
            self.num_arrivals += 1
            customer_id = self.num_arrivals
            self.env.process(self.customer_flow(customer_id, arrival_time))
    
    def customer_flow(self, customer_id, arrival_time):
        queue1_entry = self.env.now
        self.queue1_entry_times[customer_id] = queue1_entry
        
        with self.server1.request() as req:
            yield req
            
            queue1_delay = self.env.now - queue1_entry
            self.queue1_delays.append(queue1_delay)
            del self.queue1_entry_times[customer_id]
            yield self.env.timeout(self.get_service_time())
        
        queue2_entry = self.env.now
        self.queue2_entry_times[customer_id] = queue2_entry
        with self.server2.request() as req:
            yield req
            
            queue2_delay = self.env.now - queue2_entry
            self.queue2_delays.append(queue2_delay)
            del self.queue2_entry_times[customer_id]
            
            yield self.env.timeout(self.get_service_time())
        
        system_time = self.env.now - arrival_time
        self.system_times.append(system_time)
        self.num_completed += 1
    
    def monitor_queues(self):
        while True:
            q1_len = len(self.server1.queue)
            self.queue1_lengths.append(q1_len)
            
            q2_len = len(self.server2.queue)
            self.queue2_lengths.append(q2_len)
            
            yield self.env.timeout(0.1) 
    
    def monitor_servers(self):
        while True:
            self.server1_busy.append(len(self.server1.users))
            self.server2_busy.append(len(self.server2.users))
            yield self.env.timeout(0.1)  
    
    def generate_report(self):
        def safe_mean(data):
            return statistics.mean(data) if data else 0.0
        
        def safe_max(data):
            return max(data) if data else 0.0
        
        def safe_min(data):
            return min(data) if data else 0.0
        
        report = "Multi-server queueing system using SimPy\n\n"
        report += f"Mean interarrival time{11*' '}{self.mean_interarrival:.3f} minutes\n\n"
        report += f"Mean service time{16*' '}{self.mean_service:.3f} minutes\n\n"
        report += f"Total simulation time{12*' '}{self.env.now:.3f} minutes\n\n"
        report += f"Distribution type: {self.distribution_type}\n"
        
        dist_map = {
            1: "Interarrival: Exponential, Service: Exponential",
            2: "Interarrival: Constant, Service: Exponential",
            3: "Interarrival: Exponential, Service: Constant",
            4: "Interarrival: Constant, Service: Constant"
        }
        report += dist_map.get(self.distribution_type, "Invalid distribution type") + "\n"
        report += f"Number of servers at level 1: {self.server1.capacity}\n"
        report += f"Number of servers at level 2: {self.server2.capacity}\n\n"
        
        report += "\nDelays in Queue 1, in minutes:\n"
        report += f"  Average: {safe_mean(self.queue1_delays):.3f}\n"
        report += f"  Maximum: {safe_max(self.queue1_delays):.3f}\n"
        report += f"  Minimum: {safe_min(self.queue1_delays):.3f}\n"
        report += f"  Number measured: {len(self.queue1_delays)}\n"
        
        report += "\nDelays in Queue 2, in minutes:\n"
        report += f"  Average: {safe_mean(self.queue2_delays):.3f}\n"
        report += f"  Maximum: {safe_max(self.queue2_delays):.3f}\n"
        report += f"  Minimum: {safe_min(self.queue2_delays):.3f}\n"
        report += f"  Number measured: {len(self.queue2_delays)}\n"
        
        report += "\nTotal System Time (arrival to final departure), in minutes:\n"
        report += f"  Average: {safe_mean(self.system_times):.3f}\n"
        report += f"  Maximum: {safe_max(self.system_times):.3f}\n"
        report += f"  Minimum: {safe_min(self.system_times):.3f}\n"
        report += f"  Number measured: {len(self.system_times)}\n"
        
        report += "\nQueue lengths:\n"
        report += f"  Average queue 1 length: {safe_mean(self.queue1_lengths):.3f}\n"
        report += f"  Average queue 2 length: {safe_mean(self.queue2_lengths):.3f}\n"
        
        server1_util = sum(self.server1_busy) / len(self.server1_busy) / self.server1.capacity * 100
        server2_util = sum(self.server2_busy) / len(self.server2_busy) / self.server2.capacity * 100
        report += "\nServer utilization:\n"
        report += f"  Server 1 utilization: {server1_util:.1f}%\n"
        report += f"  Server 2 utilization: {server2_util:.1f}%\n"
        
        report += f"\nTime simulation ended:{12*' '}{self.env.now:.3f} minutes\n"
        report += f"Number of customers completed both services:{8*' '}{self.num_completed}\n"
        
        return report

def read_parameters(filename):
    with open(filename, 'r') as f:
        values = list(map(float, f.readline().strip().split()))
        
        mean_interarrival = values[0]
        mean_service = values[1]
        total_simulation_time = int(values[2])
        distribution_type = int(values[3])
        servers_level1 = int(values[4])
        servers_level2 = int(values[5])
        
        return (mean_interarrival, mean_service, total_simulation_time,
                distribution_type, servers_level1, servers_level2)

def run_simulation(input_file, output_prefix):
    try:
        params = read_parameters(input_file)
        mean_interarrival, mean_service, total_simulation_time, \
        distribution_type, servers_level1, servers_level2 = params
        
        env = simpy.Environment()
        system = SimuladorSecuencial(env, mean_interarrival, mean_service,
                                   servers_level1, servers_level2, distribution_type)
        env.run(until=total_simulation_time)
        
        report = system.generate_report()
        output_filename = f"{output_prefix}_{distribution_type}.txt"
        
        with open(output_filename, 'w') as f:
            f.write(report)
        
        print(f"Simulation complete. Report saved to {output_filename}")
        return True
    
    except FileNotFoundError:
        print(f"Error: Cannot open input file {input_file}")
        return False
    except Exception as e:
        print(f"Error running simulation: {str(e)}")
        return False

if __name__ == "__main__":
    input_file = "parameters_9.txt"
    output_prefix = "report_9"
    
    if not run_simulation(input_file, output_prefix):
        print("Creating sample parameters file and running simulation...")
        with open(input_file, 'w') as f:
            f.write("5.0 4.0 1000 1 2 3\n")
        
        run_simulation(input_file, output_prefix)