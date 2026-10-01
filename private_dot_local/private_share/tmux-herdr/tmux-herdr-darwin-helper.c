#define _DARWIN_C_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#ifdef __APPLE__
#include <libproc.h>
#include <sys/ioctl.h>
#include <sys/proc_info.h>
#include <termios.h>
#endif

#define INPUT_LIMIT (16U * 1024U)
#define OUTPUT_LIMIT (16U * 1024U)
#define RECORD_LIMIT 16384U
#define MAX_PROCESSES 4096U
#define MAX_DEPTH 512U
#define MAX_TEXT (4096U + 1U)
#define SESSION_ID_MAX_BYTES 256U
#define SESSION_PATH_MAX_BYTES 4096U

static void result_ok(void) { (void)puts("{\"ok\":true}"); }

static void result_error(const char *reason) {
  char safe[64];
  size_t out = 0;
  for (const char *p = reason; *p && out + 1 < sizeof safe; ++p) {
    if ((*p >= 'a' && *p <= 'z') || (*p >= '0' && *p <= '9') || *p == '_')
      safe[out++] = *p;
    else
      break;
  }
  safe[out] = '\0';
  if (safe[0] == '\0')
    (void)puts("{\"ok\":false,\"reason\":\"invalid\"}");
  else
    (void)printf("{\"ok\":false,\"reason\":\"%s\"}\n", safe);
}

static int read_request(char *buffer, size_t capacity) {
  size_t used = 0;
  while (used < capacity) {
    ssize_t n = read(STDIN_FILENO, buffer + used, capacity - used);
    if (n < 0 && errno == EINTR)
      continue;
    if (n < 0)
      return -1;
    if (n == 0)
      break;
    used += (size_t)n;
  }
  if (used == capacity) {
    char extra;
    ssize_t n;
    do {
      n = read(STDIN_FILENO, &extra, 1);
    } while (n < 0 && errno == EINTR);
    if (n != 0)
      return -2;
  }
  return (int)used;
}

#ifdef __APPLE__
typedef struct {
  const char *p;
  const char *end;
} json_parser;

static void jp_ws(json_parser *parser) {
  while (parser->p < parser->end &&
         (*parser->p == ' ' || *parser->p == '\t' || *parser->p == '\r' ||
          *parser->p == '\n'))
    ++parser->p;
}

static int jp_char(json_parser *parser, char expected) {
  jp_ws(parser);
  if (parser->p >= parser->end || *parser->p != expected)
    return -1;
  ++parser->p;
  return 0;
}

static int hex_value(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  return -1;
}

static int append_codepoint(char *out, size_t capacity, size_t *used,
                            uint32_t codepoint) {
  if (codepoint == 0 || codepoint == 0x7f || codepoint > 0x10ffff ||
      (codepoint >= 0xd800 && codepoint <= 0xdfff))
    return -1;
  unsigned char encoded[4];
  size_t length;
  if (codepoint < 0x80) {
    encoded[0] = (unsigned char)codepoint;
    length = 1;
  } else if (codepoint < 0x800) {
    encoded[0] = (unsigned char)(0xc0 | (codepoint >> 6));
    encoded[1] = (unsigned char)(0x80 | (codepoint & 0x3f));
    length = 2;
  } else if (codepoint < 0x10000) {
    encoded[0] = (unsigned char)(0xe0 | (codepoint >> 12));
    encoded[1] = (unsigned char)(0x80 | ((codepoint >> 6) & 0x3f));
    encoded[2] = (unsigned char)(0x80 | (codepoint & 0x3f));
    length = 3;
  } else {
    encoded[0] = (unsigned char)(0xf0 | (codepoint >> 18));
    encoded[1] = (unsigned char)(0x80 | ((codepoint >> 12) & 0x3f));
    encoded[2] = (unsigned char)(0x80 | ((codepoint >> 6) & 0x3f));
    encoded[3] = (unsigned char)(0x80 | (codepoint & 0x3f));
    length = 4;
  }
  if (*used + length >= capacity)
    return -1;
  memcpy(out + *used, encoded, length);
  *used += length;
  out[*used] = '\0';
  return 0;
}

static int jp_hex4(json_parser *parser, uint32_t *value) {
  if (parser->end - parser->p < 4)
    return -1;
  uint32_t result = 0;
  for (int i = 0; i < 4; ++i) {
    int digit = hex_value(parser->p[i]);
    if (digit < 0)
      return -1;
    result = (result << 4) | (uint32_t)digit;
  }
  parser->p += 4;
  *value = result;
  return 0;
}

