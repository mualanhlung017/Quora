'''
@author: mlarocca02
'''
from string import upper
import re
from sys import stdin

INTEGER_RE = "(\d+)"            #Regular expression: Matches any non negative integer
STRING_RE = "([A-Z]+)"          #Regular expression: Matches a string of uppercase char only

'''Constant dictionary that associates each letter in the English alphabet with its scrabble score'''
POINTS = {'A':1, 'E':1, 'I':1, 'L':1, 'N':1, 'O':1, 'R':1, 'S':1, 'T':1, 'U':1,
          'D':2, 'G':2, 'B':3, 'C':3, 'M':3, 'P':3, 'F':4, 'H':4, 'V':4, 'W':4,
          'Y':4, 'K':5, 'J':8, 'X':8, 'Q':10, 'Z':10}


''' Reads the input from a file f
    The input is assumed to be formatted as follows:
    First line: 1 integer K
    Second line: 1 integer N
    N lines composed by strings (Possibly of K characters - since it is not specified, we omit the check on words length here, since it won't affect the output)
   
    @param f:   The file from which to read the input (stdin by default)
    @return:    The selected word length K, as read from the input.
'''
def read_dictionary_from_file():
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the specs above
    line = stdin.readline()
    K  = int( regex.findall(line)[0] )
    line = stdin.readline()
    N  = int ( regex.findall(line)[0] )
    
    regex = re.compile(STRING_RE)  #Regular Expression for strings
    
    dictionary = []
    scores = {}
    
    ''' Computes the score associated with the word passed as its parameter, if it is a valid one.
        @param word:    The word whose score needs to be computed;
        @return:    The score associated with the word (i.e., the sum of the scrabble scores for each of its characters).
    '''
    def word_score(word):
        word = upper(word)
        score = 0
        for i in range(len(word)):
            #INVARIANT: word characters must be in the range [A-Z]- it's OK to raise an exception otherwise
            score += POINTS[word[i]]
        return score
        
    #Reads the words list
    for i in range(N):
        #Since no assumption is made on the input, it must be cheched that it is well formatted
        #Exceptions are raised here and caught in the outer loop
        line = stdin.readline()
        w = regex.findall(line)[0]
        if len(w) == K:     #Filter over word length
            dictionary.append(w)
            scores[w] = word_score(w)

    return K, dictionary, scores
      
    
'''For every word in the dictionary, makes a list of its neighbours, i.e. the words with a distance
   of exactly one (meaning that the two words differ for just one character)
   The list of neighbours is stored inside the Dictionary instance, but it is also returned to the caller.
   @return:    A python dictionary containing, for every word in the Dictionary, the list of its neighbours.
'''
def compute_neighbours_list(dictionary):
    neighbours = {}
   
    def are_neighbours(w1, w2):

        #INVARIANT:  The two words have the same length  
        i = 0
        diff = False
        while i < len(w1):
            if w1[i] != w2[i]:
                i += 1
                diff = True
                break
            else:
                i += 1
        #Now either the distance is at least one, or it is zero (in the latter case skips the next while)
        while i < len(w1):
            if w1[i] != w2[i]:
                return False    #Distance is at least 2
                break
            else:
                i += 1 
        
        return diff                       

        
    for i in range(len(dictionary)):
        
        for j in range(i+1,len(dictionary)):
            #INVARIANT: no word appears twice in the dictionary!
            if are_neighbours(dictionary[i], 
                                        dictionary[j]):
                if dictionary[i] in neighbours:
                    neighbours[dictionary[i]].append(dictionary[j])
                else:
                    neighbours[dictionary[i]] = [dictionary[j]]
                
                if dictionary[j] in neighbours:
                    neighbours[dictionary[j]].append(dictionary[i])
                else:
                    neighbours[dictionary[j]] = [dictionary[i]]
        #if the word hasn't been added to the dictionary yet...
        if not dictionary[i] in neighbours:
            neighbours[dictionary[i]] = []
    
    return neighbours
    
