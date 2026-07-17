/* BSD: getpid/getppid/getuid/geteuid/getgid/getegid — process/cred */
#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("pid=%d ppid=%d uid=%d euid=%d gid=%d egid=%d\n",
           (int)getpid(), (int)getppid(),
           (int)getuid(), (int)geteuid(),
           (int)getgid(), (int)getegid());
    printf("demo01 ok\n");
    return 0;
}
