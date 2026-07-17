CC ?= cc
CFLAGS ?= -Wall -Wextra -O0
PORTABLE = \
	01_process_ids \
	02_file_basic \
	03_file_at \
	04_memory_mmap \
	05_pipe_fcntl \
	06_socket_udp \
	07_signal_basic \
	08_pthread_sync \
	09_pthread_cancel \
	10_time_rusage \
	11_entropy \
	12_shm_posix \
	13_spawn_wait \
	14_event_poll

DARWIN = \
	20_mach_self_ports \
	21_mach_vm \
	22_mach_msg_bootstrap \
	23_csops_darwin

.PHONY: all check check-darwin clean

all: $(PORTABLE)

check: $(PORTABLE)
	@for t in $(PORTABLE); do echo "== $$t =="; ./$$t || exit 1; done
	@echo "all portable demos ok"

check-darwin: $(DARWIN)
	@for t in $(DARWIN); do echo "== $$t =="; ./$$t || exit 1; done
	@echo "all darwin demos ok"

08_pthread_sync 09_pthread_cancel: LDLIBS += -lpthread
12_shm_posix: LDLIBS += -lrt -lpthread

% : %.c
	$(CC) $(CFLAGS) -o $@ $< $(LDLIBS)

clean:
	rm -f $(PORTABLE) $(DARWIN)
