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

int num_custs_delayed,num_delays_required,total_simulation_time,num_completed_customers;
float mean_interarrival, mean_service;
FILE *infile, *outfile;

void init_model(void){
    num_custs_delayed = 0;
    event_schedule(sim_time + mean_interarrival, EVENT_ARRIVAL);
}

void arrive(void){
    event_schedule(sim_time + mean_interarrival, EVENT_ARRIVAL);
    
    if (list_size[LIST_SERVER1] == 1){
        transfer[1] = sim_time;
        list_file(LAST, LIST_QUEUE1);
    }
    else {
        sampst(0.0, SAMPST_DELAYS);
        ++num_custs_delayed;
        list_file(FIRST, LIST_SERVER1);
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE1);
    }
}


void depart1(void){
    if (list_size[LIST_QUEUE1] == 0){
        list_remove(FIRST, LIST_SERVER1);
    } else {
        list_remove(FIRST, LIST_QUEUE1);
        sampst(sim_time - transfer[1], SAMPST_DELAYS);
        ++num_custs_delayed;
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE1);
    }

    if (list_size[LIST_SERVER2] == 1){
        transfer[1] = sim_time;
        list_file(LAST, LIST_QUEUE2);
    }
    else {
        list_file(FIRST, LIST_SERVER2);
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE2);
    }
}
void depart2(void){
    if (list_size[LIST_QUEUE2] == 0){
        list_remove(FIRST, LIST_SERVER2);
    } else {
        list_remove(FIRST, LIST_QUEUE2);
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE2);
    }

    ++num_completed_customers;
}

void report(void){
    fprintf(outfile, "\nDelays in queue, in minutes:\n");
    out_sampst(outfile, SAMPST_DELAYS, SAMPST_DELAYS);
    fprintf(outfile, "\nQueue length and server utilization:\n");
    out_filest(outfile, LIST_QUEUE1, LIST_SERVER1);
    out_filest(outfile, LIST_QUEUE2, LIST_SERVER2);
    fprintf(outfile, "\nTime simulation ended:%12.3f minutes\n", sim_time);
    fprintf(outfile, "Number of customers completed both services:%8d\n", num_completed_customers);
}

int main(){
    infile = fopen("mm9smlb.in", "r");
    if (infile == NULL) {
        printf("Error: cannot open input file mm9smlb.in\n");
        return 1;
    }
    outfile = fopen("mm9smlb2.out", "w");
    if (outfile == NULL) {
        printf("Error: cannot open output file mm9smlb.out\n");
        fclose(infile);
        return 1;
    }
    fscanf(infile, "%f %f %d", &mean_interarrival, &mean_service, &total_simulation_time);
    fprintf(outfile, "Single-server queueing system using simlib\n\n");
    fprintf(outfile, "Mean interarrival time%11.3f minutes\n\n", mean_interarrival);
    fprintf(outfile, "Mean service time%16.3f minutes\n\n", mean_service);
    fprintf(outfile, "Total simulation time%12d minutes\n\n", total_simulation_time);

    maxatr = 4;
    maxlist = 26;
    init_simlib();
    init_model();
    while (sim_time < total_simulation_time) {
        timing();
        switch (next_event_type){
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
