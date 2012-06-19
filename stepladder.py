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
        self.dictionary = [w for w in self.complete_dictionary if len(w)==word_length]
    
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

''' Simulated Annealing Algorithm class.
    Exposes a method that performs simulated annealing on a dictionary (passed upon instance construction) to find an optimal stepladder.
    The problem space has plenty of local minima, but the algorithm appears performant enough to reach the global minimum even with a few
    cooling steps and mutation cycles for cooling step, resulting quicker than exhaustive backtracking.   
'''
class AnnealingAlgorithm():
    
  
    ''' Start temperature'''
    __INITIAL_TEMPERATURE = 1
    
    ''' How many times do we cool'''
    __COOLING_STEPS = 10        #500
    
    ''' How much to cool each time'''
    __COOLING_FRACTION = 0.97    
    
    ''' Number of mutations cycles for each temperature cooling step - lower makes it faster, higher makes it potentially better. '''
    __STEPS_PER_TEMP = 50         #1000
    
    ''''Problem specific Boltzman's constant'''
    K = 0.001      

    ''' Constructor
        @param D:    The dictionary from were words can be drafted.
    '''
    def __init__(self, D, word_length):
        seed(time())
        self.dictionary = deepcopy(D)
        #Leaves only the words with length word_length
        self.dictionary.filter_words_by_length(word_length)
        
        return

    '''Compute the stepladder score
       Assumes that the stepladder is valid (either by construction or because it has been checked before)
       @param ladder: - The stepladder to examine
       @return:: The sum of the scores of the words in the stepladder, otherwise
    '''    
    def __stepladder_score(self, ladder):
        total_score = 0;
        for i in range(len(ladder)):    #n+1 is even => ceil((n+1)/2) == (n+1)/2 == floor((n+1)/2)
            total_score += self.dictionary.scores[ladder[i]]
        return total_score
    
    '''Checks if a ladder is a valid stepladder
       That means that the ladder is not empty, that it has an odd number of words,
       that all the words are the same length, and that the words' score is monotonically increasing
       until the certral element, and monotonically decreasing after that
       @param ladder: - The stepladder to examine
       @return: 0 <=> the stepladder is not valid
                s>0 <=> the sum of the scores of the words in the stepladder, otherwise
    '''    
    def __stepladder_check_and_score(self, ladder):
        total_score = 0;
        n = len (ladder)
        used_words = {}
        if n%2 == 0:
            return 0
        #There is at list one element in ladder because n%2==1
        K = len(ladder[0])
        #Check the first part of the ladder
        for i in range(n/2):    #n+1 is even => ceil((n+1)/2) == (n+1)/2 == floor((n+1)/2)
            w = ladder[i]
            if  w in used_words or len(w)!=K or (not self.dictionary.check_word(w)
                    or self.dictionary.scores[w] >= self.dictionary.scores[ladder[i+1]] 
                    or Dictionary.word_distance(w, ladder[i+1])!=1):
                return 0
            used_words[w] = 0   #adds the word to the list of used words (a word cannot be used twice in a ladder)
            total_score += self.dictionary.scores[w]
        
        #Check the second part of the ladder
        for i in range(n/2, n-1):    #n+1 is even => ceil((n+1)/2) == (n+1)/2 == floor((n+1)/2)
            w = ladder[i]
            if  w in used_words or len(w)!=K or (not self.dictionary.check_word(w)
                    or self.dictionary.scores[w] <= self.dictionary.scores[ladder[i+1]]
                    or Dictionary.word_distance(w, ladder[i+1])!=1):
                return 0
            used_words[w] = 0   #adds the word to the list of used words (a word cannot be used twice in a ladder)
            score = self.dictionary.scores[ladder[i]]
            total_score += score
    
        #Checks the last word
        if len(ladder[n-1])!=K or not self.dictionary.check_word(ladder[n-1]):
            return 0
        total_score += self.dictionary.scores[ladder[n-1]]
        return total_score

    '''Creates a solution at random
       Chooses at random a word to place at the center of the ladder; the probability distribution 
       in this case is not uniform, but proportional to the score of the word: higher scores word
       has much more probability to appear in the middle of stepladders than lower score ones.
       After that, keeps adding couples of words with distance 1 from the bottom and top of the ladder
       until there is no other possible couple to add;
       @return:    A valid stepladder (provided that the dictionary isn't empty)       
    '''    
    def __random_solution(self):
        #Implements a non uniform random picker, with probability proportional to each dictionary word's score
        t = sum([self.dictionary.scores[w] for w in self.dictionary.dictionary])
        pick = randrange(t)
        tot = 0
        for i in range(len(self.dictionary.dictionary)):
            tot += self.dictionary.scores[self.dictionary.dictionary[i]]
            if tot > pick:
                break
        #i is now the index of the chosen element
        solution = [self.dictionary.dictionary[i]]
        bottom = top = self.dictionary.dictionary[i]
        while True:
            bottom_neighbours = [w for w in self.dictionary.neighbours[bottom] 
                            if w not in solution and 
                                self.dictionary.scores[w] < self.dictionary.scores[bottom]]
            if len(bottom_neighbours)==0:
                return solution
            new_bottom = bottom_neighbours[randrange(len(bottom_neighbours))]
            
            top_neighbours = [w for w in self.dictionary.neighbours[top]
                              if w not in solution and
                              self.dictionary.scores[w]< self.dictionary.scores[top] ]
            if len(top_neighbours)==1 and new_bottom in top_neighbours:
                #If the only available word to be inserted at the top edge would be the one chosen for the bottom, tries to found another one for the bottom
                bottom_neighbours = [w for w in self.dictionary.neighbours[bottom]
                                     if w not in solution and 
                                        self.dictionary.scores[w] < self.dictionary.scores[bottom]
                                        and w!=new_bottom]
                if len(bottom_neighbours)==0:
                    #No choice available
                    return solution
                else:
                    #We now that new_bottom is the only word possible for new_top
                    new_top = new_bottom    
                    #And we must choose a new word for the bottom
                    new_bottom = bottom_neighbours[randrange(len(bottom_neighbours))]
                    
            elif len(top_neighbours)==0:
                return solution
            else:
                #Must avoid duplicates!!!
                if (new_bottom in top_neighbours):
                    top_neighbours.remove(new_bottom)
                    
                new_top = top_neighbours[randrange(len(top_neighbours))]
                    
            solution.insert(0, new_bottom)      
            solution.append(new_top)
            bottom = new_bottom             
            top = new_top

        return solution
    
    ''' First kind of mutation: chooses a position at random, and tries to change the word at that position according to the one neighbour closest to the
        center of the stepladder; then tries to fix the stepladder properties from there to the closest edge, until it's not possible anymore
        (at that point prunes the remaining words at the two sides of the stepladder)
        @param solution:    The current solution of the annealing;
        @return:    The new solution obtained after the mutation           
    '''
    def __mutation_1(self, solution):
        new_solution = solution[:]  #makes a copy
        #Randomly select one position
        n = len(new_solution)
        i = randrange( 0, n )