static int jp_string(json_parser *parser, char *out, size_t capacity) {
  size_t used = 0;
  if (jp_char(parser, '"') != 0)
    return -1;
  while (parser->p < parser->end) {
    unsigned char c = (unsigned char)*parser->p++;
    if (c == '"') {
      out[used] = '\0';
      return 0;
    }
    if (c < 0x20)
      return -1;
    if (c == '\\') {
      if (parser->p >= parser->end)
        return -1;
      char escaped = *parser->p++;
      if (escaped == 'u') {
        uint32_t codepoint;
        if (jp_hex4(parser, &codepoint) != 0)
          return -1;
        if (codepoint >= 0xd800 && codepoint <= 0xdbff) {
          if (parser->end - parser->p < 6 || parser->p[0] != '\\' ||
              parser->p[1] != 'u')
            return -1;
          parser->p += 2;
          uint32_t low;
          if (jp_hex4(parser, &low) != 0 || low < 0xdc00 || low > 0xdfff)
            return -1;
          codepoint = 0x10000 + ((codepoint - 0xd800) << 10) +
                      (low - 0xdc00);
        } else if (codepoint >= 0xdc00) {
          return -1;
        }
        if (append_codepoint(out, capacity, &used, codepoint) != 0)
          return -1;
        continue;
      }
      const char *escapes = "\\\"/bfnrt";
      if (!strchr(escapes, escaped))
        return -1;
      unsigned char decoded = escaped;
      if (escaped == 'b') decoded = '\b';
      if (escaped == 'f') decoded = '\f';
      if (escaped == 'n') decoded = '\n';
      if (escaped == 'r') decoded = '\r';
      if (escaped == 't') decoded = '\t';
      if (decoded < 0x20 || used + 1 >= capacity)
        return -1;
      out[used++] = (char)decoded;
      continue;
    }
    if (c < 0x80) {
      if (c == 0x7f || used + 1 >= capacity) return -1;
      out[used++] = (char)c;
      continue;
    }
    int length = (c & 0xe0) == 0xc0 ? 2 :
                 (c & 0xf0) == 0xe0 ? 3 :
                 (c & 0xf8) == 0xf0 ? 4 : 0;
    if (length == 0 || parser->end - parser->p < length - 1)
      return -1;
    uint32_t codepoint = c & ((1 << (8 - length - 1)) - 1);
    for (int i = 1; i < length; ++i) {
      unsigned char continuation = (unsigned char)parser->p[i - 1];
      if ((continuation & 0xc0) != 0x80)
        return -1;
      codepoint = (codepoint << 6) | (continuation & 0x3f);
    }
    parser->p += length - 1;
    if ((length == 2 && codepoint < 0x80) ||
        (length == 3 && codepoint < 0x800) ||
        (length == 4 && codepoint < 0x10000) ||
        append_codepoint(out, capacity, &used, codepoint) != 0)
      return -1;
  }
  return -1;
}

static int jp_integer(json_parser *parser, long long *value) {
  jp_ws(parser);
  const char *start = parser->p;
  if (parser->p < parser->end && *parser->p == '-') ++parser->p;
  const char *digits = parser->p;
  while (parser->p < parser->end && *parser->p >= '0' && *parser->p <= '9')
    ++parser->p;
  if (parser->p == digits)
    return -1;
  if (parser->p - digits > 1 && *digits == '0')
    return -1;
  char number[32];
  size_t length = (size_t)(parser->p - start);
  if (length >= sizeof number)
    return -1;
  memcpy(number, start, length);
  number[length] = '\0';
  char *end = NULL;
  errno = 0;
  long long parsed = strtoll(number, &end, 10);
  if (errno == ERANGE || end == number || *end != '\0')
    return -1;
  *value = parsed;
  return 0;
}

static int valid_pane_id(const char *value) {
  if (value[0] != '%' || value[1] == '\0') return 0;
  for (const char *p = value + 1; *p; ++p)
    if (*p < '0' || *p > '9') return 0;
  return 1;
}

