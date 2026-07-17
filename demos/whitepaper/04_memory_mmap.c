/* BSD→Mach: mmap/mprotect/munmap */
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(void) {
    size_t pagesz = (size_t)sysconf(_SC_PAGESIZE);
    void *p = mmap(NULL, pagesz, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    memcpy(p, "mmap-ok", 8);
    if (mprotect(p, pagesz, PROT_READ) != 0) { perror("mprotect"); return 1; }
    printf("byte0=%c\n", ((char *)p)[0]);
    if (munmap(p, pagesz) != 0) { perror("munmap"); return 1; }
    printf("demo04 ok\n");
    return 0;
}
