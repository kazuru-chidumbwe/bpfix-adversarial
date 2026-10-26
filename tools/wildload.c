// SPDX-License-Identifier: MIT
/*
 * wildload: load every program of a BPF object on its own and report its verdict.
 *
 * For each program, the object is opened afresh with only that program set to
 * autoload, and loaded with the kernel log level bpftool -d uses (1|2|4) and
 * libbpf's debug output on stderr, so each program's log has the same layout
 * as a `bpftool -d prog load` capture. Writes <outdir>/<prog>.log per program
 * and one line per program on stdout:
 *
 *   PROG <name> <ACCEPT|REJECT|ERROR> <errno> <section>
 *
 * REJECT = the kernel returned EACCES/EINVAL with a non-empty verifier log;
 * ERROR = anything else (open, BTF, attach-target or map creation failures).
 *
 * Build: cc -O2 -o wildload tools/wildload.c -lbpf -lelf -lz
 * Usage: sudo ./wildload <object.o> <outdir>
 */
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <bpf/libbpf.h>

static FILE *cur_log;

static int print_all(enum libbpf_print_level level, const char *fmt, va_list args)
{
	(void)level;
	if (cur_log)
		return vfprintf(cur_log, fmt, args);
	return 0;
}

static int load_one(const char *path, const char *want, const char *outdir, char *section, size_t seclen,
		    int *err_out, int *log_nonempty)
{
	struct bpf_object_open_opts opts = { .sz = sizeof(opts), .kernel_log_level = 1 | 2 | 4 };
	struct bpf_object *obj = bpf_object__open_file(path, &opts);
	struct bpf_program *p;
	char logpath[4096];
	long before, after;
	int err;

	if (!obj) {
		*err_out = errno;
		return -1;
	}
	bpf_object__for_each_program(p, obj) {
		int me = strcmp(bpf_program__name(p), want) == 0;
		bpf_program__set_autoload(p, me);
		if (me)
			snprintf(section, seclen, "%s", bpf_program__section_name(p));
	}
	snprintf(logpath, sizeof(logpath), "%s/%s.log", outdir, want);
	cur_log = fopen(logpath, "w");
	before = cur_log ? ftell(cur_log) : 0;
	err = bpf_object__load(obj);
	if (cur_log) {
		after = ftell(cur_log);
		fclose(cur_log);
		cur_log = NULL;
	} else {
		after = before;
	}
	*err_out = err ? -err : 0;
	*log_nonempty = after > before;
	bpf_object__close(obj);
	return err;
}

int main(int argc, char **argv)
{
	struct bpf_object *obj;
	struct bpf_program *p;
	char names[512][256];
	int n = 0;

	if (argc != 3) {
		fprintf(stderr, "usage: %s <object.o> <outdir>\n", argv[0]);
		return 2;
	}
	libbpf_set_print(print_all);
	obj = bpf_object__open_file(argv[1], NULL);
	if (!obj) {
		printf("OPEN_ERROR %d\n", errno);
		return 1;
	}
	bpf_object__for_each_program(p, obj) {
		if (n < 512)
			snprintf(names[n++], sizeof(names[0]), "%s", bpf_program__name(p));
	}
	bpf_object__close(obj);

	for (int i = 0; i < n; i++) {
		char section[256] = "";
		int err = 0, nonempty = 0;
		int rc = load_one(argv[1], names[i], argv[2], section, sizeof(section), &err, &nonempty);
		const char *verdict = "ACCEPT";
		if (rc) {
			char logpath[4096], line[512];
			int has_prog_log = 0;
			FILE *f;
			snprintf(logpath, sizeof(logpath), "%s/%s.log", argv[2], names[i]);
			f = fopen(logpath, "r");
			while (f && fgets(line, sizeof(line), f))
				if (strstr(line, "-- BEGIN PROG LOAD LOG --"))
					has_prog_log = 1;
			if (f)
				fclose(f);
			verdict = ((err == EACCES || err == EINVAL) && has_prog_log) ? "REJECT" : "ERROR";
		}
		printf("PROG %s %s %d %s\n", names[i], verdict, err, section);
		fflush(stdout);
	}
	return 0;
}