#                        if AnnealingAlgorithm.TRACE_OUTPUT:
#                            print  "swap WIN %d value %f  temp=%f i=%d j=%d\n" % (i1, current_value,temperature,i,j)    
        #Edge cases
        if i==0:
            if n>1:
                #if there is another element tries to choose another word from its neighbours list
                ns = [w for w in self.dictionary.neighbours[new_solution[1]] 
                        if w not in new_solution 
                        and self.dictionary.scores[w] < self.dictionary.scores[new_solution[1]]]
                if len(ns)>0:
                    new_solution[0] = ns[randrange(len(ns))]
                #else: if there is no valid neighbour, simply leave things as they are
                    
            else:
                #INVARIANT: there is always at least a word in a new_solution (empty ladders are not valid ladders)
                #There is only one element in the ladder: then chooses a random word from the dictionary
                new_solution[0] = self.dictionary.dictionary[randrange(len(self.dictionary.dictionary))]
        elif i==n-1:
            #INVARIANT: at this point n>=3 because otherwise i would have been 0 and the previous if would have been entered
            ns = [w for w in self.dictionary.neighbours[new_solution[n-2]]
                    if w not in new_solution
                    and self.dictionary.scores[w] < self.dictionary.scores[new_solution[n-2]]]
            if len(ns)>0:
                new_solution[n-1] = ns[randrange(len(ns))]
            #else: if there is no valid neighbour, simply leave things as they are
        else:
            #INVARIANT: at this point n>=3 because otherwise i would have been 0 and the irst if would have been entered
            #General case:
            #1) It must be determined which one is the direction that goes from the center of the ladder to the edges
            #n is odd, then n/2 is the index of the middle element
            if i==n/2:
                #Chooses the middle element absolutely randomly
                new_solution[i] = self.dictionary.dictionary[randrange(len(self.dictionary.dictionary))]
                if (Dictionary.word_distance(new_solution[i], new_solution[i+1])==1
                    and self.dictionary.scores[new_solution[i]] > self.dictionary.scores[new_solution[i+1]]):
                    delta = -1
                elif (Dictionary.word_distance(new_solution[i], new_solution[i-1])==1
                      and self.dictionary.scores[new_solution[i]] > self.dictionary.scores[new_solution[i-1]]):
                    delta = 1
                else:
                    #No way to agree with surrounding elements
                    return [new_solution[i]]
                    
            else: 
                delta = 1 - 2 * (i<n/2)      #Outputs +/- 1
                ns = [w for w in self.dictionary.neighbours[new_solution[i-delta]]
                        if w not in new_solution
                        and self.dictionary.scores[w] < self.dictionary.scores[new_solution[i-delta]]]
                if len(ns)>0:
                    new_solution[i] = ns[randrange(len(ns))]
                else:
                    #If there is no valid neighbour, simply leave things as they are
                    return new_solution

            i += delta
            #Tries to fix the stepladder property for element after the mutated one
            while (i>=0 and i<=n-1 
                   and (Dictionary.word_distance(new_solution[i],new_solution[i-delta])==1
                   and self.dictionary.scores[new_solution[i-delta]] > self.dictionary.scores[new_solution[i]])) :
                i += delta

                #continues until reaches the end of the solution, or no more elements can be added

            if (delta<0):
                new_solution = new_solution[i+1:n-i-1]
            else:
                #i > n/2 => n-i < i
                new_solution = new_solution[n-i:i]

        return new_solution
    
    '''Second kind of mutation: Tries to add new couple of words at the 2 edges of the stepladder. It is used in combination with mutation 1
       @param solution:    The current solution of the annealing;
       @return: new_solution
                The new solution obtained after the mutation    
    '''
    def __mutation_2(self,solution):
        new_solution = solution[:]  #makes a copy
        
        bottom = new_solution[0]
        top = new_solution[len(new_solution)-1]
        while True:
            bottom_neighbours = [w for w in self.dictionary.neighbours[bottom] 
                                    if w not in new_solution
                                    and self.dictionary.scores[w]< self.dictionary.scores[bottom]]
            if len(bottom_neighbours)==0:
                return new_solution
            new_bottom = bottom_neighbours[randrange(len(bottom_neighbours))]
            
            top_neighbours = [w for w in self.dictionary.neighbours[top]
                                if w not in new_solution
                                and self.dictionary.scores[w]< self.dictionary.scores[top]]
            if len(top_neighbours)==1 and new_bottom in top_neighbours:
                #If the only available word to be inserted at the top edge would be the one chosen for the bottom, tries to found another one for the bottom
                bottom_neighbours = [w for w in self.dictionary.neighbours[bottom]
                                        if w not in new_solution
                                        and self.dictionary.scores[w]< self.dictionary.scores[bottom]
                                        and w!=new_bottom]
                if len(bottom_neighbours)==0:
                    #No choice available
                    return new_solution
                else:
                    #We now that new_bottom is the only word possible for new_top
                    new_top = new_bottom    
                    #And we must choose a new word for the bottom
                    new_bottom = bottom_neighbours[randrange(len(bottom_neighbours))]
                    
            elif len(top_neighbours)==0:
                return new_solution
            else:
                #Must avoid duplicates!!!
                if (new_bottom in top_neighbours):
                    top_neighbours.remove(new_bottom)
                    
                new_top = top_neighbours[randrange(len(top_neighbours))]
                    
                    
            new_solution.insert(0,new_bottom)
            new_solution.append(new_top)
            bottom = new_bottom
            top = new_top
        return new_solution



    ''' Third kind of mutation: chooses a random position and tries to replace the word in that position with another word with an higher
        score and that mantains the stepladder legal. If no such word exists, moves the pointer towards the sides of the ladder, and tries
        again.
    
        @param solution:    The current solution of the annealing;
        @return: new_solution
                 The new solution obtained after the mutation
    '''
    def __mutation_3(self, solution):
        new_solution = solution[:]
        n = len(new_solution)
        #INVARIANT: solution has at least one element (valid stepladders have at least 1 word)
        if n == 1:
            word = new_solution[0]
            #Replaces the only word in the ladder with another one with an higher score 
            matches = [w for w in self.dictionary.dictionary
                        if (not w in new_solution)
                        and self.dictionary.scores[w] > self.dictionary.scores[word]]
            
            if len(matches) == 0:
                return new_solution
            else:
                i = randrange(len(matches))
                new_solution[0] = matches[i]
        else:
            #Chooses a position at random
            i = randrange(len(new_solution))
        
            if i<n/2:
                direction = +1
            elif i>n/2:
                direction = -1
            else:   # i == n/2
                w_before = new_solution[i-1]
                w_after = new_solution[i+1]
                matches = [w for w in self.dictionary.neighbours[w_before]
                                if (not w in new_solution)
                                and w in self.dictionary.neighbours[w_after]
                                and self.dictionary.scores[w] > w_before
                                and self.dictionary.scores[w] > w_after]
                if len(matches) == 0:
                    #Can't change the word in this position, so chooses a direction at random and moves up/down the ladder
                    if random() < 0.5:
                        direction = +1
                    else:
                        direction = -1
                    i -= direction
                else:
                    j = randrange(len(matches))
                    new_solution[i] = matches[j]

                    #As soon as it manages to make a substitution, returns    
                    return new_solution
                        
                while i>=0 and i<n:
                    word = new_solution[i]
                    
                    if i == 0 or i == n-1:
                        w_before = new_solution[i+direction]       
                        matches = [w for w in self.dictionary.neighbours[w_before] 
                                        if (not w in new_solution)
                                        and self.dictionary.scores[w] < w_before]
                    else:
                        w_before = new_solution[i+direction]
                        w_after = new_solution[i-direction]
                        matches = [w for w in self.dictionary.neighbours[w_before]
                                        if (not w in new_solution)
                                        and w in self.dictionary.neighbours[w_after]
                                        and self.dictionary.scores[w] < w_before
                                        and self.dictionary.scores[w] > w_after]
                
                    if len(matches) == 0:
                        i -= direction
                    else:
                        j = randrange(len(matches))
                        new_solution[i] = matches[j]
                        #As soon as it manages to make a substitution, returns
                        return new_solution
                        

        return new_solution





    
    
    '''Fourth kind of mutation: like the randomized inizialization, but chooses the central word at random with uniform probability
       and then chooses always the words to add at the sides according to their score (chooses the words with maximum score).
       @param solution:    The current solution of the annealing - it isn't actually used, it is taken for compatibility with the other mutation functions
       @return: new_solution
                The new solution obtained after the mutation
                
        NOTE:   this mutation has been discarded because it isn't very effective: it produces worse stepladders 99,8% of the times and even if that may help to exit from
                local minima, the ratio is too low and overall make annealing performance worse (it is not even worth contrasting it by 
                changing the Boltzman's constant)
    '''
    def __mutation_4(self, solution=None):
        
        i = randrange(len(self.dictionary.dictionary))
        new_solution = [self.dictionary.dictionary[i]]
        bottom = top = self.dictionary.dictionary[i]
        
        while True:
            bottom_neighbours = sorted([w for w in self.dictionary.neighbours[bottom]
                                            if w not in new_solution
                                            and self.dictionary.scores[w]< self.dictionary.scores[bottom]],
                                       key=lambda(w): -dictionary.scores[w])
            if len(bottom_neighbours)==0:
                return new_solution
            top_neighbours = sorted( [w for w in self.dictionary.neighbours[top]
                                            if w not in new_solution
                                            and self.dictionary.scores[w]< self.dictionary.scores[top]],
                                    key=lambda(w): -dictionary.scores[w])
            if len(top_neighbours)==0:
                return new_solution
            new_top = top_neighbours.pop()
            new_bottom = bottom_neighbours.pop()

            if new_top == new_bottom:
                if len(top_neighbours) == 0:
                    if len(bottom_neighbours) == 0:
                        return new_solution
                    else:
                        new_bottom = bottom_neighbours.pop()
                elif len(bottom_neighbours) == 0:
                    new_top = top_neighbours.pop()
                else:
                    #discards the one with the highest difference from the next word in the respective list (doesn't matter how it breaks ties because top and bottom are interchangeable concepts)
                    if (dictionary.scores[new_top] - dictionary.scores[top_neighbours[0]] <= 
                        dictionary.scores[new_bottom] - dictionary.scores[bottom_neighbours[0]]):
                        new_top = top_neighbours.pop()
                    else:
                        new_bottom = bottom_neighbours.pop()

            new_solution.insert(0, new_bottom)
            new_solution.append(new_top)
            
            bottom = new_bottom
            top = new_top
      
        return new_solution
    
    ''' Single iteration of simulated annealing
        @return: (best_value, best_solution)
                best_solution is the the best solution to the problem that this cycle of simulated annealing could find, and best_value 
                is its score according to the problem's own metric.
                
    '''
    def __annealing(self):
        
        temperature = AnnealingAlgorithm.__INITIAL_TEMPERATURE
    
        solution = self.__random_solution()
        best_solution = solution[:]
        best_value = current_value = self.__stepladder_score(solution)
        
        for i in range(AnnealingAlgorithm.__COOLING_STEPS):
            temperature *= AnnealingAlgorithm.__COOLING_FRACTION
            start_value = current_value
            
            for j in range( AnnealingAlgorithm.__STEPS_PER_TEMP ):
                for mutation in [lambda sol: self.__mutation_2(self.__mutation_1(sol)),
                                            self.__mutation_3]:               
                    new_solution = mutation(solution)

                    new_value = self.__stepladder_score(new_solution)
                    delta = new_value - current_value

                    if delta==0:
                        continue
                                            
                    flip = random()
                    exponent = float(delta/new_value)*AnnealingAlgorithm.K/temperature
                    merit = e ** exponent
    
                    if delta > 0 : # ACCEPT-WIN
                        solution = new_solution[:]
                        current_value = new_value
                        if current_value > best_value:
                            best_value = current_value
                            best_solution = solution[:]
                            
                    elif merit > flip :  #ACCEPT-LOSS
                        solution = new_solution[:]
                        current_value = new_value
    
            if  (current_value-start_value) > 0.0 : # rerun at this temp
                temperature /= AnnealingAlgorithm.__COOLING_FRACTION
    
        return (best_value, best_solution)

    '''Simulated annealing main: until all the allotted time has been used, keeps restarting
       the annealing procedure and saves its result
       @param max_time: the maximum (indicative) execution time for the annealing, in seconds;
       @return: (best_score, best_solution)
               The best solution found by simulated annealing, and its score.
    '''
    def simulated_annealing(self, max_time):
    
        ''' Checks that at least one word is saved in the dictionary
            (otherwise, no valid stepladder can be created).
            INVARIANT:  word length filter has already been applied to the
                        dictionary.
        '''
        if len(self.dictionary.dictionary) == 0:
            return 0, []
        
        start_time = time()
        best_solution = None
        best_score = 0

        #Continues until the execution exceeded the allotted time
        while time() < start_time + max_time:
                (score, solution) = self.__annealing()
                if score > best_score:
                    best_solution = solution[:]
                    best_score = score

        return (best_score, best_solution)

