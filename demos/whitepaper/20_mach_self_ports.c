/* Mach traps: task_self / thread_self / host_self / mach_reply_port */
#include <stdio.h>

#ifdef __APPLE__
#include <mach/mach.h>
#endif

int main(void) {
#ifndef __APPLE__
    printf("skip: Darwin-only mach self ports\n");
    printf("demo20 skipped\n");
    return 0;
#else
    mach_port_t task = mach_task_self();
    mach_port_t thread = mach_thread_self();
    mach_port_t host = mach_host_self();
    mach_port_t reply = mach_reply_port();
    printf("task=%u thread=%u host=%u reply=%u\n",
           task, thread, host, reply);
    mach_port_deallocate(task, thread);
    mach_port_deallocate(task, host);
    printf("demo20 ok\n");
    return 0;
#endif
}
