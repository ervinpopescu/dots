#define _DARWIN_C_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#define DESTINATION "tmux-herdr-darwin-helper"

static int open_private_directory(const char *path, uid_t owner) {
  if (path[0] != '/') return -1;
  int fd = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) return -1;
  const char *cursor = path + 1;
  while (*cursor) {
    while (*cursor == '/') ++cursor;
    if (*cursor == '\0') break;
    const char *end = strchr(cursor, '/');
    size_t length = end ? (size_t)(end - cursor) : strlen(cursor);
    if (length == 0 || length >= NAME_MAX ||
        (length == 1 && cursor[0] == '.') ||
        (length == 2 && cursor[0] == '.' && cursor[1] == '.')) {
      close(fd); return -1;
    }
    char component[NAME_MAX];
    memcpy(component, cursor, length); component[length] = '\0';
    int next = openat(fd, component,
                      O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (next < 0) { close(fd); return -1; }
    struct stat info;
    if (fstat(next, &info) < 0 || !S_ISDIR(info.st_mode) ||
        (info.st_uid != owner && info.st_uid != 0) ||
        ((info.st_mode & (S_IWGRP | S_IWOTH)) != 0 &&
         !(info.st_uid == 0 && (info.st_mode & (S_ISUID | S_ISGID | S_ISVTX | S_IRWXU | S_IRWXG | S_IRWXO)) ==
           (S_ISVTX | S_IRWXU | S_IRWXG | S_IRWXO)))) {
      close(next); close(fd); return -1;
    }
    close(fd); fd = next;
    cursor = end ? end + 1 : cursor + length;
  }
  struct stat leaf;
  if (fstat(fd, &leaf) < 0 || !S_ISDIR(leaf.st_mode) ||
      leaf.st_uid != owner || (leaf.st_mode & 0777) != 0700 ||
      (leaf.st_mode & 06000) != 0) { close(fd); return -1; }
  return fd;
}

static int create_install_temp(int directory, char *name, size_t capacity) {
  for (unsigned attempt = 0; attempt < 32U; ++attempt) {
    uint64_t entropy = 0;
    arc4random_buf(&entropy, sizeof entropy);
    int length = snprintf(name, capacity, ".tmux-herdr-install-%016llx.tmp",
                          (unsigned long long)entropy);
    if (length < 0 || (size_t)length >= capacity) return -1;
    int fd = openat(directory, name,
                    O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                    0700);
    if (fd >= 0) return fd;
    if (errno != EEXIST) return -1;
  }
  return -1;
}

static int copy_file(int source, int destination) {
  char buffer[16384];
  for (;;) {
    ssize_t count = read(source, buffer, sizeof buffer);
    if (count < 0 && errno == EINTR) continue;
    if (count < 0) return -1;
    if (count == 0) return 0;
    size_t written = 0;
    while (written < (size_t)count) {
      ssize_t result = write(destination, buffer + written,
                              (size_t)count - written);
      if (result < 0 && errno == EINTR) continue;
      if (result <= 0) return -1;
      written += (size_t)result;
    }
  }
}

int main(int argc, char **argv) {
  if (argc != 3 || argv[1][0] != '/' || argv[2][0] != '/') return 2;
  uid_t owner = geteuid();
  int source = open(argv[1], O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (source < 0) return 1;
  struct stat source_info;
  if (fstat(source, &source_info) < 0 || !S_ISREG(source_info.st_mode) ||
      source_info.st_uid != owner || (source_info.st_mode & 0777) != 0700 ||
      source_info.st_nlink != 1) { close(source); return 1; }
  int directory = open_private_directory(argv[2], owner);
  if (directory < 0) { close(source); return 1; }
  struct stat existing;
  if (fstatat(directory, DESTINATION, &existing, AT_SYMLINK_NOFOLLOW) == 0) {
    if (S_ISLNK(existing.st_mode) || !S_ISREG(existing.st_mode) ||
        existing.st_uid != owner || (existing.st_mode & 0777) != 0700 ||
        existing.st_nlink != 1) { close(directory); close(source); return 1; }
  } else if (errno != ENOENT) { close(directory); close(source); return 1; }
  char temporary_name[NAME_MAX];
  int temporary = create_install_temp(directory, temporary_name,
                                      sizeof temporary_name);
  if (temporary < 0) { close(directory); close(source); return 1; }
  int status = copy_file(source, temporary);
  struct stat copied;
  if (status == 0 && (fstat(temporary, &copied) < 0 ||
      !S_ISREG(copied.st_mode) || copied.st_uid != owner ||
      (copied.st_mode & 0777) != 0700 || copied.st_nlink != 1 ||
      fsync(temporary) < 0)) status = -1;
  close(source); close(temporary);
  if (status == 0 && (renameat(directory, temporary_name, directory,
                               DESTINATION) < 0 || fsync(directory) < 0))
    status = -1;
  close(directory);
  return status == 0 ? 0 : 1;
}