static int valid_session_id(const char *value) {
  size_t n = strlen(value);
  if (n == 0 || n > SESSION_ID_MAX_BYTES) return 0;
  if (!((value[0] >= 'A' && value[0] <= 'Z') ||
        (value[0] >= 'a' && value[0] <= 'z') ||
        (value[0] >= '0' && value[0] <= '9')) ||
      !((value[n - 1] >= 'A' && value[n - 1] <= 'Z') ||
        (value[n - 1] >= 'a' && value[n - 1] <= 'z') ||
        (value[n - 1] >= '0' && value[n - 1] <= '9')))
    return 0;
  for (size_t i = 1; i + 1 < n; ++i) {
    char c = value[i];
    if (!((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
          (c >= '0' && c <= '9') || c == '.' || c == '_' || c == '-'))
      return 0;
  }
  return 1;
}

static int valid_session_value(const char *kind, const char *value) {
  if (strcmp(kind, "id") == 0) return valid_session_id(value);
  size_t length = strlen(value);
  if (strcmp(kind, "path") != 0 || value[0] != '/' ||
      length > SESSION_PATH_MAX_BYTES ||
      length < 6 || strcmp(value + length - 6, ".jsonl") != 0)
    return 0;
  for (const unsigned char *p = (const unsigned char *)value; *p; ++p)
    if (*p < 0x20 || *p == 0x7f) return 0;
  return 1;
}

typedef struct {
  char directory[PATH_MAX];
  char pane_id[128];
  char kind[16];
  char value[MAX_TEXT];
  long long publisher_pid;
} publish_request;

typedef struct {
  char directory[PATH_MAX];
  char pane_id[128];
  char pane_tty[PATH_MAX];
  long long pane_pid;
} resolve_request;

static int parse_object_end(json_parser *parser, int fields);

static int parse_publish_request(const char *json, size_t length,
                                 publish_request *request) {
  json_parser parser = {json, json + length};
  char key[64], operation[16];
  long long version = 0;
  unsigned seen = 0;
  int fields = 0, after_comma = 0;
  if (jp_char(&parser, '{') != 0) return -1;
  for (;;) {
    jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == '}') { if (after_comma) return -1; break; }
    if (jp_string(&parser, key, sizeof key) != 0 || jp_char(&parser, ':') != 0) return -1;
    unsigned bit;
    if (strcmp(key, "v") == 0) { bit = 1; if (seen & bit || jp_integer(&parser, &version) != 0) return -1; }
    else if (strcmp(key, "op") == 0) { bit = 2; if (seen & bit || jp_string(&parser, operation, sizeof operation) != 0) return -1; }
    else if (strcmp(key, "directory") == 0) { bit = 4; if (seen & bit || jp_string(&parser, request->directory, sizeof request->directory) != 0) return -1; }
    else if (strcmp(key, "publisher_pid") == 0) { bit = 8; if (seen & bit || jp_integer(&parser, &request->publisher_pid) != 0) return -1; }
    else if (strcmp(key, "pane_id") == 0) { bit = 16; if (seen & bit || jp_string(&parser, request->pane_id, sizeof request->pane_id) != 0) return -1; }
    else if (strcmp(key, "session_kind") == 0) { bit = 32; if (seen & bit || jp_string(&parser, request->kind, sizeof request->kind) != 0) return -1; }
    else if (strcmp(key, "session_value") == 0) { bit = 64; if (seen & bit || jp_string(&parser, request->value, sizeof request->value) != 0) return -1; }
    else return -1;
    seen |= bit; ++fields; after_comma = 0; jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == ',') { ++parser.p; after_comma = 1; continue; }
    if (*parser.p == '}') break;
    return -1;
  }
  if (parse_object_end(&parser, fields) != 0 || seen != 127 || version != 1 || strcmp(operation, "publish") != 0 || request->publisher_pid <= 0 || request->publisher_pid > INT_MAX || !valid_pane_id(request->pane_id) || !valid_session_value(request->kind, request->value)) return -1;
  return 0;
}

static int parse_resolve_request(const char *json, size_t length,
                                 resolve_request *request) {
  json_parser parser = {json, json + length};
  char key[64], operation[16];
  long long version = 0;
  unsigned seen = 0;
  int fields = 0, after_comma = 0;
  if (jp_char(&parser, '{') != 0) return -1;
  for (;;) {
    jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == '}') { if (after_comma) return -1; break; }
    if (jp_string(&parser, key, sizeof key) != 0 || jp_char(&parser, ':') != 0) return -1;
    unsigned bit;
    if (strcmp(key, "v") == 0) { bit = 1; if (seen & bit || jp_integer(&parser, &version) != 0) return -1; }
    else if (strcmp(key, "op") == 0) { bit = 2; if (seen & bit || jp_string(&parser, operation, sizeof operation) != 0) return -1; }
    else if (strcmp(key, "directory") == 0) { bit = 4; if (seen & bit || jp_string(&parser, request->directory, sizeof request->directory) != 0) return -1; }
    else if (strcmp(key, "pane_pid") == 0) { bit = 8; if (seen & bit || jp_integer(&parser, &request->pane_pid) != 0) return -1; }
    else if (strcmp(key, "pane_tty") == 0) { bit = 16; if (seen & bit || jp_string(&parser, request->pane_tty, sizeof request->pane_tty) != 0) return -1; }
    else if (strcmp(key, "pane_id") == 0) { bit = 32; if (seen & bit || jp_string(&parser, request->pane_id, sizeof request->pane_id) != 0) return -1; }
    else return -1;
    seen |= bit; ++fields; after_comma = 0; jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == ',') { ++parser.p; after_comma = 1; continue; }
    if (*parser.p == '}') break;
    return -1;
  }
  if (parse_object_end(&parser, fields) != 0 || seen != 63 || version != 1 || strcmp(operation, "resolve") != 0 || request->pane_pid <= 0 || request->pane_pid > INT_MAX || !valid_pane_id(request->pane_id) || request->pane_tty[0] != '/') return -1;
  return 0;
}

