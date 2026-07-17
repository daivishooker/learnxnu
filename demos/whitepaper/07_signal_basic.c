/* BSD: sigaction / raise(→kill self) */
#include <signal.h>
#include <stdio.h>
#include <string.h>

static volatile sig_atomic_t hit;

static void handler(int sig) {
    (void)sig;
    hit = 1;
}

int main(void) {
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = handler;
    sigemptyset(&sa.sa_mask);
    if (sigaction(SIGUSR1, &sa, NULL) != 0) { perror("sigaction"); return 1; }
    if (raise(SIGUSR1) != 0) { perror("raise"); return 1; }
    if (!hit) { fprintf(stderr, "signal not delivered\n"); return 1; }
    printf("SIGUSR1 handled\n");
    printf("demo07 ok\n");
    return 0;
}
