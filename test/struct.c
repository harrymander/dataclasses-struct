#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>


struct test {
    char str_test[13];
    uint32_t u32_test;
    double double_test;
}
#ifdef TEST_PACKED_STRUCT
__attribute__((packed))
#endif
;

int main(const int argc, const char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "usage: %s [outfile]\n", argv[0]);
        return 1;
    }

    const struct test t = {
        .str_test = "Hello!",
        .u32_test = 5,
        .double_test = -0.5,
    };

    FILE *fp = fopen(argv[1], "w");
    if (!fp) {
        fprintf(stderr, "cannot open file: %s\n", strerror(errno));
        return 1;
    }

    if (fwrite(&t, sizeof(t), 1, fp) != 1) {
        fprintf(stderr, "write error\n");
        return 1;
    }

    fclose(fp);
    return 0;
}
