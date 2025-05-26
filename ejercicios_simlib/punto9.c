#include "simlib.h"

#define EVENT_ARRIVAL 1
#define EVENT_DEPARTURE1 2
#define EVENT_DEPARTURE2 3
#define LIST_QUEUE1 1
#define LIST_SERVER1 2
#define LIST_QUEUE2 3
#define LIST_SERVER2 4
#define SAMPST_DELAYS_Q1 1    // Separate delay tracking for Queue 1
#define SAMPST_DELAYS_Q2 2    // Separate delay tracking for Queue 2
#define SAMPST_TOTAL_TIME 3   // For total system time
#define STREAM_INTERARRIVAL 1
#define STREAM_SERVICE 2

int num_custs_delayed, total_simulation_time, num_completed_customers, distribution_type;
int servers_level1, servers_level2;  // Number of servers at each level
float mean_interarrival, mean_service;
FILE *infile, *outfile;

float get_interarrival_time() {
    switch (distribution_type) {
        case 1: // Exponential interarrival
        case 3:
            return expon(mean_interarrival, STREAM_INTERARRIVAL);
        case 2: // Constant interarrival
        case 4:
            return mean_interarrival; // Constant time = mean
        default:
            return expon(mean_interarrival, STREAM_INTERARRIVAL); // Default to exponential
    }
}

float get_service_time() {
    switch (distribution_type) {
        case 1: // Exponential service
        case 2:
            return expon(mean_service, STREAM_SERVICE);
        case 3: // Constant service
        case 4:
            return mean_service; // Constant time = mean
        default:
            return expon(mean_service, STREAM_SERVICE); // Default to exponential
    }
}

void init_model(void) {
    num_custs_delayed = 0;
    num_completed_customers = 0;
    event_schedule(sim_time + get_interarrival_time(), EVENT_ARRIVAL);
}

void arrive(void) {
    event_schedule(sim_time + get_interarrival_time(), EVENT_ARRIVAL);

    // Store arrival time in transfer[1] and queue1 entry time in transfer[2]
    transfer[1] = sim_time;  // Arrival time
    transfer[2] = sim_time;  // Initially same as arrival, may be updated if queued
    
    if (list_size[LIST_SERVER1] >= servers_level1) {
        list_file(LAST, LIST_QUEUE1);
    }
    else {
        sampst(0.0, SAMPST_DELAYS_Q1);  // No delay in queue 1
        ++num_custs_delayed;
        list_file(FIRST, LIST_SERVER1);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE1);
    }
}

void depart1(void) {
    // Remove the customer who just finished service at server1
    list_remove(FIRST, LIST_SERVER1);

    // Process this customer's movement to level2
    transfer[3] = sim_time;  // Time entering queue2/service2
    
    if (list_size[LIST_SERVER2] >= servers_level2) {
        transfer[4] = sim_time;  // Record queue2 entry time
        list_file(LAST, LIST_QUEUE2);
    }
    else {
        sampst(0.0, SAMPST_DELAYS_Q2);  // No delay in queue2
        list_file(FIRST, LIST_SERVER2);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE2);
    }

    // Now check if there are customers in queue1 to serve in server1
    if (list_size[LIST_QUEUE1] > 0) {
        list_remove(FIRST, LIST_QUEUE1);
        sampst(sim_time - transfer[2], SAMPST_DELAYS_Q1);  // Queue1 delay
        ++num_custs_delayed;
        list_file(FIRST, LIST_SERVER1);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE1);
    }
}

void depart2(void) {
    // Remove the customer who just finished service at server2
    list_remove(FIRST, LIST_SERVER2);

    // Calculate and record total system time using original arrival time
    float system_time = sim_time - transfer[1];
    sampst(system_time, SAMPST_TOTAL_TIME);
    ++num_completed_customers;

    // Check if there are customers in queue2 to serve
    if (list_size[LIST_QUEUE2] > 0) {
        list_remove(FIRST, LIST_QUEUE2);
        sampst(sim_time - transfer[4], SAMPST_DELAYS_Q2);  // Queue2 delay
        list_file(FIRST, LIST_SERVER2);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE2);
    }
}

void report(void) {
    fprintf(outfile, "\nDelays in Queue 1, in minutes:\n");
    out_sampst(outfile, SAMPST_DELAYS_Q1, SAMPST_DELAYS_Q1);
    
    fprintf(outfile, "\nDelays in Queue 2, in minutes:\n");
    out_sampst(outfile, SAMPST_DELAYS_Q2, SAMPST_DELAYS_Q2);
    
    fprintf(outfile, "\nTotal System Time (arrival to final departure), in minutes:\n");
    out_sampst(outfile, SAMPST_TOTAL_TIME, SAMPST_TOTAL_TIME);
    
    fprintf(outfile, "\nQueue lengths and server utilization:\n");
    out_filest(outfile, LIST_QUEUE1, LIST_SERVER1);
    out_filest(outfile, LIST_QUEUE2, LIST_SERVER2);
    
    fprintf(outfile, "\nTime simulation ended:%12.3f minutes\n", sim_time);
    fprintf(outfile, "Number of customers completed both services:%8d\n", num_completed_customers);
    fprintf(outfile, "Number of servers at level 1: %d\n", servers_level1);
    fprintf(outfile, "Number of servers at level 2: %d\n", servers_level2);
}

int main() {
    char outfilename[20];

    infile = fopen("parameters_9.txt", "r");
    if (infile == NULL) {
        printf("Error: cannot open input file mm9smlb.in\n");
        return 1;
    }

    // Read input parameters including server counts
    fscanf(infile, "%f %f %d %d %d %d", 
           &mean_interarrival, &mean_service, 
           &total_simulation_time, &distribution_type,
           &servers_level1, &servers_level2);

    // Generate output filename
    sprintf(outfilename, "report_9_%d.txt", distribution_type);

    outfile = fopen(outfilename, "w");
    if (outfile == NULL) {
        printf("Error: cannot open output file %s\n", outfilename);
        fclose(infile);
        return 1;
    }

    fprintf(outfile, "Multi-server queueing system using simlib\n\n");
    fprintf(outfile, "Mean interarrival time%11.3f minutes\n\n", mean_interarrival);
    fprintf(outfile, "Mean service time%16.3f minutes\n\n", mean_service);
    fprintf(outfile, "Total simulation time%12d minutes\n\n", total_simulation_time);
    fprintf(outfile, "Distribution type: %d\n", distribution_type);
    switch (distribution_type) {
        case 1:
            fprintf(outfile, "Interarrival: Exponential, Service: Exponential\n");
            break;
        case 2:
            fprintf(outfile, "Interarrival: Constant, Service: Exponential\n");
            break;
        case 3:
            fprintf(outfile, "Interarrival: Exponential, Service: Constant\n");
            break;
        case 4:
            fprintf(outfile, "Interarrival: Constant, Service: Constant\n");
            break;
        default:
            fprintf(outfile, "Invalid distribution type. Defaulting to Exponential/Exponential.\n");
    }
    fprintf(outfile, "Number of servers at level 1: %d\n", servers_level1);
    fprintf(outfile, "Number of servers at level 2: %d\n\n", servers_level2);

    maxatr = 10;
    maxlist = 26;
    init_simlib();
    init_model();
    while (sim_time < total_simulation_time) {
        timing();
        switch (next_event_type) {
            case EVENT_ARRIVAL:
                arrive();
                break;
            case EVENT_DEPARTURE1:
                depart1();
                break;
            case EVENT_DEPARTURE2:
                depart2();
                break;
        }
    }
    report();
    fclose(infile);
    fclose(outfile);

    return 0;
}