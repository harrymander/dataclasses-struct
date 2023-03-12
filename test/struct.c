#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#ifdef _MSC_VER
#define _CRT_SECURE_NO_WARNINGS
#endif

#if defined(TEST_PACKED_STRUCT) && defined(_MSC_VER)
#pragma pack(push, 1)
#endif
struct test {
    char str_test[13];
    uint32_t u32_test;
    double double_test;
}
#ifdef TEST_PACKED_STRUCT
#ifdef _MSC_VER
#pragma pack(pop)
#else
__attribute__((packed))
#endif // _MSC_VER
#endif // TEST_PACKED_STRUCT
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