static int parse_object_end(json_parser *parser, int fields) {
  jp_ws(parser);
  if (jp_char(parser, '}') != 0) return -1;
  jp_ws(parser);
  return fields > 0 && parser->p == parser->end ? 0 : -1;
}

typedef struct {
  pid_t pid;
  pid_t ppid;
  pid_t pgid;
  pid_t sid;
  dev_t tty_dev;
  pid_t tpgid;
  uint64_t start_sec;
  uint64_t start_usec;
  uint32_t flags;
} process_record;

static int parse_beacon_object(const char *json, size_t length, pid_t candidate,
                               const process_record *record, const char *pane_id,
                               char *kind, size_t kind_capacity, char *value,
                               size_t value_capacity) {
  json_parser parser = {json, json + length};
  char key[64], stored_pane[128], start[128];
  long long schema = 0, pid = 0;
  unsigned seen = 0;
  int fields = 0, after_comma = 0;
  if (jp_char(&parser, '{') != 0) return -1;
  for (;;) {
    jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == '}') { if (after_comma) return -1; break; }
    if (jp_string(&parser, key, sizeof key) != 0 || jp_char(&parser, ':') != 0) return -1;
    unsigned bit;
    if (strcmp(key, "schema") == 0) { bit = 1; if (seen & bit || jp_integer(&parser, &schema) != 0) return -1; }
    else if (strcmp(key, "pid") == 0) { bit = 2; if (seen & bit || jp_integer(&parser, &pid) != 0) return -1; }
    else if (strcmp(key, "pane_id") == 0) { bit = 4; if (seen & bit || jp_string(&parser, stored_pane, sizeof stored_pane) != 0) return -1; }
    else if (strcmp(key, "start_time") == 0) { bit = 8; if (seen & bit || jp_string(&parser, start, sizeof start) != 0) return -1; }
    else if (strcmp(key, "session_ref") == 0) {
      bit = 16; if (seen & bit || jp_char(&parser, '{') != 0) return -1;
      char nested[64]; unsigned nested_seen = 0; int nested_fields = 0, nested_after_comma = 0;
      for (;;) {
        jp_ws(&parser); if (parser.p >= parser.end) return -1;
        if (*parser.p == '}') { if (nested_after_comma) return -1; break; }
        if (jp_string(&parser, nested, sizeof nested) != 0 || jp_char(&parser, ':') != 0) return -1;
        unsigned nested_bit;
        if (strcmp(nested, "kind") == 0) { nested_bit = 1; if (nested_seen & nested_bit || jp_string(&parser, kind, kind_capacity) != 0) return -1; }
        else if (strcmp(nested, "value") == 0) { nested_bit = 2; if (nested_seen & nested_bit || jp_string(&parser, value, value_capacity) != 0) return -1; }
        else return -1;
        nested_seen |= nested_bit; ++nested_fields; nested_after_comma = 0; jp_ws(&parser);
        if (parser.p >= parser.end) return -1;
        if (*parser.p == ',') { ++parser.p; nested_after_comma = 1; continue; }
        if (*parser.p == '}') break;
        return -1;
      }
      if (parse_object_end(&parser, nested_fields) != 0 || nested_seen != 3) return -1;
    } else return -1;
    seen |= bit; ++fields; after_comma = 0; jp_ws(&parser);
    if (parser.p >= parser.end) return -1;
    if (*parser.p == ',') { ++parser.p; after_comma = 1; continue; }
    if (*parser.p == '}') break;
    return -1;
  }
  if (parse_object_end(&parser, fields) != 0 || seen != 31 || schema != 1 || pid != candidate || strcmp(stored_pane, pane_id) != 0) return -1;
  char expected[128];
  (void)snprintf(expected, sizeof expected, "%llu.%06llu", (unsigned long long)record->start_sec, (unsigned long long)record->start_usec);
  if (strcmp(start, expected) != 0) return -2;
  return valid_session_value(kind, value) ? 0 : -1;
}

