/* BSD: openat/fstatat/unlinkat — *at family */
#include <fcntl.h>
#include <stdio.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    const char *dir = "/tmp";
    const char *name = "learnxnu_wp_03.txt";
    int dfd = open(dir, O_RDONLY | O_DIRECTORY);
    if (dfd < 0) { perror("open dir"); return 1; }
    int fd = openat(dfd, name, O_CREAT | O_TRUNC | O_WRONLY, 0600);
    if (fd < 0) { perror("openat"); return 1; }
    close(fd);
    struct stat st;
    if (fstatat(dfd, name, &st, 0) != 0) { perror("fstatat"); return 1; }
    if (unlinkat(dfd, name, 0) != 0) { perror("unlinkat"); return 1; }
    close(dfd);
    printf("created size=%lld then unlinked\n", (long long)st.st_size);
    printf("demo03 ok\n");
    return 0;
}
