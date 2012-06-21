'''
@author: mlarocca
'''

from math import floor
import re
from sys import stdin, stdout, argv
#DEBUG    from time import time


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
    
    def __init__(self, mask, size, score, height, deecpy=False):
        if deecpy:
            self.mask = mask[:]
        else:
            self.mask = mask
        self.size = size
        self.score = score
        self.height = height
 
''' Simulated Annealing Algorithm class.
    Exposes a method that performs simulated annealing on a dictionary (passed upon instance construction) to find an optimal stepladder.
    The problem space has plenty of local minima, but the algorithm appears performant enough to reach the global minimum even with a few
    cooling steps and mutation cycles for cooling step, resulting quicker than exhaustive start.   
'''
class BackTrackingAlgorithm():
  
    ''' Constructor
        @param full_stories_set:    The set of all the stories available, ordered
                                    according to the ratio score/height of each story,
                                    from the largest to the smallest
        @param page_height:    The limit for the sum of the story heights (i.e.
                                the capacity of the Knapsack)
    '''
    def __init__(self, full_stories_set, page_height):
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

    ''' Performs, iteratively, the Horowitz-Sahni algorithms for 0-1 KP problem.
        INVARIANT: the elements to put in the knapsack must be ordered according
                    to the ratio value/cost, from the highest to the lowest.
        Tries to add as much elements to the set as possible according to their
        scaled value ("forward move") and then, when it funds a critical element 
        (i.e. one that cannot be added to the knapsack) estimates an upper bound
        (in particular Dantzig's upper bound) for the maximum value that is possible
        to get with the current elements included in the solution:
        if this bound is lower than the best score obtained so far, prunes the
        recursion and perform a backtracking move, looking for the closest '1'
        in the subset bit mask (if it exists), and removing the corresponding
        element from the knapsack.
        
        @param mask:    A bit mask that keeps track of the elements added to the
                        solution so far;
        @param size:    The number of elements added to the knapsack so far;
        @param score:   Total score for the current solution;
        @param height:    Total height for the curent solution;
        @param pos:    The index of the new element to examine;
    '''
    def __horowitz_sahni(self):
        mask = [0 for i in range(self.__N)]
        best_solution = Solution(mask, 0, 0 ,0, True)
        score = 0
        height = 0
        size = 0 
        
        j = 0
        while True:
            while j < self.__N:
                
                #Tries a forward move        
                pos = j
                
                initial_score = score
                initial_heigh = height
                initial_size = size
                
                while pos < self.__N:
                    story = self.__full_stories_set[pos]
                    
                    #First tries a forward move, if possible
                    if story._height > self.__page_height - height:
                        break
                    else:
                        size += 1
                        mask[pos] = 1
                        score += story._score
                        height += story._height
                        pos += 1

                if pos < self.__N:
                    #Estimates Dantzig's upper bound
                    story = self.__full_stories_set[pos]
                    upper_bound = score + floor(story._scaled_score * (self.__page_height - height))
                    
                    if best_solution.score > upper_bound or (
                        best_solution.score == upper_bound and
                         best_solution.size < size):
                        #The forward move would led us to a better solution,
                        #so it performs backtracking

                        #Brings the situation back at before the forward move
                        for k in range(j,pos):
                            mask[k] = 0
                        
                        score = initial_score 
                        height = initial_heigh
                        size = initial_size

                        #Looks for a possible backtracking move
                        pos = j - 1
                        while pos >= 0 and mask[pos] == 0:
                            pos -= 1
                        if pos < 0:
                            #No more backtracking possible
                            return best_solution
                        else:
                            #Exclude the element from the knapsack
                            mask[pos] = 0
                            size -= 1
                            story = self.__full_stories_set[pos]
                            score -= story._score
                            height -= story._height
                            j = pos + 1
                    else:
                        #The forward move was successful: discards the next element
                        #(which couldn't have been added because violates the
                        #knapsack capacity) and tries to perform more f. moves.
                        j = pos + 1
                else:
                    #Completed one "depth first search" visit in the solution 
                    #space tree: now must break off the while cycle
                    break
                    
            #INVARIANT: j == self.__N:
            #Completed one "depth first search" visit in the solution space tree.
            solution = Solution(mask, size, score, height)
            if self.compareSolutions(solution, best_solution) < 0:
                #Checks current solution
                best_solution = Solution(mask, size, score, height, True)

            #Tries a backtracking move
            pos = self.__N - 1
            while pos >= 0 and mask[pos] == 0:
                pos -= 1
            if pos < 0:
                #No more backtracking possible
                return best_solution
            else:
                #Exclude the element from the knapsack
                mask[pos] = 0
                size -= 1
                story = self.__full_stories_set[pos]
                score -= story._score
                height -= story._height
                j = pos + 1
        
        
                    
    ''' Shorthand: Performs the Horowitz-Sahni algorithms on the input, and
        then returns the best solution found.
    '''
    def start(self):
        #Tries trivial solutions first
        i = 0
        height = 0
        while i < self.__N and height <= self.__page_height:
            height += self.__full_stories_set[i]._height
            i += 1

        if i == self.__N and height <= self.__page_height:
            return sum(map(lambda s:s._score,self.__full_stories_set)),  sorted(self.__full_stories_set[:], key=lambda s: s._id )
        
        #No luck...
        best_solution = self.__horowitz_sahni()
        return best_solution.score, self.__get_subset(best_solution.mask)


        
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
                raise Exception("Bad formatted input!")

    return events, W, H

