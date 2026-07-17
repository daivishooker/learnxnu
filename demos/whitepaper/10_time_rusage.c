/* BSD: gettimeofday / getrusage */
#include <stdio.h>
#include <sys/resource.h>
#include <sys/time.h>

int main(void) {
    struct timeval tv;
    struct rusage ru;
    if (gettimeofday(&tv, NULL) != 0) { perror("gettimeofday"); return 1; }
    if (getrusage(RUSAGE_SELF, &ru) != 0) { perror("getrusage"); return 1; }
    printf("sec=%ld usec=%ld maxrss=%ld\n",
           (long)tv.tv_sec, (long)tv.tv_usec, (long)ru.ru_maxrss);
    printf("demo10 ok\n");
    return 0;
}
