from functools import partial
from nltk.corpus import wordnet as wn
from subprocess import Popen, PIPE
from collections import namedtuple

CLAUSIE_FRAME_DICT = {
	'SVC': [4,6,7],
	'SV' : [1,3],
	'SVA': [1,2,12,13,22,27],
	'SVOO': [14,15],
	'SVOC': [5],
	'SVO': [26,34,1,2,8,9,10,11,33],
	'SVOA': [1,2,8,9,10,11,15,16,17,18,19,20,21,30,31,33,24,28,29,32,35]}



Clause = namedtuple('Clause', ['type', 'dict'])
Sentence = namedtuple('ClauseLine', ['raw_sentence', 'clauses', 'triples'])

def to_typed_clause(clause_line):
	first_part = clause_line.split('(')[0]
	clause_type = first_part.split('-')[0].strip()
	clause_parenth = clause_line[len(first_part):].strip()
	clause_parenth = clause_parenth.replace('(', ' { ')
	clause_parenth = clause_parenth.replace(',', ' , ')
	clause_parenth = clause_parenth.replace(')', ' } ')
	clause_parenth = clause_parenth.replace('@', '_')
	clause_parenth = clause_parenth.replace(':', ' :')
	c_list = clause_parenth.split()
	c_list = ["\'" + c_item + "\'" if c_item not in ['}', '{', ':', ','] else c_item for c_item in c_list]
	clause_parenth = ' '.join(c_list)
	clause_dict = eval(clause_parenth)
	return Clause(clause_type, clause_dict)

def to_clause_line(sub_lines):
	raw_sentence = sub_lines[0][10:].strip()
	clauses = []
	triples = []

	# skip semantic graph?
	for i, line in enumerate(sub_lines[1:]):
		if line[4:12] == 'Detected':
			# find num clauses
			num_clauses = int(line[13:15].strip())
			break

	# each subsequent line is a clause
	clause_lines = [sub_lines[i + 2 + k] for k in range(num_clauses)]
	for clause in clause_lines:
		clauses.append(to_typed_clause(clause))

	# skip next line, original sentence (+1)
	for cndt in sub_lines[i + 2 + num_clauses + 1:]:
		split_cndt = cndt.split('\t')
		triples.append(split_cndt[1:4])

	return Sentence(raw_sentence, clauses, triples)


def setup_clausie():
	clausie_port = Popen(
		['java', '-jar',
		 'D:/Documents/Python/ClausIEpy/clausie.jar', '-c',
		 'D:/Documents/Python/ClausIEpy/resources/clausie.conf',
		 '-v', '-s', '-p', '-o', 'clausie_output.txt'],
		stdin=PIPE)
	return clausie_port


def clausie(input_parser=None, text=None, restart=None):
	if input_parser is None or restart is not None:
		parser = setup_clausie()
	else:
		parser = input_parser

	for sent in text:
		parser.stdin.write(sent)

	parser.communicate()
	# returns Sentences
	return read_clausie_output('clausie_output.txt')

def read_clausie_output(text_file_name):
	sents = []
	sent = []
	started = False
	with open(text_file_name, 'r') as clausie_text:

		for line in clausie_text:
			if line[:6] == '# Line':
				if not started:
					started = True
				if sent:
					sents.append(sent)
					sent = []
			if started:
				sent.append(line)

	return sents

if __name__ == '__main__':

	# test: give sample sentences, read them and get output
	sample_text = [b'The body floats to the surface of the water.\n', b'He shoots first, asks questions later.\n']
	sentences = clausie(text=sample_text)

	for sent in sentences:
		print(sent)
