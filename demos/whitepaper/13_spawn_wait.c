/* BSD: posix_spawn / waitpid — process */
#include <spawn.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>

extern char **environ;

int main(void) {
    pid_t pid = 0;
    char *argv[] = { "/bin/true", NULL };
#ifdef __linux__
    argv[0] = "/usr/bin/true";
#endif
    int rc = posix_spawn(&pid, argv[0], NULL, NULL, argv, environ);
    if (rc != 0) {
        /* fallback path for minimal environments */
        argv[0] = "/bin/echo";
        char *argv2[] = { "/bin/echo", "spawn", NULL };
        rc = posix_spawn(&pid, argv2[0], NULL, NULL, argv2, environ);
        if (rc != 0) {
            fprintf(stderr, "posix_spawn: %d\n", rc);
            return 1;
        }
    }
    int status = 0;
    if (waitpid(pid, &status, 0) < 0) { perror("waitpid"); return 1; }
    printf("spawned pid=%d status=%d\n", (int)pid, status);
    printf("demo13 ok\n");
    return 0;
}
