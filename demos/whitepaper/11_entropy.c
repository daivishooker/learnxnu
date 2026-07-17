/* BSD SEC-H: getentropy */
#define _DEFAULT_SOURCE
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#if defined(__APPLE__) || defined(__linux__)
int getentropy(void *buf, size_t buflen);
#endif

int main(void) {
    unsigned char buf[16];
    memset(buf, 0, sizeof(buf));
#if defined(__APPLE__) || defined(__linux__)
    if (getentropy(buf, sizeof(buf)) != 0) {
        perror("getentropy");
        return 1;
    }
#else
    FILE *f = fopen("/dev/urandom", "rb");
    if (!f || fread(buf, 1, sizeof(buf), f) != sizeof(buf)) {
        perror("urandom");
        return 1;
    }
    if (f) fclose(f);
#endif
    printf("entropy:");
    for (size_t i = 0; i < sizeof(buf); i++) printf(" %02x", buf[i]);
    printf("\n");
    printf("demo11 ok\n");
    return 0;
}
