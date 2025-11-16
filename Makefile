WORDS_FILE := words.txt

WORDS := $(file < $(WORDS_FILE))

# $(info "words $(WORDS)")

define WORD_TARGET_TEMPLATE

snd/$1.mp3: snd
	@echo "Processing item: $1 ($$@)"
	python3 -m piper -m en_US-lessac-medium -f - -- '$1.' | ffmpeg -y -i - -codec:a libmp3lame -q:a 2 $$@
endef

$(eval $(foreach word,$(WORDS),$(call WORD_TARGET_TEMPLATE,$(word))))

# $(info "template foreach" $(foreach word,$(WORDS),$(call WORD_TARGET_TEMPLATE,$(word))))
# $(info "targets foreach $(foreach word,$(WORDS),snd/$(word).mp3)")

wordlist.js: words.txt
	awk '{printf "%s\"%s\"", sep, $$0; sep=", "} END{print ""}' words.txt | sed 's/^/var wordList = [/; s/$$/];/' > $@

snd:
	mkdir -p snd

.PHONY: all
all: wordlist.js $(foreach word,$(WORDS),snd/$(word).mp3)