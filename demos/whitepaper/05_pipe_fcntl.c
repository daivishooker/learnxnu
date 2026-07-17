/* BSD: pipe/fcntl/read/write */
#include <fcntl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int fds[2];
    char buf[8];
    if (pipe(fds) != 0) { perror("pipe"); return 1; }
    int fl = fcntl(fds[1], F_GETFL);
    if (fl < 0) { perror("fcntl"); return 1; }
    if (write(fds[1], "P", 1) != 1) { perror("write"); return 1; }
    if (read(fds[0], buf, 1) != 1) { perror("read"); return 1; }
    close(fds[0]);
    close(fds[1]);
    printf("pipe got %c flags=0x%x\n", buf[0], fl);
    printf("demo05 ok\n");
    return 0;
}