'''For each word in the dictionary, inits a stepladder with that word as the central word, and then starts
   the start to find couple of elements to put around it
'''
def highest_score_stepladder():

    word_length, dictionary, scores = read_dictionary_from_file()
    
    dictionary = sorted([w for w in dictionary if len(w) == word_length], key=lambda w: scores[w], reverse=True)
    
    neighbours = compute_neighbours_list(dictionary)
 
 
    ''' Backtracking: tries to add every legal couple of words at the extremes of the stepladder, and then calls itself recursively
        to try to further extend the ladder.
        @param ladder:    A valid stepladder
        @param (bottom, top):    First and last element of the stepladder to be extended
        @param score:    The score of the input stepladder (makes it easy to compute the new score without having to examine again all every word in the stepladder)
        @return:    (best_score, best_ladder)
                    best_ladder is the best extension to ladder that the function could find (possibly ladder itself), and best_score is its score.
    '''
    
    def backtracking(ladder, (bottom, top), score ):
        bottom_neighbours = [w for w in neighbours[bottom]
                                if (not w in ladder)
                                and scores[w] < scores[bottom]]
        top_neighbours = [w for w in neighbours[top]
                            if (not w in ladder)
                            and scores[w] < scores[top]]
        best_score = score
        #best_ladder = ladder
        #checks every possible couple of words to add to bottm and top
        for wb in bottom_neighbours:
            for wt in top_neighbours:
                if wb!=wt:
                    #(tmp_score, tmp_ladder) = 
                    tmp_score = backtracking(ladder + [wb, wt],
                                             (wb,wt),
                                             score + scores[wb]
                                             + scores[wt])
                    if tmp_score > best_score:
                        best_score = tmp_score
                        #best_ladder = tmp_ladder
        
        return best_score       #(best_score, best_ladder)
    
    best_score = 0  #If the dictionary is empty, it must return 0

    #best_ladder = []
    for w in dictionary:
        #score = start([w], (w, w), scores[w])
        #(score, ladder) = backtracking([w], (w, w), scores[w])
        
        #Upperbound on score:
        s_w = scores[w]
        if best_score >= s_w **2:
            continue
       
        #The first time inside the cycle the score of the central word is added twice
        stack = [(w,w, [], -scores[w])]
        s_append = stack.append
        s_pop = stack.pop
        
        while len(stack) > 0:
            
            bottom, top, old_ladder, score = s_pop()
            score += scores[top] + scores[bottom]
            
            ladder = old_ladder[:]
            ladder.append(bottom)
            ladder.append(top)
            
            if score > best_score:
                best_score = score
            bottom_neighbours = [w for w in neighbours[bottom]
                                    if (not w in ladder)
                                    and scores[w] < scores[bottom]]
            top_neighbours = [w for w in neighbours[top]
                                if (not w in ladder)
                                and scores[w] < scores[top]]
            #best_ladder = ladder
            #checks every possible couple of words to add to bottm and top
            for wb in bottom_neighbours:
                for wt in top_neighbours:
                    s_wt = scores[wt]
                    s_wb = scores[wb]
                    if wb!=wt and score + s_wb*(s_wb+1)/2 + s_wt*(s_wt+1)/2 > best_score:  #Upper bound on possible score
                        s_append((wb, wt, ladder, score))

    return best_score 


''' Main.    
    USAGE:
    -f filename: Reads input from a file [by default it reads input from stdin]
    -a seconds: Try to solve the problem using simulated annealing; The allotted time for the annealing must specified as a float number
                right after the option tag.
    -v        : Verbose mode: details on the Dictionary read from the input and on the solution will be displayed to help debugging;
                WARNING: the output will not match the challenge specifications (just the score of the best solution) in verbose mode 
'''    
if __name__ == '__main__':

    #(best_score, best_ladder)  = start.highest_score_stepladder()
    best_score  = highest_score_stepladder()

    print best_score