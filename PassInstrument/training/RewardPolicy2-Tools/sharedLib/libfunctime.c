#include "headers/c/thesis_api.h"
// time ops
#include <sys/time.h>
#include <sys/resource.h>
// file ops
#include <unistd.h>
#include <sys/stat.h>
#include <fcntl.h>
// snprintf
#include <stdio.h>

unsigned long long __thesis_getUserTime() {
  struct rusage usage;
  struct timeval time;
  getrusage(RUSAGE_SELF, &usage);
  time = usage.ru_utime;
  return time.tv_sec*1000000 + time.tv_usec;
}

void __thesis_LogTiming(unsigned long long entryTime, char *FuncName) {
  unsigned long long elapsed = __thesis_getUserTime() - entryTime;
  /* prepare the log content */
  char buf[128] = {0};
  snprintf(buf, sizeof(buf), "%s;%llu\n", FuncName, elapsed);
  /* log to file */
  int fd;
  fd = open("/tmp/test-IR-write", O_WRONLY|O_APPEND|O_CREAT);
  write(fd, buf, sizeof(buf));
  close(fd);
}