static int read_process(pid_t pid, process_record *record) {
  struct proc_bsdinfo info;
  memset(&info, 0, sizeof info);
  errno = 0;
  int size = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, sizeof info);
  if (size != (int)sizeof info)
    return -1;
  pid_t sid = getsid(pid);
  if (sid < 0)
    return -1;
  record->pid = info.pbi_pid;
  record->ppid = info.pbi_ppid;
  record->pgid = info.pbi_pgid;
  record->sid = sid;
  record->tty_dev = info.e_tdev;
  record->tpgid = info.e_tpgid;
  record->start_sec = (uint64_t)info.pbi_start_tvsec;
  record->start_usec = (uint64_t)info.pbi_start_tvusec;
  record->flags = info.pbi_flags;
  return 0;
}

static int find_record(const process_record *records, size_t count, pid_t pid) {
  for (size_t i = 0; i < count; ++i)
    if (records[i].pid == pid)
      return (int)i;
  return -1;
}

static int descendant_of(const process_record *records, size_t count,
                        pid_t candidate, pid_t root) {
  pid_t current = candidate;
  for (size_t depth = 0; depth < MAX_DEPTH; ++depth) {
    if (current == root)
      return 1;
    int index = find_record(records, count, current);
    if (index < 0 || records[index].ppid == current || records[index].ppid <= 0)
      return 0;
    current = records[index].ppid;
  }
  return -1;
}

static int same_process_record(const process_record *left,
                               const process_record *right) {
  return left->pid == right->pid && left->ppid == right->ppid &&
         left->pgid == right->pgid && left->sid == right->sid &&
         left->tty_dev == right->tty_dev && left->tpgid == right->tpgid &&
         left->start_sec == right->start_sec &&
         left->start_usec == right->start_usec && left->flags == right->flags;
}

static int verify_process_chain(const process_record *records, size_t count,
                                pid_t candidate, pid_t root) {
  pid_t current = candidate;
  pid_t seen[MAX_DEPTH];
  size_t depth = 0;
  while (depth < MAX_DEPTH) {
    for (size_t i = 0; i < depth; ++i)
      if (seen[i] == current) return -1;
    seen[depth++] = current;
    int index = find_record(records, count, current);
    if (index < 0) return 0;
    process_record reread;
    if (read_process(current, &reread) != 0 ||
        !same_process_record(&records[index], &reread))
      return 0;
    if (current == root) return 1;
    if (records[index].ppid <= 0) return 0;
    current = records[index].ppid;
  }
  return -1;
}

