#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#ifdef _MSC_VER
#define _CRT_SECURE_NO_WARNINGS
#endif

struct test {
#ifdef TEST_NATIVE_INTS
    // TODO: test with native ints (int, long, short etc.)
#else
    // TODO: test with stdint types
#endif
    double double_test;
    char str_test[13];
};

int main(const int argc, const char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s [outfile]\n", argv[0]);
        return 1;
    }

    const struct test t = {
        .double_test = -0.5,
        .str_test = "Hello!",
    };

    FILE *fp = fopen(argv[1], "w");
    if (!fp) {
        fprintf(stderr, "cannot open file: %s\n", strerror(errno));
        return 1;
    }

    int ret = fwrite(&t, sizeof(t), 1, fp) != 1;
    if (ret) {
        fprintf(stderr, "write error\n");
    }
    fclose(fp);
    return ret;
}
