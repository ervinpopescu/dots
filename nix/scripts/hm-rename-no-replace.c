#define _GNU_SOURCE

#include <errno.h>
#include <stdio.h>

#if defined(__linux__)
#include <fcntl.h>
#include <linux/fs.h>
#include <sys/syscall.h>
#include <unistd.h>
#elif defined(__APPLE__)
#include <unistd.h>
#else
#error "hm-rename-no-replace supports only Linux and macOS"
#endif

int main(int argc, char **argv) {
  int result;

  if (argc != 3) {
    fprintf(stderr, "usage: hm-rename-no-replace SOURCE TARGET\n");
    return 2;
  }

#if defined(__linux__)
  result = syscall(SYS_renameat2, AT_FDCWD, argv[1], AT_FDCWD, argv[2],
                   RENAME_NOREPLACE);
#elif defined(__APPLE__)
  result = renamex_np(argv[1], argv[2], RENAME_EXCL);
#endif

  if (result == 0) {
    return 0;
  }
  if (errno == EEXIST || errno == ENOTEMPTY) {
    return 3;
  }

  perror("hm-rename-no-replace");
  return 1;
}
