htmldoc:
	$(MAKE) -C doc html

clean:
	rm -rf build

.PHONY: htmldoc clean
