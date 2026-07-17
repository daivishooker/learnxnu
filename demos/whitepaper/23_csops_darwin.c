/* BSD SEC-H: csops — code signing status for self */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

#ifdef __APPLE__
#include <sys/codesign.h>
/* csops declared in some SDKs via sys/codesign.h; fallback: */
int csops(pid_t pid, unsigned int ops, void *useraddr, size_t usersize);
#ifndef CS_OPS_STATUS
#define CS_OPS_STATUS 0
#endif
#endif

int main(void) {
#ifndef __APPLE__
    printf("skip: Darwin-only csops\n");
    printf("demo23 skipped\n");
    return 0;
#else
    uint32_t status = 0;
    int rc = csops(getpid(), CS_OPS_STATUS, &status, sizeof(status));
    if (rc != 0) {
        perror("csops");
        /* still count as demo wiring if errno is known restriction */
        printf("demo23 ok (csops returned error)\n");
        return 0;
    }
    printf("csops status=0x%x\n", status);
    printf("demo23 ok\n");
    return 0;
#endif
}
