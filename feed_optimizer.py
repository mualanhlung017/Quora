'''
@author: mlarocca
'''

from time import time
from random import random, randrange, seed
from math import copysign
import re
from sys import stdin, stdout, argv
from copy import deepcopy
from math import e



''' For convenience, gather all the parameters of a story and make them identifiable
    with a name rather than its position. Being a convenience wrapper, parameters are
    not marked as private, although using Python naming convention they are marked
    as read only.
    The wrapper class is also used to keep track of the order of creation of the
    stories, hence automatically assigning IDs to the stories on construction.
'''
class Story():
    '''__counter: class attribute, keeps track of how many stories have been created'''
    __counter = 0
    
    ''' Contructor
        @param time:    Time of creation of the story, as read from the input;
        @param _score:    Score of the story;
        @param height:    Height needed to show the story.
    '''
    def __init__(self, time, score, height):
        self._time = time
        self._score = score
        self._height = height
        self._scaled_score = float(score)/height
        Story.__counter += 1
        self._id = Story.__counter
        





 
''' Convenience class for a solution
''' 
class Solution():
    
    def __init__(self, mask, size, score, height):
        self.mask = deepcopy(mask)
        self.size = size
        self.score = score
        self.height = height
 
''' Simulated Annealing Algorithm class.
    Exposes a method that performs simulated annealing on a dictionary (passed upon instance construction) to find an optimal stepladder.
    The problem space has plenty of local minima, but the algorithm appears performant enough to reach the global minimum even with a few
    cooling steps and mutation cycles for cooling step, resulting quicker than exhaustive start.   
'''
class BacktrackingAlgorithm():
  
    ''' Constructor
        @param full_stories_set:    The set of all the stories available, ordered
                                    according to the ratio score/height of each story,
                                    from the largest to the smallest
        @param page_height:    The limit for the sum of the story heights (i.e.
                                the capacity of the Knapsack)
    '''
    def __init__(self, full_stories_set, page_height):
        seed(time())
        self.__full_stories_set = full_stories_set
        self.__N = len(self.__full_stories_set)
        self.__page_height = page_height
        
        return

    ''' Returns the list of the stories corresponding to ones in the mask;
        @param mask: A binary mask corresponding to a subset of the stories
        @return: The corresponding list of ids.
    '''
    def __get_subset(self, mask):
        #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
        return sorted([self.__full_stories_set[i] for i in range(len(mask)) if mask[i]], key=lambda s: s._id )

    ''' Returns the list of the ids of the stories corresponding to ones in the mask; 
        @param mask: A binary mask corresponding to a subset of the stories:
        @return: The corresponding list of ids.
    '''
    def __get_subset_ids(self, mask):
        #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
        return [self.__full_stories_set[i]._id for i in range(len(mask)) if mask[i]]


    ''' Compares two solutions according to the specifications;
        solution_1 is better than solution_2 iff
        1) Has an higher score,
        2) Has the same score, but with fewer stories,
        3) Has the same score and the same number of stories, but the set of
            stories IDs of solution_1 comes lexicographically before solution_2's.
        @param solution_1, solution_2: The two solutions to compare;
        @return:    -1 <=> solution_1 is a better solution than solution_2, or it is equal to solution_2
                    1 <=> vice versa.
    '''
    def compareSolutions(self, solution_1, solution_2):
        
        #INVARIANT: all solutions tested are valid
        if solution_1.score > solution_2.score:
            return -1
        elif solution_1.score < solution_2.score:
            return 1
        else:
            if solution_1.size < solution_2.size:
                return -1
            elif solution_1.size > solution_2.size:
                return 1
            else:
                stories_ids_1 = sorted(self.__get_subset_ids(solution_1.mask))
                stories_ids_2 = sorted(self.__get_subset_ids(solution_2.mask))
                if stories_ids_1 <= stories_ids_2:
                    return -1
                else:
                    return 1

    ''' Performs, recursively, the Horowitz-Sahni algorithms for 0-1 KP problem.
        INVARIANT: the elements to put in the knapsack must be ordered according
                    to the ratio value/cost, from the highest to the lowest.
        For each call, unless the whole list has been already examined (pos >= self.__N)
        examine recursively the two branches of the solution tree;
        if the element corresponding to the current position can't be added to
        the solution (because its cost is too high) checks whether it was
        performing a "forward move", i.e. adding as many (at least 1) consecutive
        elements as possible to the solution, and in that case compare the current
        solution with the best one so far (it is safe to do so because if the
        algorithm is not performing a forward move no element has been added to
        the current solution since the last time it was compared to the best one.
        
        @param mask:    A bit mask that keeps track of the elements added to the
                        solution so far;
        @param size:    The number of elements added to the knapsack so far;
        @param score:   Total score for the current solution;
        @param height:    Total height for the curent solution;
        @param pos:    The index of the new element to examine;
        @param forward_move: Is the algorithm performing a forward move or a backtracking move?
    '''
    def __horowitz_sahni(self, mask, size, score, height, pos, forward_move):
        if pos >= self.__N:
            if forward_move:
                solution = Solution(mask, size, score, height)
                if self.compareSolutions(solution, self.__best_solution) < 0:
                    self.__best_solution = solution
            return
            
        story = self.__full_stories_set[pos]
        residual_capacity = self.__page_height - height
        #First tries a forward move, if possible
        if story._height > residual_capacity:   #Pruning
            if forward_move:
                solution = Solution(mask, size, score, height)
                if self.compareSolutions(solution, self.__best_solution) < 0:
                    self.__best_solution = solution
        else:
            mask[pos] = 1
            self.__horowitz_sahni(mask, size + 1, score + story._score, height + story._height, pos + 1, True)
            mask[pos] = 0
            
        #Then performs a backtracking
        self.__horowitz_sahni(mask, size, score, height, pos + 1, False)
    

    ''' Shorthand: Performs the Horowitz-Sahni algorithms on the input, and
        then returns the best solution found.
    '''
    def start(self):
        
        self.__best_solution = Solution([0 for i in range(self.__N)], 0, 0, 0)
        self.__horowitz_sahni(deepcopy(self.__best_solution.mask), 0, 0, 0, 0, True)
        return self.__best_solution.score, self.__get_subset(self.__best_solution.mask)


        
