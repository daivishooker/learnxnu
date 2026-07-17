/* BSD: pipe + poll — event multiplex */
#include <poll.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int fds[2];
    if (pipe(fds) != 0) { perror("pipe"); return 1; }
    if (write(fds[1], "x", 1) != 1) { perror("write"); return 1; }
    struct pollfd pfd = { .fd = fds[0], .events = POLLIN };
    int n = poll(&pfd, 1, 1000);
    if (n != 1 || !(pfd.revents & POLLIN)) {
        fprintf(stderr, "poll failed n=%d revents=0x%x\n", n, pfd.revents);
        return 1;
    }
    char c;
    read(fds[0], &c, 1);
    close(fds[0]);
    close(fds[1]);
    printf("poll ready got=%c\n", c);
    printf("demo14 ok\n");
    return 0;
}