''' Backtracking handler class.
    Exposes a highest_score_stepladder method that, once the class is initialized with a proper dictionary, perform backtracking on
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
       the backtracking to find couple of elements to put around it
    '''
    def highest_score_stepladder(self):
        best_score = 0
        best_ladder = []
        for w in dictionary.dictionary:
            #score = backtracking([w], (w, w), scores[w])
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
        if (argv[i] == '-a' or argv[i] == '-A'):
            annealing_mode = True
            i += 1
            if i >= len(argv):
                print 'Error using option -a: it requires a maximum time allowed to be specified'
                quit()
            try:
                annealing_time = float(argv[i])
            except:
                print 'Error using option -a: maximum time allowed MUST be a decimal number'
                quit()
        
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
    
    if annealing_mode:
        #Simulated annealing:
        annealingHandler = AnnealingAlgorithm(dictionary, K)
        (best_score, best_ladder) = annealingHandler.simulated_annealing(annealing_time)        
        if verbose_mode:
            print 'Simulated annealing: best solution found in {} seconds has score: {}'.format(annealing_time, best_score)
            print best_ladder
        else:
            print best_score
    else: 
    
        backtracking = BacktrackingAlgorithm(dictionary, K)
        (best_score, best_ladder)  = backtracking.highest_score_stepladder()
        if verbose_mode:
            print 'Backtracking solution score: {}'.format(best_score)
            print best_ladder
        else:
            print best_score