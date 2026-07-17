/* BSD: open/write/read/lseek/close/stat — file */
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    const char *path = "/tmp/learnxnu_wp_02.txt";
    const char *msg = "hello-whitepaper";
    char buf[64];
    struct stat st;
    int fd = open(path, O_CREAT | O_TRUNC | O_RDWR, 0600);
    if (fd < 0) { perror("open"); return 1; }
    if (write(fd, msg, strlen(msg)) < 0) { perror("write"); return 1; }
    if (lseek(fd, 0, SEEK_SET) < 0) { perror("lseek"); return 1; }
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    if (n < 0) { perror("read"); return 1; }
    buf[n] = '\0';
    if (fstat(fd, &st) != 0) { perror("fstat"); return 1; }
    close(fd);
    unlink(path);
    printf("readback=%s size=%lld\n", buf, (long long)st.st_size);
    printf("demo02 ok\n");
    return 0;
}
