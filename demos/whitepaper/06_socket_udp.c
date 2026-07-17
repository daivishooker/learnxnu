/* BSD: socket/bind/getsockname/sendto/recvfrom/close */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

int main(void) {
    int s = socket(AF_INET, SOCK_DGRAM, 0);
    if (s < 0) { perror("socket"); return 1; }
    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = 0;
    if (bind(s, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        perror("bind"); return 1;
    }
    socklen_t alen = sizeof(addr);
    if (getsockname(s, (struct sockaddr *)&addr, &alen) != 0) {
        perror("getsockname"); return 1;
    }
    const char *msg = "udp";
    if (sendto(s, msg, 3, 0, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("sendto"); return 1;
    }
    char buf[8];
    struct sockaddr_in from;
    socklen_t flen = sizeof(from);
    ssize_t n = recvfrom(s, buf, sizeof(buf), 0, (struct sockaddr *)&from, &flen);
    if (n < 0) { perror("recvfrom"); return 1; }
    buf[n] = '\0';
    close(s);
    printf("udp port=%d got=%s\n", ntohs(addr.sin_port), buf);
    printf("demo06 ok\n");
    return 0;
}
