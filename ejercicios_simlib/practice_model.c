#include "simlib.h"

#define EVENT_ARRIVAL 1
#define EVENT_DEPARTURE 2
#define LIST_QUEUE 1
#define LIST_SERVER 2
#define SAMPST_DELAYS 1
#define STREAM_INTERARRIVAL 1
#define STREAM_SERVICE 2

int num_custs_delayed,num_delays_required;
float mean_interarrival, mean_service;
FILE *infile, *outfile;

void init_model(void){
    num_custs_delayed = 0;
    event_schedule(sim_time + expon(mean_interarrival, STREAM_INTERARRIVAL), EVENT_ARRIVAL);
}

void arrive(void){
    event_schedule(sim_time + expon(mean_interarrival, STREAM_INTERARRIVAL), EVENT_ARRIVAL);
    if (list_size[LIST_SERVER] == 1){
        transfer[1] = sim_time;
        list_file(LAST, LIST_QUEUE);
    }
    else{
        sampst(0.0, SAMPST_DELAYS);
        ++num_custs_delayed;
        list_file(FIRST, LIST_SERVER);
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE);
    }
}

void depart(void){
    if (list_size[LIST_QUEUE] == 0){
        list_remove(FIRST, LIST_SERVER);
    }
    else{
        list_remove(FIRST, LIST_QUEUE);
        sampst(sim_time - transfer[1], SAMPST_DELAYS);
        ++num_custs_delayed;
        event_schedule(sim_time + expon(mean_service, STREAM_SERVICE), EVENT_DEPARTURE);
    }
}
void report(void){
    fprintf(outfile, "\nDelays in queue, in minutes:\n");
    out_sampst(outfile, SAMPST_DELAYS, SAMPST_DELAYS);
    fprintf(outfile, "\nQueue length (1) and server utilization (2):\n");
    out_filest(outfile, LIST_QUEUE, LIST_SERVER);
    fprintf(outfile, "\nTime simulation ended:%12.3f minutes\n", sim_time);}

int main(){
    infile = fopen("mm1smlb.in", "r");
    if (infile == NULL) {
        printf("Error: cannot open input file mm1smlb.in\n");
        return 1;
    }
    outfile = fopen("mm1smlb.out", "w");
    if (outfile == NULL) {
        printf("Error: cannot open output file mm1smlb.out\n");
        fclose(infile);
        return 1;
    }
    fscanf(infile, "%f %f %d", &mean_interarrival, &mean_service, &num_delays_required);
    fprintf(outfile, "Single-server queueing system using simlib\n\n");
    fprintf(outfile, "Mean interarrival time%11.3f minutes\n\n", mean_interarrival);
    fprintf(outfile, "Mean service time%16.3f minutes\n\n", mean_service);
    fprintf(outfile, "Number of customers%14d\n\n\n", num_delays_required);

    maxatr = 4;
    maxlist = 26;
    init_simlib();
    init_model();
    while (num_custs_delayed < num_delays_required) {
        timing();
        switch (next_event_type){
            case EVENT_ARRIVAL:
                arrive();
                break;
            case EVENT_DEPARTURE:
                depart();
                break;
        }
    }
    report();
    fclose(infile);
    fclose(outfile);

    return 0;
}