'''REGULAR EXPRESSIONS'''

'''Regular Expression: Matches any non negative integer'''
INTEGER_RE = '(\d+)'
'''Regular Expression: Matches a space character (the only separator admitted)'''
SEPARATOR_RE = ' '                 #We consider just spaces as separators
'''Regular Expression: Matches a "story"-type line of input'''
STORY_RE = 'S' + (SEPARATOR_RE + INTEGER_RE)*3
'''Regular Expression: Matches a "reload" type line of input'''
RELOAD_RE = 'R' + SEPARATOR_RE + INTEGER_RE



'''UTILITIES FUNCTIONS'''



'''Reads the input from a file f
   The input is assumed to be formatted as follows:
   First line: 3 integers __N  W  H
   __N lines representing events, and so composed by 1 char (the event type) followed by either 1 or 3 integers
   @param f:    The file from which the input should be read;
   @return: 
               events:    The list of events.
               W:    The _time window to use to distinguish recent __full_stories_set from too old ones
               H:    The page _height, in pixel
'''
def read_input(f):
    line = f.readline()
        
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the specs above
    [N, W, H]  = regex.findall(line)
    
    N = int(N)
    W = int(W)
    H = int(H)

    events = []

    #Reads the topics list
    regex_story = re.compile(STORY_RE)
    regex_reload = re.compile(RELOAD_RE)
    
    for i in range(N):
        line = f.readline()
        m_story = regex_story.match(line)
        if m_story != None:
            #INVARIANT: the input is assumed to be well formed
            events.append(('S', int(m_story.group(1)), int(m_story.group(2)), int(m_story.group(3))))
        else:
            m_reload = regex_reload.match(line)
            if m_reload != None:
                #INVARIANT: the input is assumed to be well formed
                events.append(('R', int(m_reload.group(1))))
            else:
                #Bad formatted input
                raise "Bad formatted input!"

    return events, W, H


''' Main flow of the program.
    Reads the input from the input file (stdin by default), collects every command
    in a separate element of a list, and then executes them one by one.
    For every reload command, runs the Horowitz-Sahni backtracking algorithm.
    
    @param file_in:    The file from which to read the input;
    @param file_out:    The file on which the output should be written;
'''
def main_handler(file_in, file_out):

    results_set = []
    stories_set = []
      
    events_set, time_window, page_height = read_input(file_in)

    for event in events_set:        
        if event[0] == 'S':
            #It's a story that must be added to DB
            story = Story(event[1], event[2], event[3])
            
            i = 0
            while i < len(stories_set) and story._scaled_score < stories_set[i]._scaled_score:
                    i += 1
            stories_set.insert(i, story)
            #sorted(full_stories_set, key=lambda s:float(s._score)/s._height, reverse=True)
        elif event[0] == 'R':
            #Prunes the stories too old to be interesting (they won't be considered in the future) 
            #and the ones to large to fit on the page
            min_time = event[1] - time_window
            stories_set = [story for story in stories_set
                              if story._time >= min_time
                              and story._height <= page_height ]
            
            backtrack = BacktrackingAlgorithm(stories_set, page_height)

            score, subset = backtrack.start()
            
            result_string = '{} {}'.format(score, len(subset))
            for story in subset:
                result_string += ' {}'.format(story._id)
            results_set.append(result_string+'\n')
                 
    file_out.writelines(results_set)
        
    file_in.close()
    file_out.close()

 
 
 
''' Main.
    Interpret the command line parameters, if any, and then gives the control to
    the "real" main.
    
    USAGE:
    -f filename: Reads input from a file [by default it reads input from stdin]
    -o filename: Writes output to a file [by default it writes output on stdout]
'''
if __name__ == '__main__':
    
    DEFAULT_TIME_LIMIT = 4.5
    
    file_in = stdin
    file_out = stdout
        
    for i in range(1, len(argv)):
        if (argv[i] == '-f'):
            i += 1
            if i >= len(argv):
                print 'Error using option -f: filename required'
                break
            try:
                #Takes the second parameter
                file_in = open(argv[i], 'r')
            except:
                print 'The requested file: {} does not exist. Please insert your input from the terminal.'.format(argv[i])
                file_in = stdin
        if (argv[i] == '-o'):
            i += 1
            if i >= len(argv):
                print 'Error using option -o: filename required'
                break
            try:
                #Takes the second parameter
                file_out = open(argv[i], 'w')
            except:
                print 'The requested file: {} does not exist. Output will be redirected to stdout.'.format(argv[i])
                file_out = stdout
    
    main_handler(file_in, file_out)