def read_and_process_input(file_in, file_out):
    line = file_in.readline()
        
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the specs above
    [N, W, H]  = regex.findall(line)
    
    N = int(N)
    W = int(W)
    H = int(H)

    stories_set = []


    #Reads the commands list
    regex_story = re.compile(STORY_RE)
    regex_reload = re.compile(RELOAD_RE)
    
    for i in range(N):
        line = file_in.readline()
        m_story = regex_story.match(line)
        if m_story != None:
            #INVARIANT: the input is assumed to be well formed
            #It's a story that must be added to DB
            story = Story(int(m_story.group(1)), int(m_story.group(2)), int(m_story.group(3)))
            
            i = 0
            while i < len(stories_set) and story._scaled_score < stories_set[i]._scaled_score:
                    i += 1
            stories_set.insert(i, story)

        else:
            m_reload = regex_reload.match(line)
            if m_reload != None:
                    #INVARIANT: the input is assumed to be well formed
                #Prunes the stories too old to be interesting (they won't be considered in the future) 
                #and the ones to large to fit on the page
                min_time = int(m_reload.group(1)) - W
                i = 0
                while i < len(stories_set):
                    if (stories_set[i]._time < min_time
                                  or stories_set[i]._height > H):
                        stories_set.pop(i)
                    else:
                        i += 1
                #stories_set = [story for story in stories_set
                #                  if story._time >= min_time
                #                  and story._height <= page_height ]
                
                backtrack = BackTrackingAlgorithm(stories_set, H)
    
                score, subset = backtrack.start()
                
                result_string = '{} {}'.format(score, len(subset))
                for story in subset:
                    result_string += ' {}'.format(story._id)
                
                file_out.write(result_string+'\n')

    file_in.close()
    file_out.close()

''' Main flow of the program.
    Reads the input from the input file (stdin by default), collects every command
    in a separate element of a list, and then executes them one by one.
    For every reload command, runs the Horowitz-Sahni backtracking algorithm.
    
    @param file_in:    The file from which to read the input;
    @param file_out:    The file on which the output should be written;
'''
def main_handler(file_in, file_out):
#DEBUG    start_time = time()

    results_set = []
    stories_set = []
      
    events_set, time_window, page_height = read_input(file_in)

#DEBUG    counter = 0
    for event in events_set:
#DEBUG        counter += 1
#DEBUG        if time()-start_time > 15:
#DEBUG            raise Exception('Execution is not in deadlock, just slow', 'Command {} out of {} '.format(counter, len(events_set)))
                
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
            i = 0
            while i < len(stories_set):
                if (stories_set[i]._time < min_time
                              or stories_set[i]._height > page_height):
                    stories_set.pop(i)
                else:
                    i += 1
            #stories_set = [story for story in stories_set
            #                  if story._time >= min_time
            #                  and story._height <= page_height ]
            
            backtrack = BackTrackingAlgorithm(stories_set, page_height)

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
    
    #main_handler(file_in, file_out)
    read_and_process_input(file_in, file_out)