/* Mach traps: mach_vm_allocate / protect / deallocate */
#include <stdio.h>
#include <string.h>

#ifdef __APPLE__
#include <mach/mach.h>
#include <mach/mach_vm.h>
#endif

int main(void) {
#ifndef __APPLE__
    printf("skip: Darwin-only mach_vm\n");
    printf("demo21 skipped\n");
    return 0;
#else
    mach_vm_address_t addr = 0;
    mach_vm_size_t size = 4096;
    kern_return_t kr = mach_vm_allocate(mach_task_self(), &addr, size, VM_FLAGS_ANYWHERE);
    if (kr != KERN_SUCCESS) { fprintf(stderr, "allocate %d\n", kr); return 1; }
    memcpy((void *)(uintptr_t)addr, "V", 1);
    kr = mach_vm_protect(mach_task_self(), addr, size, FALSE, VM_PROT_READ);
    if (kr != KERN_SUCCESS) { fprintf(stderr, "protect %d\n", kr); return 1; }
    printf("mach_vm addr=0x%llx byte=%c\n", (unsigned long long)addr,
           *(char *)(uintptr_t)addr);
    mach_vm_deallocate(mach_task_self(), addr, size);
    printf("demo21 ok\n");
    return 0;
#endif
}
