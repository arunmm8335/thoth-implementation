# Makefile for Thoth Benchmark Suite
# Compiles for X86_64 target (can also use RISCV if cross-compiler available)

CC = gcc
CFLAGS = -O2 -static
BINS = hashmap btree rbtree swap

all: $(BINS)

hashmap: hashmap.c
	$(CC) $(CFLAGS) -o hashmap hashmap.c

btree: btree.c
	$(CC) $(CFLAGS) -o btree btree.c

rbtree: rbtree.c
	$(CC) $(CFLAGS) -o rbtree rbtree.c

swap: swap.c
	$(CC) $(CFLAGS) -o swap swap.c

clean:
	rm -f $(BINS)

.PHONY: all clean
