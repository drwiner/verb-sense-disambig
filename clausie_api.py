from functools import partial
from nltk.corpus import wordnet as wn
from subprocess import Popen, PIPE

CLAUSIE_FRAME_DICT = {
	'SVC': [4,6,7],
	'SV' : [1,3],
	'SVA': [1,2,12,13,22,27],
	'SVOO': [14,15],
	'SVOC': [5],
	'SVO': [26,34,1,2,8,9,10,11,33],
	'SVOA': [1,2,8,9,10,11,15,16,17,18,19,20,21,30,31,33,24,28,29,32,35]}


class ClausieLine:
	# API for reading from clausie text output

	def __init__(self, sub_lines):
		self.raw = sub_lines
		"""
		# first line is of the form::  # Line x: "sentence"
		# second line begins semantic graph, indented subsequent lines
		# third item is of the form:: # Detect x clause(s), subsequent lines start with "-SVC" style
			SVC style lines, start with hyphen, then parentheses, then dictionary with @ (sometimes) pointing to line
				# we can try splittling at @ and just take the first part, and if len(split) > 1, last entry [-1]
		"""


def setup_clausie():
	clausie_port = Popen(
		['java', '-jar',
		 'D:/Documents/Python/ClausIEpy/clausie.jar', '-c',
		 'D:/Documents/Python/ClausIEpy/resources/clausie.conf',
		 '-v', '-s' '-p', '-o', 'clausie_output.txt'],
		stdin=PIPE)
	return partial(clausie, clausie_port)


def clausie(input_parser=None, text=None, restart=None):
	if input_parser is None or restart is not None:
		parser = setup_clausie()
	else:
		parser = input_parser

	for sent in text:
		parser.stdin.write(sent)
	parser.communicate()

	# TODO: improve API here.
	clause_types = []
	verb_lemmas = []
	with open('clausie_output.txt', 'r') as fp:
		last_line = None
		last_id = 0
		for line in fp:
			if line[0] == '#':
				last_line = line
			# print(line)
			elif line.split()[0] == last_id:
				continue
			else:
				last_id = line.split()[0]
				# This is an output, last line has clause type
				sep_line = last_line.split()
				clause_type = sep_line[2]
				# print(line.split())

				verb_instance = None
				for i, item in enumerate(sep_line[3:]):
					if 'V:' in item:
						verb_instance = sep_line[3 + i + 1]
						break
				verb_instance = verb_instance.split('@')[0]
				verb_lemmas.append(verb_instance)
				clause_types.append(clause_type)

	cndt_fids = []
	sent_zip = zip(clause_types, verb_lemmas)
	for ctype, vlemma in sent_zip:
		print('{} : {}'.format(ctype, vlemma))
		frameids = CLAUSIE_FRAME_DICT[ctype]
		for i, synset in enumerate(wn.synsets(vlemma)):
			fids = synset.frame_ids()
			interfids = list(set(frameids) & set(fids))
			if len(interfids) > 0:
				cndt_fids.extend(interfids)
				print('{}: {}'.format(i, synset.definition()))
		print('\n')

def read_clausie_output(text_file_name):
	sents = []
	sent = []
	started = False
	with open(text_file_name, 'r') as clausie_text:

		for line in clausie_text:
			if line[:5] == '# Line':
				if not started:
					started = True
				if sent != []:
					sents.append(sent)
					sent = []
				sent.append(line)
			if started:
				sent.append(line)

	return sents

if __name__ == '__main__':

	read_clausie_output('clausie_output.txt')

