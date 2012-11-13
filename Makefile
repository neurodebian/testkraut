BUILDDIR=$(CURDIR)/build
MAN_DIR=$(BUILDDIR)/man

PYTHON = python
PYTHON3 = python3
NOSETESTS = $(PYTHON) $(shell which nosetests)

# Setup local PYTHONPATH depending on the version of provided $(PYTHON)
PYVER = $(shell $(PYTHON) -c 'import sys; print(sys.version_info[0])')
ifeq ($(PYVER),2)
 # just use the local sources and run tests 'in source'
 TEST_DIR = .
 LPYTHONPATH = .:$(PYTHONPATH)
else
 # for 3 (and hopefully not above ;) ) -- corresponding build/
 # since sources go through 2to3 conversion
 TEST_DIR = $(BUILD3DIR)
 LPYTHONPATH = $(BUILD3DIR):$(PYTHONPATH)
endif

htmldoc:
	$(MAKE) -C doc html BUILDDIR=$(BUILDDIR)

clean:
	rm -rf build
	rm -f MANIFEST

manpages: mkdir-MAN_DIR
	@echo "I: Creating manpages"
	PYTHONPATH=$(LPYTHONPATH) help2man --no-discard-stderr \
		--help-option="--help-np" -N -n "command line interface for testkraut" \
			bin/testkraut > $(MAN_DIR)/testkraut.1
	for cmd in $$(grep import < testkraut/cmdline/__init__.py | cut -d _ -f 2-); do \
		summary="$$(grep 'man: -*-' < testkraut/cmdline/cmd_$${cmd}.py | cut -d '%' -f 2-)"; \
		PYTHONPATH=$(LPYTHONPATH) help2man --no-discard-stderr \
			--help-option="--help-np" -N -n "$$summary" \
				"bin/testkraut $${cmd}" > $(MAN_DIR)/testkraut-$${cmd}.1 ; \
	done

test:
	PYTHONPATH=$(LPYTHONPATH) $(NOSETESTS) \
		--nocapture \
		--with-doctest \
		--doctest-extension .rst \
		--doctest-tests doc/source/*.rst \
		.

#
# Little helpers
#

mkdir-%:
	if [ ! -d $($*) ]; then mkdir -p $($*); fi

.PHONY: htmldoc clean manpages
