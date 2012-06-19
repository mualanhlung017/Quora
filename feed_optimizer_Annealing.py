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
        Story.__counter += 1
        self._id = Story.__counter





 
''' Convenience class for a solution
''' 
class Solution():
    
    def __init__(self, mask, size, valid, score, height):
        self.mask = mask
        self.size = size
        self.valid = valid    
        self.score = score
        self.height = height
 
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
    __STEPS_PER_TEMP = 5#0         #1000
    
    ''''Problem specific Boltzman's constant'''
    __K = 1e-13   

    ''' Constructor
        @param D:    The dictionary from were words can be drafted.
    '''
    def __init__(self, full_stories_set, page_height):
        seed(time())
        self.__full_stories_set = full_stories_set
        self.__chromosome_length = len(full_stories_set)
        self.__page_height = page_height
        
        return
    
    def __get_subset(self, mask):
        #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
        return [self.__full_stories_set[i] for i in range(len(mask)) if mask[i]]


    def compareSolutions(self, solution1, solution2):
        
        if solution1.valid:
            if not solution2.valid:
                return -1
            else:
                if solution1.score > solution2.score:
                    return -1
                elif solution1.score < solution2.score:
                    return 1
                else:
                    if solution1.size < solution2.size:
                        return -1
                    elif solution1.size > solution2.size:
                        return 1
                    else:
                        if solution1.mask <= solution2.mask:
                            return -1
                        else:
                            return 1
        elif solution2.valid:
            return 1 
        else:
            if solution1.score > solution2.score:
                return -1
            elif solution1.score < solution2.score:
                return 1
            else:
                if solution1.size < solution2.size:
                    return -1
                elif solution1.size > solution2.size:
                    return 1
                else:
                    if solution1.mask <= solution2.mask:
                        return -1
                    else:
                        return 1
            

    ''' Creates a solution at random
        Initialize the bit mask .
        The probability distribution over the space of the subsets is uniform.
        @return:    A Solution Object.
    '''
    def __random_solution(self):
        N = self.__chromosome_length
        mask = [0 for i in range(N)]
        #Create an array with a random permutation of the indices
        #(with uniform distribution over the set of all permutations)
        indices = range(N)
        for i in range(N):
            j = randrange(i,N)
            tmp = indices[i]
            indices[i] = indices[j]
            indices[j] = tmp
        
        score = 0
        height = 0
        size = 0
        while (size < N):   #Adds random stories until the limit would be crossed
            i = indices[size]
            story = self.__full_stories_set[i]
            if height + story._height < self.__page_height:
                mask[i] = 1
                score += story._score
                height += story._height
                size += 1
            else:
                break;

        valid = 1

        return Solution(mask, size, valid, score, height)

    
    ''' First kind of mutation:         
        One flag, chosen at random, is flipped, so that one story previously
        included in the set won't be included anymore, or viceversa;
        @param solution:    The current solution of the annealing;
        @return:    The new solution obtained after the mutation           
    '''
    def __mutation_1(self, solution):
        mask = deepcopy(solution.mask)
        point = randrange(self.__chromosome_length)
        mask[point] = int( copysign(mask[point]-1, 1) )
        if mask[point]:
            size = solution.size + 1
            score = solution.score + self.__full_stories_set[point]._score
            height = solution.height + self.__full_stories_set[point]._height
        else:
            size = solution.size - 1
            score = solution.score - self.__full_stories_set[point]._score
            height = solution.height - self.__full_stories_set[point]._height
        
        if height <= self.__page_height:
            valid = 1
        else:
            valid = 0   
        return Solution(mask, size, valid, score, height)
        

    ''' Single iteration of simulated annealing
        @return: (best_value, best_solution)
                best_solution is the the best solution to the problem that this cycle of simulated annealing could find, and best_value 
                is its _score according to the problem's own metric.
                
    '''
    def __annealing(self):
        
        temperature = AnnealingAlgorithm.__INITIAL_TEMPERATURE
    
        solution = self.__random_solution()
        best_solution = deepcopy(solution)
        
        for i in range(AnnealingAlgorithm.__COOLING_STEPS):
            temperature *= AnnealingAlgorithm.__COOLING_FRACTION
            
            start_solution = deepcopy(solution)
            
            for j in range( AnnealingAlgorithm.__STEPS_PER_TEMP ):
                new_solution = self.__mutation_1(solution)

                delta = float(solution.valid * solution.score - new_solution.valid * new_solution.score) / (new_solution.score + 1)

                flip = random()
                exponent = delta * AnnealingAlgorithm.__K/temperature
                merit = e ** exponent

                if self.compareSolutions(new_solution, solution) < 0 : # ACCEPT-WIN
                    solution = deepcopy(new_solution)
                    if self.compareSolutions(solution, best_solution) < 0:
                        best_solution = deepcopy(solution)
                        
                elif merit > flip :  #ACCEPT-LOSS
                    solution = deepcopy(new_solution)
    
            if  self.compareSolutions(start_solution, solution) < 0 : # rerun at this temp
                temperature /= AnnealingAlgorithm.__COOLING_FRACTION
    
        return best_solution

    '''Simulated annealing main: until all the allotted time has been used, keeps restarting
       the annealing procedure and saves its result
       @param max_time: the maximum (indicative) execution time for the annealing, in seconds;
       @return: (best_score, best_solution)
               The best solution found by simulated annealing, and its _score.
    '''
    def simulated_annealing(self, max_time, file_log=None):
    
        ''' Checks that at least one word is saved in the dictionary
            (otherwise, no valid stepladder can be created).
            INVARIANT:  word length filter has already been applied to the
                        dictionary.
        '''
        if len(self.__full_stories_set) == 0:
            return 0, []
        
        start_time = time()
        best_solution = None

        #Continues until the execution exceeded the allotted time
        while time() < start_time + max_time:
                solution = self.__annealing()
                if (best_solution == None
                    or self.compareSolutions(solution, best_solution) < 0):
                    
                    best_solution = deepcopy(solution)
                    
                if file_log:
                    file_log.write("Best: ({}, score:{})  -  Last:  ({}, score:{})\n"
                                   .format(best_solution.valid, best_solution.score, 
                                           solution.valid, solution.score))
        if best_solution.valid:
            return best_solution.score, self.__get_subset(best_solution.mask)
        else:
            return 0, []






        
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
   First line: 3 integers __chromosome_length  W  H
   __chromosome_length lines representing events, and so composed by 1 char (the event type) followed by either 1 or 3 integers
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
    For every reload command, runs a genetic algorithm to explore the
    solution space quickly: although the best solution isn't guaranteed, the
    algorithm has proven quite effective. The results of the reload commands
    are stored in a list of strings, which is in turn printed on the output
    file (stdout by default) after all the commands have been examined.
    
    @param file_in:    The file from which to read the input;
    @param file_out:    The file on which the output should be written;
    @param file_log:    If it is specified, writes accessory info on it during the
                        execution;
    @param population_size:    The number of individuals evolved by the GA
                                (MUST be greater than 4)
    @param global_time_limit:    The allotted time for the whole program;
                                    Starting from this value, it is computed
                                    a time limit for each of the reload request,
                                    with some margin given the low precision of
                                    the mechanism used to limit the execution
                                    time of each run of the GA.
                                    
