CC      := cc
CFLAGS  := -O2 -Wall -Wextra -std=gnu11
TARGETS := write_latency

all: $(TARGETS)

write_latency: write_latency.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)

.PHONY: all clean
