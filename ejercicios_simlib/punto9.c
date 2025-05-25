#include "simlib.h"

#define EVENT_ARRIVAL 1
#define EVENT_DEPARTURE1 2
#define EVENT_DEPARTURE2 3
#define LIST_QUEUE1 1
#define LIST_SERVER1 2
#define LIST_QUEUE2 3
#define LIST_SERVER2 4
#define SAMPST_DELAYS 1
#define STREAM_INTERARRIVAL 1
#define STREAM_SERVICE 2

int num_custs_delayed, total_simulation_time, num_completed_customers, distribution_type,servers_level1, servers_level2;
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
    event_schedule(sim_time + get_interarrival_time(), EVENT_ARRIVAL);
}

void arrive(void) {
    event_schedule(sim_time + get_interarrival_time(), EVENT_ARRIVAL);
    
    if (list_size[LIST_SERVER1] >= servers_level1) {  // Check against number of servers
        transfer[1] = sim_time;
        list_file(LAST, LIST_QUEUE1);
    }
    else {
        sampst(0.0, SAMPST_DELAYS);
        ++num_custs_delayed;
        list_file(FIRST, LIST_SERVER1);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE1);
    }
}

void depart1(void) {
    if (list_size[LIST_QUEUE1] == 0) {
        list_remove(FIRST, LIST_SERVER1);
    } else {
        list_remove(FIRST, LIST_QUEUE1);
        sampst(sim_time - transfer[1], SAMPST_DELAYS);
        ++num_custs_delayed;
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE1);
    }

    if (list_size[LIST_SERVER2] >= servers_level2) {  // Check against number of servers
        transfer[1] = sim_time;
        list_file(LAST, LIST_QUEUE2);
    }
    else {
        list_file(FIRST, LIST_SERVER2);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE2);
    }
}

void depart2(void) {
    if (list_size[LIST_QUEUE2] == 0) {
        list_remove(FIRST, LIST_SERVER2);
    } else {
        list_remove(FIRST, LIST_QUEUE2);
        event_schedule(sim_time + get_service_time(), EVENT_DEPARTURE2);
    }

    ++num_completed_customers;
}

void report(void) {
    fprintf(outfile, "\nDelays in queue, in minutes:\n");
    out_sampst(outfile, SAMPST_DELAYS, SAMPST_DELAYS);
    fprintf(outfile, "\nQueue length and server utilization:\n");
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
        printf("Error: cannot open input file parameters_9.txt\n");
        return 1;
    }

    // Read input parameters including server counts
    fscanf(infile, "%f %f %d %d %d %d", 
           &mean_interarrival, &mean_service, 
           &total_simulation_time, &distribution_type,
           &servers_level1, &servers_level2);

    // Generate output filename
    sprintf(outfilename, "report_9_%d.txt", distribution_type, servers_level1, servers_level2);

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

    maxatr = 4;
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