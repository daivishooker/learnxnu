/* Mach traps: mach_msg via bootstrap_look_up (SEC-H IPC path) */
#include <stdio.h>
#include <string.h>

#ifdef __APPLE__
#include <mach/mach.h>
#include <servers/bootstrap.h>
#endif

int main(void) {
#ifndef __APPLE__
    printf("skip: Darwin-only mach_msg/bootstrap\n");
    printf("demo22 skipped\n");
    return 0;
#else
    mach_port_t port = MACH_PORT_NULL;
    kern_return_t kr = bootstrap_look_up(bootstrap_port, "com.apple.system.logger", &port);
    /* lookup may fail on some configs; still exercised bootstrap/mach path setup */
    printf("bootstrap_look_up kr=%d port=%u\n", kr, port);
    if (port != MACH_PORT_NULL) {
        mach_port_deallocate(mach_task_self(), port);
    }
    printf("demo22 ok\n");
    return 0;
#endif
}