'''
def main_handler(file_in, file_out, file_log, population_size, global_time_limit):
      
    results_set = []
    stories_set = []
      
    events_set, time_window, page_height = read_input(file_in)

    #Counts the number of reloads in order to assign a time_limits for each
    #optimization that allows the execution to run within the global _time 
    #limit (4.5 seconds by default)
    runs = len([e for e in events_set if e[0]=='R'])
    if runs == 0:
        raise "No reload request in the input!"
    time_limit = float(global_time_limit) / (1. + runs)   
    
    for event in events_set:
        if event[0] == 'S':
            #It's a story that must be added to DB
            stories_set.append(Story(event[1], event[2], event[3]))
        elif event[0] == 'R':
            min_time = event[1] - time_window
            recent_stories = [story for story in stories_set if story._time >= min_time ]
            annealing = AnnealingAlgorithm(recent_stories, page_height)

            if file_log != None:
                file_log.write('Request at time {}\n'.format(event[1]))
            
            score, subset = annealing.simulated_annealing(time_limit, file_log)
            
            result_string = '{} {}'.format(score, len(subset))
            for story in subset:
                result_string += ' {}'.format(story._id)
            results_set.append(result_string+'\n')
                 
    file_out.writelines(results_set)
        
    file_in.close()
    file_out.close()
    if file_log != None:
        file_log.close()

 
 
 
''' Main.
    Interpret the command line parameters, if any, and then gives the control to
    the "real" main.
    
    USAGE:
    -f filename: Reads input from a file [by default it reads input from stdin]
    -o filename: Writes output to a file [by default it writes output on stdout]
    -l filename: Logs debug info, like intermediate results, on a log file
                    NOTE: for -o option only, it is possible to specify 'stdout' explicitly as the output stream;
    -tl time_limit: Set a (approximate) time limit in seconds for the global execution [Default is 4.5 seconds]
    -ps population_size: Set the dimension of the population evolved by the GA [Default is 25];
                            Larger population means getting to the optimal result in fewer generations,
                            but also allows fewer generation to be trained in a fixed time.
'''
if __name__ == '__main__':
    
    DEFAULT_TIME_LIMIT = 4.5
    DEFAULT_POPULATION_SIZE = 25
    
    file_in = stdin
    file_out = stdout
    file_log = None
    population_size = DEFAULT_POPULATION_SIZE
    
    time_limit = DEFAULT_TIME_LIMIT

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
        if (argv[i] == '-l'):
            i += 1
            if i >= len(argv):
                print 'Error using option -l: filename required'
                break
            try:
                #Takes the second parameter as the filename
                if ('stdout' == argv[i]):
                    file_log = stdout
                else:
                    file_log = open(argv[i], 'a')
            except:
                print 'Cannot open the requested file for LOG: '.format(argv[i])
                print 'LOG will be disabled'
                file_log = None
        if (argv[i] == '-tl'):
            i += 1
            if i >= len(argv):
                print 'Error using option -tl: float required'
                break
            try:
                #Takes the second parameter as the float time limit
                time_limit = float(argv[i])
                if time_limit <= 0:
                    raise
            except:
                print 'Error using -tl option: the time limit will be set to default'
                time_limit = DEFAULT_TIME_LIMIT
        if (argv[i] == '-ps'):
            i += 1
            if i >= len(argv):
                print 'Error using option -ps: int required'
                break
            try:
                #Takes the second parameter as the float time limit
                population_size = int(argv[i])
                if population_size <= 4:
                    raise
            except:
                print 'Error using -ps option: population size will be set to default'
                population_size = DEFAULT_POPULATION_SIZE        
    
    main_handler(file_in, file_out, file_log, population_size, time_limit)
