/* Darwin: pthread_* → psynch_*; portable mutex/cond/rwlock */
#include <pthread.h>
#include <stdio.h>

static pthread_mutex_t m = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t c = PTHREAD_COND_INITIALIZER;
static pthread_rwlock_t rw = PTHREAD_RWLOCK_INITIALIZER;
static int ready;
static int value;

static void *worker(void *arg) {
    (void)arg;
    pthread_mutex_lock(&m);
    ready = 1;
    pthread_cond_signal(&c);
    pthread_mutex_unlock(&m);

    pthread_rwlock_wrlock(&rw);
    value = 7;
    pthread_rwlock_unlock(&rw);
    return NULL;
}

int main(void) {
    pthread_t t;
    if (pthread_create(&t, NULL, worker, NULL) != 0) { perror("create"); return 1; }
    pthread_mutex_lock(&m);
    while (!ready) pthread_cond_wait(&c, &m);
    pthread_mutex_unlock(&m);
    pthread_join(t, NULL);
    pthread_rwlock_rdlock(&rw);
    printf("value=%d\n", value);
    pthread_rwlock_unlock(&rw);
    printf("demo08 ok\n");
    return 0;
}
