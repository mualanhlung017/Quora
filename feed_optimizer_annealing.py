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
    cooling steps and mutation cycles for cooling step, resulting quicker than exhaustive start.   
'''
class AnnealingAlgorithm():
  
    ''' Start temperature'''
    __INITIAL_TEMPERATURE = 1
    
    ''' How many times do we cool'''
    __COOLING_STEPS = 20        #500
    
    ''' How much to cool each time'''
    __COOLING_FRACTION = 0.97    
    
    ''' Number of mutations cycles for each temperature cooling step - lower makes it faster, higher makes it potentially better. '''
    __STEPS_PER_TEMP = 50         #1000
    
    ''''Problem specific Boltzman's constant'''
    __K = 1e-5

    ''' Constructor
        @param full_stories_set
        @param page_height:    The limit for the 
    '''
    def __init__(self, full_stories_set, page_height):
        seed(time())
        self.__full_stories_set = sorted(full_stories_set, key=lambda s:float(s._score)/s._height, reverse=True)
        self.__N = len(self.__full_stories_set)
        self.__page_height = page_height
        
        return

    def __get_subset(self, mask):
        #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
        return [self.__full_stories_set[i] for i in range(len(mask)) if mask[i]]

    @staticmethod
    def get_total_steps():
        return AnnealingAlgorithm.__COOLING_STEPS * AnnealingAlgorithm.__STEPS_PER_TEMP
        
    def compareSolutions(self, solution_1,solution_22):
        #DEBUG
        if not (solution_1.valid and solution_22.valid):
            raise 
        
        #INVARIANT: all solutions tested are valid
        if solution_1.score >solution_22.score:
            return -1
        elif solution_1.score <solution_22.score:
            return 1
        else:
            if solution_1.size <solution_22.size:
                return -1
            elif solution_1.size >solution_22.size:
                return 1
            else:
                if solution_1.mask <=solution_22.mask:
                    return -1
                else:
                    return 1

    ''' Creates a solution at random
        Initialize the bit mask .
        The probability distribution over the space of the subsets is uniform.
        @return:    A Solution Object.
    '''
    def __initial_solution(self):
        mask = [0 for i in range(self.__N)]

        score = 0
        height = 0
        size = 0
        j = 0
        while (j < self.__N):   #Adds random stories until the limit would be crossed
            story = self.__full_stories_set[j]
            slack = self.__page_height - story._height
            if height <= slack:
                mask[j] = 1
                score += story._score
                height += story._height
                size += 1
                j += 1
            else:
                if slack == 0:
                    break
                else:
                    j += 1
                    continue

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
        point = randrange(self.__N)
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
        

    ''' First kind of mutation:         
        One flag, chosen at random, is flipped, so that one story previously
        included in the set won't be included anymore, or viceversa;
        @param solution:    The current solution of the annealing;
        @return:    The new solution obtained after the mutation           
    '''
    def __mutation_2(self, solution):
        
        mask = deepcopy(solution.mask)
        mask_1 = [i for i in range(self.__N) if mask[i] == 1]
        if len(mask_1) == 0:
            return solution
        
        point = mask_1[randrange(len(mask_1))]
        
        mask[point] = 0
        size = solution.size - 1
        score = solution.score - self.__full_stories_set[point]._score
        height = solution.height - self.__full_stories_set[point]._height
        point += 1
        
        while point < self.__N:   #Adds random stories until the limit would be crossed
            story = self.__full_stories_set[point]
            if mask[point]==1:
                point += 1
                continue
            
            slack = self.__page_height - story._height
            if height <= slack:
                mask[point] = 1
                score += story._score
                height += story._height
                size += 1
                point += 1
            else:
                if slack == 0:
                    break
                else:
                    point += 1
                    continue 
        return Solution(mask, size, 1, score, height)


    '''Simulated annealing main: until all the allotted time has been used, keeps restarting
       the annealing procedure and saves its result
       @param max_time: the maximum (indicative) execution time for the annealing, in seconds;
       @return: (best_score, best_solution)
               The best solution found by simulated annealing, and its _score.
    '''
    def start(self, max_time, file_log=None):
    
        ''' Checks that at least one story exists (otherwise the best
            solution is the empty set)
        '''
        if len(self.__full_stories_set) == 0:
            return 0, []
        
        start_time = time()
        
        temperature = AnnealingAlgorithm.__INITIAL_TEMPERATURE
    
        initial_solution = self.__initial_solution()
        best_solution = deepcopy(initial_solution)
        
        while True:
            
            for i in range(AnnealingAlgorithm.__COOLING_STEPS):
                solution = deepcopy(initial_solution)
                start_solution = deepcopy(solution)
                                
                temperature *= AnnealingAlgorithm.__COOLING_FRACTION
                
                for j in range( AnnealingAlgorithm.__STEPS_PER_TEMP ):
                    new_solution = self.__mutation_2(solution)
    
    
                    if self.compareSolutions(new_solution, solution) < 0 : # ACCEPT-WIN
                        solution = deepcopy(new_solution)
                        if self.compareSolutions(solution, best_solution) < 0:
                            best_solution = deepcopy(solution)
                            
                    else:
                        delta = float(solution.valid * solution.score - new_solution.valid * new_solution.score)
        
                        flip = random()
                        exponent = -delta * AnnealingAlgorithm.__K/temperature
                        merit = e ** exponent
        
    #                    print 'merit = ', merit
                        
                        if merit > flip :  #ACCEPT-LOSS
                            solution = deepcopy(new_solution)
        
                if  self.compareSolutions(start_solution, solution) < 0 : # rerun at the same temperature
                    temperature /= AnnealingAlgorithm.__COOLING_FRACTION
            

                #Continues until the execution exceeded the allotted time
                if time() >= start_time + max_time:
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
def main_handler(file_in, file_out, file_log, global_time_limit):
    start_time  = time()
    results_set = []
    stories_set = []
      
    events_set, time_window, page_height = read_input(file_in)

    #Counts the number of reloads in order to assign a time_limits for each
    #optimization that allows the execution to run within the global _time 
    #limit (4.5 seconds by default)
    runs = len([e for e in events_set if e[0]=='R'])
    if runs == 0:
        return
        #raise "No reload request in the input!"
    
    for event in events_set:
        if event[0] == 'S':
            #It's a story that must be added to DB
            stories_set.append(Story(event[1], event[2], event[3]))
        elif event[0] == 'R':
            #dynamically adjust the time limit for each step according to the remaining time 
            time_limit = float(global_time_limit - (time()-start_time)) / (AnnealingAlgorithm.get_total_steps() * runs)   

            min_time = event[1] - time_window
            recent_stories = [story for story in stories_set
                              if story._time >= min_time
                              and story._height <= page_height ]
            annealing = AnnealingAlgorithm(recent_stories, page_height)

            if file_log != None:
                file_log.write('Request at time {}\n'.format(event[1]))
            
            score, subset = annealing.start(time_limit, file_log)
            
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
    
    file_in = stdin
    file_out = stdout
    file_log = None
        
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
    
    main_handler(file_in, file_out, file_log, time_limit)
