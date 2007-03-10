include config.mak

all:
	$(Q)$(MAKE) -C lib

clean:
	$(Q)$(MAKE) -C lib clean
