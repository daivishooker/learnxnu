#include <jni.h>
#include <fcntl.h>
#include <unistd.h>
#include <cstring>
#include <cstdio>

/**
 * 轻量 native 辅助：读取 TracerPid。
 * 仅作教学/基线，不构成对抗级反调试方案。
 */
static int read_tracer_pid() {
    int fd = open("/proc/self/status", O_RDONLY);
    if (fd < 0) {
        return -1;
    }

    char buf[2048];
    ssize_t n = read(fd, buf, sizeof(buf) - 1);
    close(fd);
    if (n <= 0) {
        return -1;
    }
    buf[n] = '\0';

    const char *key = "TracerPid:";
    char *line = strstr(buf, key);
    if (line == nullptr) {
        return -1;
    }
    line += strlen(key);
    while (*line == ' ' || *line == '\t') {
        ++line;
    }
    int pid = 0;
    sscanf(line, "%d", &pid);
    return pid;
}

extern "C" JNIEXPORT jint JNICALL
Java_com_example_hardening_NativeGuard_nativeTracerPidInternal(JNIEnv *, jobject) {
    return read_tracer_pid();
}
