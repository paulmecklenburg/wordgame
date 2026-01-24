# Create the environment
# python3 -m venv piper_env
# Activate it
# source piper_env/bin/activate

WORDS_FILE := words.tsv

WORDS := $(shell cut -f1 words.tsv)

# $(info "words $(WORDS)")

wordlist.js: $(WORDS_FILE)
	awk -F'\t' 'BEGIN {printf "const wordList = [\n"} {printf "  \"%s\",\n", $$1} END {print "];"}' $< > $@

.PHONY: snd_mp3
snd_mp3:
	mkdir -p snd
	python3 make_mp3s.py

.PHONY: all
all: wordlist.js snd_mp3