static int open_private_directory(const char *path, int create,
                                  uid_t owner) {
  if (path[0] != '/')
    return -1;
  int fd = open("/", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
    return -1;
  const char *cursor = path + 1;
  while (*cursor) {
    while (*cursor == '/')
      ++cursor;
    if (*cursor == '\0')
      break;
    const char *end = strchr(cursor, '/');
    size_t length = end ? (size_t)(end - cursor) : strlen(cursor);
    if (length == 0 || length >= NAME_MAX ||
        (length == 1 && cursor[0] == '.') ||
        (length == 2 && cursor[0] == '.' && cursor[1] == '.')) {
      close(fd);
      return -1;
    }
    char component[NAME_MAX];
    memcpy(component, cursor, length);
    component[length] = '\0';
    int next = openat(fd, component,
                      O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    if (next < 0 && errno == ENOENT && create) {
      if (mkdirat(fd, component, 0700) < 0 && errno != EEXIST) {
        close(fd);
        return -1;
      }
      next = openat(fd, component,
                    O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
    }
    if (next < 0) {
      close(fd);
      return -1;
    }
    struct stat info;
    int is_leaf = 1;
    if (end) {
      const char *next_char = end;
      while (*next_char == '/')
        ++next_char;
      if (*next_char != '\0')
        is_leaf = 0;
    }
    if (fstat(next, &info) < 0 || !S_ISDIR(info.st_mode) ||
        (info.st_uid != owner && info.st_uid != 0) ||
        ((info.st_mode & (S_IWGRP | S_IWOTH)) != 0 &&
         !(info.st_uid == 0 && (info.st_mode & (S_ISUID | S_ISGID | S_ISVTX | S_IRWXU | S_IRWXG | S_IRWXO)) ==
           (S_ISVTX | S_IRWXU | S_IRWXG | S_IRWXO))) ||
        (is_leaf && info.st_uid != owner)) {
      close(next);
      close(fd);
      return -1;
    }
    close(fd);
    fd = next;
    cursor = end ? end + 1 : cursor + length;
  }
  struct stat leaf;
  if (fstat(fd, &leaf) < 0 || !S_ISDIR(leaf.st_mode) ||
      leaf.st_uid != owner || (leaf.st_mode & 0777) != 0700 ||
      (leaf.st_mode & 06000) != 0) {
    close(fd);
    return -1;
  }
  return fd;
}

static int sync_file(int fd) {
  if (fsync(fd) < 0)
    return -1;
#ifdef F_FULLFSYNC
  if (fcntl(fd, F_FULLFSYNC) < 0 && errno != EINVAL && errno != ENOTTY)
    return -1;
#endif
  return 0;
}

static int verify_current_tty(const process_record *self) {
  int ttyfd = open("/dev/tty", O_RDONLY | O_NOCTTY | O_CLOEXEC | O_NOFOLLOW);
  if (ttyfd < 0)
    return -1;
  struct stat ttyinfo;
  pid_t sid = tcgetsid(ttyfd);
  pid_t foreground = tcgetpgrp(ttyfd);
  int valid = fstat(ttyfd, &ttyinfo) == 0 && S_ISCHR(ttyinfo.st_mode) &&
              sid == self->sid && foreground == self->tpgid &&
              self->pgid == self->tpgid && ttyinfo.st_rdev == self->tty_dev;
  close(ttyfd);
  return valid ? 0 : -1;
}

static int json_escape(const char *input, char *output, size_t capacity) {
  size_t used = 0;
  for (const unsigned char *p = (const unsigned char *)input; *p; ++p) {
    if (*p < 0x20 || *p == '\\' || *p == '"') {
      if (used + 2 >= capacity)
        return -1;
      output[used++] = '\\';
      output[used++] = *p == '\\' ? '\\' : (*p == '"' ? '"' : '?');
      if (*p < 0x20)
        return -1;
    } else {
      if (used + 1 >= capacity)
        return -1;
      output[used++] = (char)*p;
    }
  }
  output[used] = '\0';
  return 0;
}

static int create_publication_temp(int dirfd, pid_t pid, char *name,
                                   size_t capacity) {
  for (unsigned attempt = 0; attempt < 32U; ++attempt) {
    uint64_t entropy = 0;
    arc4random_buf(&entropy, sizeof entropy);
    int length = snprintf(name, capacity, ".tmux-herdr-%d-%016llx.tmp",
                          (int)pid, (unsigned long long)entropy);
    if (length < 0 || (size_t)length >= capacity) return -1;
    int fd = openat(dirfd, name,
                    O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
                    0600);
    if (fd >= 0) return fd;
    if (errno != EEXIST) return -1;
  }
  return -1;
}

static int publish_beacon(const char *request, size_t request_length) {
  publish_request parsed;
  memset(&parsed, 0, sizeof parsed);
  if (parse_publish_request(request, request_length, &parsed) != 0) {
    result_error("invalid");
    return 1;
  }
  const char *directory = parsed.directory;
  const char *pane_id = parsed.pane_id;
  const char *kind = parsed.kind;
  const char *value = parsed.value;
  long long publisher_pid = parsed.publisher_pid;
  process_record self;
  if ((pid_t)publisher_pid != getppid()) {
    result_error("stale");
    return 1;
  }
  if (read_process((pid_t)publisher_pid, &self) != 0) {
    result_error(errno == EPERM ? "denied" : "stale");
    return 1;
  }
  if (verify_current_tty(&self) != 0) {
    result_error("no_tty");
    return 1;
  }
  char escaped_pane[256], escaped_kind[32], escaped_value[MAX_TEXT * 2];
  if (json_escape(pane_id, escaped_pane, sizeof escaped_pane) ||
      json_escape(kind, escaped_kind, sizeof escaped_kind) ||
      json_escape(value, escaped_value, sizeof escaped_value)) {
    result_error("invalid");
    return 1;
  }
  char payload[RECORD_LIMIT];
  int length = snprintf(payload, sizeof payload,
                        "{\"schema\":1,\"pid\":%d,\"pane_id\":\"%s\","
                        "\"start_time\":\"%llu.%06llu\",\"session_ref\":{"
                        "\"kind\":\"%s\",\"value\":\"%s\"}}",
                        (int)self.pid, escaped_pane,
                        (unsigned long long)self.start_sec,
                        (unsigned long long)self.start_usec, escaped_kind,
                        escaped_value);
  if (length < 0 || (size_t)length >= sizeof payload) {
    result_error("invalid");
    return 1;
  }
  int dirfd = open_private_directory(directory, 1, geteuid());
  if (dirfd < 0) {
    result_error("io");
    return 1;
  }
  char temporary[NAME_MAX];
  int filefd = create_publication_temp(dirfd, self.pid, temporary,
                                       sizeof temporary);
  if (filefd < 0) {
    close(dirfd);
    result_error("io");
    return 1;
  }
  size_t written = 0;
  while (written < (size_t)length) {
    ssize_t n = write(filefd, payload + written, (size_t)length - written);
    if (n < 0 && errno == EINTR)
      continue;
    if (n <= 0) {
      close(filefd);
      close(dirfd);
      result_error("io");
      return 1;
    }
    written += (size_t)n;
  }
  struct stat fileinfo;
  if (fstat(filefd, &fileinfo) < 0 || !S_ISREG(fileinfo.st_mode) ||
      fileinfo.st_uid != geteuid() || (fileinfo.st_mode & 0777) != 0600 ||
      fileinfo.st_nlink != 1 || sync_file(filefd) < 0) {
    close(filefd);
    close(dirfd);
    result_error("io");
    return 1;
  }
  close(filefd);
  char destination[64];
  (void)snprintf(destination, sizeof destination, "%d.json", (int)self.pid);
  if (renameat(dirfd, temporary, dirfd, destination) < 0 ||
      fsync(dirfd) < 0) {
    close(dirfd);
    result_error("io");
    return 1;
  }
  close(dirfd);
  result_ok();
  return 0;
}

static int read_bounded_file(int dirfd, const char *name, char *buffer,
                             size_t capacity) {
  int fd = openat(dirfd, name, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0)
    return errno == ENOENT ? 0 : -1;
  struct stat info;
  if (fstat(fd, &info) < 0 || !S_ISREG(info.st_mode) || info.st_uid != geteuid() ||
      (info.st_mode & 0777) != 0600 || info.st_nlink != 1 ||
      info.st_size < 0 || info.st_size >= (off_t)capacity) {
    close(fd);
    return -1;
  }
  size_t used = 0;
  while (used < (size_t)info.st_size) {
    ssize_t n = read(fd, buffer + used, (size_t)info.st_size - used);
    if (n < 0 && errno == EINTR)
      continue;
    if (n <= 0) {
      close(fd);
      return -1;
    }
    used += (size_t)n;
  }
  buffer[used] = '\0';
  close(fd);
  return (int)used;
}


static int resolve_beacon(const char *request, size_t request_length) {
  resolve_request parsed;
  memset(&parsed, 0, sizeof parsed);
  if (parse_resolve_request(request, request_length, &parsed) != 0) {
    result_error("invalid");
    return 1;
  }
  const char *directory = parsed.directory;
  const char *pane_id = parsed.pane_id;
  const char *pane_tty = parsed.pane_tty;
  long long pane_pid_value = parsed.pane_pid;
  process_record root;
  if (read_process((pid_t)pane_pid_value, &root) != 0) {
    result_error("process_disappeared");
    return 1;
  }
  int ttyfd = open(pane_tty, O_RDONLY | O_NOCTTY | O_CLOEXEC | O_NOFOLLOW);
  if (ttyfd < 0) {
    result_error(errno == EACCES ? "denied" : "no_tty");
    return 1;
  }
  struct stat ttyinfo;
  pid_t tty_sid = -1, tty_pgid = -1;
  if (fstat(ttyfd, &ttyinfo) < 0 || !S_ISCHR(ttyinfo.st_mode) ||
      (tty_sid = tcgetsid(ttyfd)) < 0 ||
      (tty_pgid = tcgetpgrp(ttyfd)) < 0) {
    close(ttyfd);
    result_error("no_tty");
    return 1;
  }
  close(ttyfd);
  if (root.tty_dev != ttyinfo.st_rdev || root.sid != tty_sid) {
    result_error("no_tty");
    return 1;
  }
  pid_t pids[MAX_PROCESSES];
  int bytes = proc_listpids(PROC_ALL_PIDS, 0, pids, sizeof pids);
  if (bytes <= 0 || (size_t)bytes >= sizeof pids) {
    result_error("process_tree_too_large");
    return 1;
  }
  size_t process_count = (size_t)bytes / sizeof(pid_t);
  process_record records[MAX_PROCESSES];
  size_t record_count = 0;
  int denied = 0;
  for (size_t i = 0; i < process_count && record_count < MAX_PROCESSES; ++i) {
    if (pids[i] <= 0)
      continue;
    process_record current;
    if (read_process(pids[i], &current) != 0) {
      if (errno == EPERM || errno == EACCES)
        ++denied;
      continue;
    }
    records[record_count++] = current;
  }
  if (find_record(records, record_count, root.pid) < 0) {
    if (read_process(root.pid, &root) != 0) {
      result_error("process_disappeared");
      return 1;
    }
    records[record_count++] = root;
  }
  int root_index = find_record(records, record_count, root.pid);
  if (root_index < 0 || !same_process_record(&root, &records[root_index])) {
    result_error("stale");
    return 1;
  }
  int dirfd = open_private_directory(directory, 0, geteuid());
  if (dirfd < 0) {
    result_error(errno == ENOENT ? "beacon_missing" : "io");
    return 1;
  }
  size_t matches = 0;
  process_record match_record;
  memset(&match_record, 0, sizeof match_record);
  char match_kind[16] = {0}, match_value[MAX_TEXT] = {0};
  int had_stale = 0;
  for (size_t i = 0; i < record_count; ++i) {
    process_record *candidate = &records[i];
    int ancestry = descendant_of(records, record_count, candidate->pid, root.pid);
    if (ancestry < 0) {
      close(dirfd);
      result_error("process_tree_too_large");
      return 1;
    }
    if (!ancestry || candidate->tty_dev != ttyinfo.st_rdev ||
        candidate->sid != tty_sid || candidate->pgid != tty_pgid ||
        candidate->tpgid != tty_pgid)
      continue;
    char name[64], beacon[RECORD_LIMIT], kind[16], value[MAX_TEXT];
    (void)snprintf(name, sizeof name, "%d.json", (int)candidate->pid);
    int size = read_bounded_file(dirfd, name, beacon, sizeof beacon);
    if (size == 0)
      continue;
    if (size < 0) {
      close(dirfd);
      result_error("io");
      return 1;
    }
    int parsed = parse_beacon_object(beacon, (size_t)size, candidate->pid,
                                     candidate, pane_id, kind, sizeof kind, value,
                                     sizeof value);
    if (parsed == -2) {
      had_stale = 1;
      continue;
    }
    if (parsed != 0)
      continue;
    if (++matches > 1) {
      close(dirfd);
      result_error("ambiguous_beacons");
      return 1;
    }
    match_record = *candidate;
    (void)snprintf(match_kind, sizeof match_kind, "%s", kind);
    (void)snprintf(match_value, sizeof match_value, "%s", value);
  }
  close(dirfd);
  if (matches == 1) {
    process_record final_record;
    int chain_status = verify_process_chain(records, record_count,
                                            match_record.pid, root.pid);
    if (chain_status != 1 || read_process(match_record.pid, &final_record) != 0 ||
        !same_process_record(&match_record, &final_record) ||
        final_record.tty_dev != ttyinfo.st_rdev ||
        final_record.sid != tty_sid || final_record.pgid != tty_pgid ||
        final_record.tpgid != tty_pgid) {
      result_error("stale");
      return 1;
    }
    char escaped_kind[32], escaped_value[MAX_TEXT * 2];
    if (json_escape(match_kind, escaped_kind, sizeof escaped_kind) ||
        json_escape(match_value, escaped_value, sizeof escaped_value)) {
      result_error("invalid");
      return 1;
    }
    (void)printf(
        "{\"ok\":true,\"kind\":\"%s\",\"value\":\"%s\","
        "\"pid\":%d,\"start_time\":\"%llu.%06llu\"}\n",
        escaped_kind, escaped_value, (int)final_record.pid,
        (unsigned long long)final_record.start_sec,
        (unsigned long long)final_record.start_usec);
    return 0;
  }
  if (denied > 0) {
    result_error("denied");
  } else if (had_stale) {
    result_error("stale");
  } else {
    result_error("beacon_missing");
  }
  return 1;
}
#endif

int main(int argc, char **argv) {
  if (argc != 2 || (strcmp(argv[1], "publish") != 0 &&
                    strcmp(argv[1], "resolve") != 0 &&
                    strcmp(argv[1], "selftest") != 0)) {
    result_error("invalid");
    return 2;
  }
  if (strcmp(argv[1], "selftest") == 0) {
    char request[INPUT_LIMIT];
    if (read_request(request, sizeof request) < 0 && errno != 0) {
      result_error("invalid");
      return 1;
    }
    result_ok();
    return 0;
  }
  char request[INPUT_LIMIT];
  int length = read_request(request, sizeof request);
  if (length < 0) {
    result_error(length == -2 ? "oversized" : "invalid");
    return 1;
  }
  if (memchr(request, '\0', (size_t)length) != NULL) {
    result_error("invalid");
    return 1;
  }
#ifndef __APPLE__
  (void)request;
  result_error("unsupported");
  return 1;
#else
  if (strcmp(argv[1], "publish") == 0)
    return publish_beacon(request, (size_t)length);
  return resolve_beacon(request, (size_t)length);
#endif
}
