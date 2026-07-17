/* Darwin: pthread_cancel → __pthread_markcancel / canceled */
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t c = PTHREAD_COND_INITIALIZER;

static void *worker(void *arg) {
    (void)arg;
    pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
    pthread_setcanceltype(PTHREAD_CANCEL_DEFERRED, NULL);
    pthread_mutex_lock(&m);
    pthread_cond_wait(&c, &m);
    pthread_mutex_unlock(&m);
    return NULL;
}

int main(void) {
    pthread_t t;
    void *ret = NULL;
    if (pthread_create(&t, NULL, worker, NULL) != 0) { perror("create"); return 1; }
    usleep(100 * 1000);
    if (pthread_cancel(t) != 0) { perror("cancel"); return 1; }
    if (pthread_join(t, &ret) != 0) { perror("join"); return 1; }
    if (ret != PTHREAD_CANCELED) { fprintf(stderr, "not canceled\n"); return 1; }
    printf("canceled ok\n");
    printf("demo09 ok\n");
    return 0;
}
