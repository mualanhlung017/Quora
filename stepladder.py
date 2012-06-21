'''
@author: mlarocca02
'''
from string import upper
import re
from sys import stdin, argv
from time import time
from random import randrange, random, seed
from math import e
from copy import deepcopy

INTEGER_RE = "(\d+)"            #Regular expression: Matches any non negative integer
STRING_RE = "([A-Z]+)"          #Regular expression: Matches a string of uppercase char only

'''Constant dictionary that associates each letter in the English alphabet with its scrabble score'''
POINTS = {'A':1, 'E':1, 'I':1, 'L':1, 'N':1, 'O':1, 'R':1, 'S':1, 'T':1, 'U':1,
          'D':2, 'G':2, 'B':3, 'C':3, 'M':3, 'P':3, 'F':4, 'H':4, 'V':4, 'W':4,
          'Y':4, 'K':5, 'J':8, 'X':8, 'Q':10, 'Z':10}


''' Represents a lexical Dictionary, i.e. a collection of
    all the admissible words.
    Provides attributes and methods to handle all the required operations,
    like filtering, computing word distance and neighborhood, and
    computing scores.
'''
class Dictionary():
    
    ''' Constructor:    inits the attributes of this class
    '''
    def __init__(self):
        #Lists of words in the dictionary; May be the result of filtering on the original dictionary;
        self.dictionary = []
        #Complete lists of words in the dictionary, as it is read from the input file: filtering takes this as input, making the same dictionary
        #reusable under different filtering requirements, without having to read again form the input (since it might also be impossible to do so).
        self.complete_dictionary = []
        #Stores the scores of the words in the dictionary in a python dictionary, so that it avoids recomputing it every time
        self.scores = {}
        #Adiacency vectors (each word is like a vertex in a graph with 1 edge between each couple of words with Hamming distance 1)
        self.neighbours = {}
    
    ''' Computes the score associated with the word passed as its parameter, if it is a valid one.
        @param word:    The word whose score needs to be computed;
        @return:    The score associated with the word (i.e., the sum of the scrabble scores for each of its characters).
    '''
    def word_score(self, word):
        word = upper(word)
        if not self.check_word(word):
            return 0 
        score = 0
        for i in range(len(word)):
            #INVARIANT: word characters must be in the range [A-Z]- it's OK to raise an exception otherwise
            score += POINTS[word[i]]
        return score
    
    ''' Checks if the passed word belongs to the dictionary.
        @param word:    The word to be checked;
        @return:    True <=> word belong to the dictionary.
    '''
    def check_word(self, word):
        #INVARIANT: word characters must be in the range [A-Z]
        #WARNING: it will returns False otherwise
        return word in self.dictionary
    
    ''' Filters the dictionary leaving only words with 'word_length' characters. As a basis for the filter uses the complete list of words read from the input.
        @param word_length:    The desired word length;
    '''
    def filter_words_by_length(self, word_length):
        self.dictionary = [w for w in self.complete_dictionary if len(w) == word_length]
    
    ''' Reads the input from a file f
        The input is assumed to be formatted as follows:
        First line: 1 integer K
        Second line: 1 integer N
        N lines composed by strings (Possibly of K characters - since it is not specified, we omit the check on words length here, since it won't affect the output)
       
        @param f:   The file from which to read the input (stdin by default)
        @return:    The selected word length K, as read from the input.
    '''
    def read_dictionary_from_file(self, f = stdin):
        regex = re.compile(INTEGER_RE)  #Regular Expression for integers
        #INVARIANT: the input is assumed well formed and adherent to the specs above
        line = f.readline()
        K  = int( regex.findall(line)[0] )
        line = f.readline()
        N  = int ( regex.findall(line)[0] )
        
        regex = re.compile(STRING_RE)  #Regular Expression for strings
        #Reads the words list
        for i in range(N):
            #Since no assumption is made on the input, it must be cheched that it is well formatted
            #Exceptions are raised here and caught in the outer loop
            line = f.readline()
            w = regex.findall(line)[0]
            if w != None and len(w) > 0:
                self.dictionary.append(w)
                self.scores[w] = self.word_score(w)
            else:
                raise "Invalid input: "
        self.complete_dictionary = self.dictionary[:]    #makes a copy, since it's going to be possible to restrict the dictionary to one of its subsets
        return K
    
    ''' Computes the distance between two words; the metric used consider the Hamming distance between two words, so for two words of the
        same length it is the number of positions in which the two strings' characters differ. Two strings of different length shouldn't 
        be even comparable; for practical purposes, the distance returned in these cases is the sum of the lengths (which is greater than
        the maximum possible distance for either word in comparison with any word of the same respective length).
        @param w1:    First word to compare;
        @param w2:    Second words to compare (order doesn't matter cause Hamming distance is commutative according to its definition);
        @return:    The Hamming distance between the two words
    '''
    @staticmethod
    def word_distance(w1, w2):
        if len(w1)!=len(w2):
            return len(w1) + len(w2)
        else:
            d = 0
            for i in range(len(w1)):
                if w1[i] != w2[i]:
                    d += 1
            return d
    
    '''For every word in the dictionary, makes a list of its neighbours, i.e. the words with a distance
       of exactly one (meaning that the two words differ for just one character)
       The list of neighbours is stored inside the Dictionary instance, but it is also returned to the caller.
       @return:    A python dictionary containing, for every word in the Dictionary, the list of its neighbours.
    '''
    def compute_neighbours_list(self):
        self.neighbours = {}
        for i in range(len(self.dictionary)):
            
            for j in range(i+1,len(self.dictionary)):
                #INVARIANT: no word appears twice in the dictionary!
                if Dictionary.word_distance(self.dictionary[i], 
                                            self.dictionary[j]) == 1:
                    if self.dictionary[i] in self.neighbours:
                        self.neighbours[self.dictionary[i]].append(self.dictionary[j])
                    else:
                        self.neighbours[self.dictionary[i]] = [self.dictionary[j]]
                    
                    if self.dictionary[j] in self.neighbours:
                        self.neighbours[self.dictionary[j]].append(self.dictionary[i])
                    else:
                        self.neighbours[self.dictionary[j]] = [self.dictionary[i]]
            #if the word hasn't been added to the dictionary yet...
            if not self.dictionary[i] in self.neighbours:
                self.neighbours[self.dictionary[i]] = []
        
        return self.neighbours

