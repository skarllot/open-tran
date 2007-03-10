include ../config.mak

DEPDIR = .deps

DEFINES += -D_GNU_SOURCE=1
CFLAGS += -fpic -Wall -I$(PYTHON)
INCLUDES = -I$(SQLITE)
COMPILE = gcc $(CFLAGS) $(DEFINES)
LDFLAGS = 

OBJS = xmalloc.o hash.o phrase.o storage.o $(SQLITE)/libsqlite3.a


all: tran _tran.so

tran: $(OBJS) main.o
	@echo "LD	$@"
	$(Q)gcc $(LDFLAGS) -o $@ $^

_tran.so: $(OBJS) tran.o
	@echo "LD	$@"
	$(Q)gcc -shared $(LDFLAGS) -o $@ $^

tran.c: tran.i
	@echo "SWIG	$@"
	$(Q)swig -python -o $@ $^

.c.o:
	@echo "CC	$@"
	$(Q)if $(COMPILE) -MT $@ -MP -MF "$(DEPDIR)/$*.Tpo" -MD \
	  -c -o $@ $<; then mv -f "$(DEPDIR)/$*.Tpo" "$(DEPDIR)/$*.po"; \
        else rm -f "$(DEPDIR)/$*.Tpo"; exit 1; fi

clean:
	rm -f tran _tran.so *.o tran.c tran.py *.pyc

include $(DEPDIR)/hash.po
include $(DEPDIR)/main.po
include $(DEPDIR)/xmalloc.po
include $(DEPDIR)/phrase.po
include $(DEPDIR)/storage.po
include $(DEPDIR)/tran.po
