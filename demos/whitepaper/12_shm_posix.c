/* BSD: shm_open / ftruncate / mmap / shm_unlink — SEC-M shared mem */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    const char *name = "/learnxnu_wp_12";
    shm_unlink(name);
    int fd = shm_open(name, O_CREAT | O_RDWR, 0600);
    if (fd < 0) { perror("shm_open"); return 1; }
    if (ftruncate(fd, 4096) != 0) { perror("ftruncate"); return 1; }
    void *p = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }
    memcpy(p, "shm-ok", 7);
    printf("shm=%s\n", (char *)p);
    munmap(p, 4096);
    close(fd);
    shm_unlink(name);
    printf("demo12 ok\n");
    return 0;
}