''' Backtracking handler class.
    Exposes a highest_score_stepladder method that, once the class is initialized with a proper dictionary, perform start on
    the word contained in that dictionary in order to find the highest score possible stepladder.
'''
class BacktrackingAlgorithm():

    '''Constructor
    '''
    def __init__(self, D, word_length):
        self.dictionary = deepcopy(D)
        #Leaves only the words with length word_length
        self.dictionary.filter_words_by_length(word_length)

    ''' Backtracking: tries to add every legal couple of words at the extremes of the stepladder, and then calls itself recursively
        to try to further extend the ladder.
        @param ladder:    A valid stepladder
        @param (bottom, top):    First and last element of the stepladder to be extended
        @param score:    The score of the input stepladder (makes it easy to compute the new score without having to examine again all every word in the stepladder)
        @return:    (best_score, best_ladder)
                    best_ladder is the best extension to ladder that the function could find (possibly ladder itself), and best_score is its score.
    '''
    
    def __backtracking(self, ladder, (bottom, top), score ):
        bottom_neighbours = [w for w in self.dictionary.neighbours[bottom]
                                if (not w in ladder)
                                and self.dictionary.scores[w] < self.dictionary.scores[bottom]]
        top_neighbours = [w for w in self.dictionary.neighbours[top]
                            if (not w in ladder)
                            and self.dictionary.scores[w] < self.dictionary.scores[top]]
        best_score = score
        best_ladder = ladder
        #checks every possible couple of words to add to bottm and top
        for wb in bottom_neighbours:
            for wt in top_neighbours:
                if wb!=wt:
                    (tmp_score, tmp_ladder) = self.__backtracking([wb]+ladder + [wt],
                                                                  (wb,wt),
                                                                  score + self.dictionary.scores[wb]
                                                                  + self.dictionary.scores[wt])
                    if tmp_score > best_score:
                        best_score = tmp_score
                        best_ladder = tmp_ladder
        
        return (best_score, best_ladder)
                 
        
    '''For each word in the dictionary, inits a stepladder with that word as the central word, and then starts
       the start to find couple of elements to put around it
    '''
    def highest_score_stepladder(self):
        best_score = 0
        best_ladder = []
        for w in self.dictionary.dictionary:
            #score = start([w], (w, w), scores[w])
            (score, ladder) = self.__backtracking([w], (w, w), self.dictionary.scores[w])
            if (score>best_score):
                best_ladder = ladder[:]
                best_score = score

        return (best_score, best_ladder)    



''' Main.    
    USAGE:
    -f filename: Reads input from a file [by default it reads input from stdin]
    -a seconds: Try to solve the problem using simulated annealing; The allotted time for the annealing must specified as a float number
                right after the option tag.
    -v        : Verbose mode: details on the Dictionary read from the input and on the solution will be displayed to help debugging;
                WARNING: the output will not match the challenge specifications (just the score of the best solution) in verbose mode 
'''    
if __name__ == '__main__':
   
    annealing_mode = False
    verbose_mode = False
    file_in = stdin
   
    for i in range(1,len(argv)):
        if (argv[i] == '-f'):
            i += 1
            if i >= len(argv):
                print 'Error using option -f: filename required'
                break
            try:
                #Takes the second parameter
                file_in = open(argv[i],'r')
            except:
                print 'The requested file: {} does not exist. Please insert your input from the terminal.'.format( argv[i])
                file_in = stdin
        if (argv[i] == '-v' or argv[i] == '-V'):
            verbose_mode = True
                        
    dictionary = Dictionary()
    K = dictionary.read_dictionary_from_file(file_in)
    if file_in!=stdin:
        file_in.close()
    
    if verbose_mode:
        print 'Dictionary:'
        print [(w,dictionary.scores[w]) for w in dictionary.dictionary ]
    
    dictionary.compute_neighbours_list()
    
    start = BacktrackingAlgorithm(dictionary, K)
    (best_score, best_ladder)  = start.highest_score_stepladder()
    if verbose_mode:
        print 'Backtracking solution score: {}'.format(best_score)
        print best_ladder
    else:
        print best_score