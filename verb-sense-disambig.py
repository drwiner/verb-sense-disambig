from pycorenlp import StanfordCoreNLP
from functools import partial
from subprocess import Popen, PIPE
import socket

from nltk.corpus import wordnet as wn
from nltk.corpus import framenet as fn

clause_frame_dict = {
	'SVC': [4,6,7],
	'SV' : [1,3],
	'SVA': [1,2,12,13,22,27],
	'SVOO': [14,15],
	'SVOC': [5],
	'SVO': [26,34,1,2,8,9,10,11,33],
	'SVOA': [1,2,8,9,10,11,15,16,17,18,19,20,21,30,31,33,24,28,29,32,35]}

def NLP(parser, text):
	return parser.annotate(text, properties={'outputFormat': 'json'})

def setup_parser():
	nlp_port = StanfordCoreNLP('http://localhost:9000')
	return partial(NLP, parser=nlp_port)


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
		frameids = clause_frame_dict[ctype]
		for i, synset in enumerate(wn.synsets(vlemma)):
			fids = synset.frame_ids()
			interfids = list(set(frameids) & set(fids))
			if len(interfids) > 0:
				cndt_fids.extend(interfids)
				print('{}: {}'.format(i, synset.definition()))
		print('\n')


def setup_clausie():
	clausie_port = Popen(
		['java', '-jar',
		 'D:/Documents/Python/ClausIEpy/clausie.jar', '-c',
		 'D:/Documents/Python/ClausIEpy/resources/clausie.conf',
		 '-v', '-s' '-p', '-o', 'clausie_output.txt'],
		stdin=PIPE)
	return partial(clausie, clausie_port)


def semafor(sock, text, reconnect=None):
	# text is single sentence here

	if reconnect is not None:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.shutdown(socket.SHUT_WR)
		sock.connect(('127.0.0.1', 8080))

	result = [u'\n'.join(text)]

	request = u'\n\n'.join(result)
	sock.sendall(request.encode('utf8'))


	response = []
	while True:
		chunk = sock.recv(8192)
		if not chunk:
			break
		response.append(chunk)
	return response
	# with open('jic.txt', 'w') as jic:
	# 	for item in response:
	# 		jic.write(item.decode('utf8'))
	# 		jic.write('\n')

def setup_semafor():
	base_path = 'D:/Documents/Python/NLP/semafor-master/semafor-master/'

	semafor_parser = Popen(
		['java', '-jar',
		 base_path + 'target/Semafor-3.0-alpha=04.jar',
		 base_path + 'edu.cmu.cs.lti.ark.fn.SemaforSocketServer ',
		 'model-dir:' + base_path + 'models/semafor_malt_mdoel_20121129/',
		 'port:8080'])

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect(('127.0.0.1', 8080))

	return partial(semafor, sock=sock)

if __name__ == '__main__':
	dep_parser = setup_parser()
	synset_parser = setup_clausie()
	frame_parser = setup_semafor()