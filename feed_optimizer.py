'''
@author: mlarocca
'''

from time import time
from random import random, randrange, seed
from math import copysign
import re
from sys import stdin, stdout, argv
from copy import deepcopy

from numpy import mean, std


''' Genetic Algorithm
    The class is designed on the Template Pattern: it implements just the sketch
    of a genetic algorithm, with a random initialization, and then a cycle, with
    a new __population created at each iteration from the __population at the previous
    one.
    This class specifies only the selection algorithm (round robin selection)
    and the elitism criteria; the details of chromosomes' structure, of the 
    crossover and of the mutations algorithms (including the number of different
    kinds of mutations), together with their ratio of application, are completely
    left to the specific class that models evolving individuals.
    
    Of course the Template pattern isn't fully applied in this case because the
    further generalization needed would make the implementation unnecessarily
    complicated and would also penalize the performance.
'''
class genetic_algorithm():
    

    
    ''' Constructor
        Sets up the parameters
        @param full_stories_set:    The set of all the stories in the DB whem the
                                    optimization starts;
        @param population_size:     The number of individuals to be included in the
                                    __population to evolve;
                                    WARNING: this value MUST be greater than or
                                             equal to 4 otherwise crossover would
                                             be meaningless (and selection would
                                             raise an exception anyway);
        @param page_height:    The limit for the sum of stories' heights;
        @param time_limit:    The maximum time that can be spent on optimizing;
                                WARNING:    the actual time spent will be slightly
                                            larger than this limit, because only
                                            when the limit is already crossed the
                                            main function will return;
    '''
    def __init__(self, full_stories_set, population_size, page_height, time_limit):
        self.__full_stories_set = full_stories_set
        self.__chromosome_length = len(full_stories_set)
        self.__population_size = population_size
        self.__time_limit = time_limit
        self.__page_height = page_height
        
      
    ''' Genetic Algorithm main
        Although it has been created specifically for this challenge, it sketches
        a general purpose genetic algorithm, needing just a few adjustments
        to be used for different problems.
        The application of the Template Design Pattern is limited in order to
        achieve clarity, readability and good performance.
        
        The algorithm goes through the following steps:
        1)    Generates randomly an initial population; The details of the
                generation of the single individual are left to the
                problem-specific class that models individual;
        2)    Repeats the following cycle, until the allotted time is over:
                2.a)    Let's the best element(s) of the previous generation
                        pass through to the next one unchenged (elitism);
                2.b)    Until the new population hasn't been fully generated:
                        2.b.1)    Randomly selects couple of elements from the old
                                    generation and let them reproduce (either by
                                    crossover or cloning);
                        2.b.2)    Applies mutation(s) to the couple of elements produced
                                    by the reproduction routine at the previous step;
                        2.b.3)    Adds each of the new elements to the new population,
                                    in the right position (the population is kept
                                    in reverse order with respect to the fitness -
                                    higher fitness means better elements);
                INVARIANT: after the iteration is completed, the first
                            element in the population, if it models a valid solution,
                            is also the best solution found so far.
        3)    Returns The solution modeled by the first element of the population
        
        @param file_log:    Optional parameter: the file to which write log info, like
                            intermediate results.
        @return:    (best_score, best_stories_subset)
                    A couple whose first element is the score of the best solution found,
                    and the second one is the solution itself, i.e. the highest score,
                    shortest and lexicographically smaller subset of the whole stories
                    universe.  
    '''  
    def start(self, file_log = None): 
        #Need to ensure randomization
        seed(time())

        
        self.__population = self.__init_population(self.__population_size, 
                                                   self.__chromosome_length)
        
        #DEBUG
        if file_log != None:
            it = 0
        
        start_time = time()     #Doen't count the initialization time, in order to have the main
                                #cycle executed at least once!
                    
        while time() - start_time < self.__time_limit:
            #Elitism: the best element always passes to the next generation
            new_population = [self.__population[0]]
            #If __population_size is even, then, since new elements are added in pairs,
            #to match the size extends elitism to the second best individual
            if not self.__population_size % 2:
                new_population.append(self.__population[1])
            M = len(new_population)
            while M < self.__population_size:
                #Select 2 individuals from the previous __population, and then have them reproduced to
                #the next one, either by crossover or cloning (see __reproduction function)
                (new_individual_1, 
                 new_individual_2) = self.__reproduction(
                                                self.__selection(self.__population, 
                                                             len(self.__population)))

                for individual in [new_individual_1, new_individual_2]:
                    #Applies the mutations according to the rates specified by the Individual's class itself
                    for mutation in individual.MUTATIONS:
                        self.__apply_mutation(mutation)
                    
                    #Tries to insert the new element in the existing __population
                    for i in range(M):
                        #Higher __fitness individuals have better rank
                        if self.__fitness(individual) > self.__fitness(new_population[i]):
                            new_population.insert(i, individual)
                            break
                    if i==M-1:
                        #Element must be added to the end of the list
                        new_population.append(individual)
                    M+=1
                
            self.__population = new_population  
            
            #DEBUG
            if file_log != None:
                it += 1
                fitnesses = map(lambda ind: self.__fitness(ind)[1], new_population)
                file_log.writelines('\tIteration # {} - Fitness: Best={}, mean={}, std={}\n'
                                    .format(it, self.__fitness(new_population[0]), 
                                           mean(fitnesses), std(fitnesses)))
        
        best_fitness = self.__fitness(self.__population[0])
        #fitness: (valid, score, 1/subset cardinality, lexicographic order)
        best_stories_subset = self.__population[0].get_subset(self.__full_stories_set)
        
        return best_fitness[1], best_stories_subset
      

    ''' Creates a population of the specified size of StorySubset individuals,
        where the subsets elements are drawn from a set of 'chromosome_length'
        stories.
        
        @param population_size:    The desired size for the population set;
        @param chromosome_length:    The length of each individual's chromosome
                                        (in the particular case, it's the size
                                        of the stories universe).
    '''    
    def __init_population(self, population_size, chromosome_length):
        new_population = []
        for i in range(population_size):
            new_population.append(StorySubset(chromosome_length))
        return new_population  
    
    ''' Shortcut to compute any individual's fitness
        @param individual:    The member of the __population whose fitness must be computed;
        @return:    The value of the individual's fitness.
    '''
    def __fitness(self, individual):
        return individual.computeFitness(self.__full_stories_set, self.__page_height)
    
    ''' Shortcut to perform "reproduction" on a couple of individuals;
        The crossover reproduction is applied with probability CROSSOVER_PROBABILITY,
        otherwise the individuals just clone themselves into the new generation;
        
        @param individual_1: The first element that is going to reproduct;
        @param individual_2: The second element that is going to reproduct;
    '''    
    def __reproduction(self, (individual_1, individual_2)):
        if random() < StorySubset.CROSSOVER_PROBABILITY:
            #Applies crossover (100*CROSSOVER_PROBABILITY)% of the times...
            (new_individual_1, new_individual_2) = individual_1.crossover(individual_2)
        else:
            #... otherwise the individuals are just copied to next generation
            (new_individual_1, new_individual_2) = (individual_1.copy(), individual_2.copy())

        return (new_individual_1, new_individual_2)
      
    ''' Shortcut to perform one of the kinds of mutations designed for the
        specific problem;
        
        @param mutation:    the function that actually perform the mutation;
        @param mutation_probability:    the probability that the mutation is actually
                                  applied.
    '''  
    def __apply_mutation(self, (mutation, mutation_probability)):
        if random() < mutation_probability:
            mutation()

    
    ''' Round robin selection;
        The how_many elements are chosen randomly from the __population;
        For each element returned, two candidates are taken randomly from a uniform
        distribution over the __population set, then with probability SELECT_BEST_PROBABILITY
        the best of the two is chosen, and with prob. 1.-SELECT_BEST_PROBABILITY the least
        fit one is chosen.
        The probability SELECT_BEST_PROBABILITY is left to the specific problem to choose;
        If SELECT_BEST_PROBABILITY == 0.5 each element is selected exactly with uniform
        probability, otherwise the mean is shifted towards one of the sides in
        proportion to the difference SELECT_BEST_PROBABILITY - 0.5, in the same way as
        the mean of the minimum between two uniform random numbers in [0,1] 
        becomes 1/3 and the mean of the maximum becomes 2/3;
        
        @param __population:    The __population from which to choose the individuals;
        @param size:    The size of the __population from which to choose;
                        NOTE:   size can be lower than len(__population), allowing
                                to use only a subset of the __population;
        @param how_many:    The number of elements to be selected;
        @return:    The list of elements chosen.
    '''
    def __selection(self, population, size, how_many = 2):
        #INVARIANT:    len(__population) >= size >= how_many * 2
        indices = [i for i in range(size)]
        chosen = []
        for i in range(how_many):
            #Chooses two individuals randomly
            first = indices[randrange(size)]
            indices.remove(first)   #Doesn't allow repetitions (Every index generated here must be different)
            size -= 1
            second = indices[randrange(size)]    
            indices.remove(second)   #Doesn't allow repetitions
            size -= 1
                       
            if random() < StorySubset.SELECT_BEST_PROBABILITY:
                #The one with better rank is chosen
                mul = 1
            else:
                #The one with worst rank is chosen
                mul = -1
            
            if (mul * population[first].computeFitness(self.__full_stories_set, self.__page_height) >
                mul * population[second].computeFitness(self.__full_stories_set, self.__page_height)):
                chosen.append(self.__population[first])
            else:
                chosen.append(self.__population[second])
 
        return chosen


#END of class genetic_algorithm


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
        @param score:    Score of the story;
        @param height:    Height needed to show the story.
    '''
    def __init__(self, time, score, height):
        self._time = time
        self.score = score
        self._height = height
        Story.__counter += 1
        self._id = Story.__counter
   
   
''' Class StorySubset
    A StorySubset Object models the solution to the problem (which is a subsest of
    __full_stories_set) in such a way that it can be used as the basis of the genetic algorithm
    sketched in the class genetic_algorithm, i.e. every Story Subset represents
    an individual in the __population evolved by the GA.
    
    Chromosomes are represented array of flags, with one flag for each story,
    such that a flag is True if the corresponding story is inserted in the feed,
    False otherwise.
'''
        
class StorySubset():
    
    ''' Constant:   alias for a value denoting a valid subsed (one that doesn't
                    violate any constraint). Since higher fitness denotes better
                    elements, this should be greather than the value for 
                    individuals violating the constraints, so that fitness
                    values will be easily comparable (see the description of
                    how the fitness value is computed below
    '''
    __VALID_SOLUTION = 1.
    ''' Constant:   alias for a value denoting an invalid subsed (one that
                    violate some constraint).'''
    __NOT_VALID_SOLUTION = 0.
    
    ''' The probability that during round robin selection it is chosen the best
        individual from the dueling couple .'''
    SELECT_BEST_PROBABILITY = .7
    ''' The probabilty that crossover is applied during individuals reproduction.'''
    CROSSOVER_PROBABILITY = .8;

    
    ''' Constructor: define a constant set containing reference to the mutation
        methods coupled with the probability with which they should be applied;
        The chromosome of the individual (i.e. a bit mask that defines the
        subset of stories included in the solution modeled by the individual
        itself) can either be passed as a parameter, or generated at random.
    ''' 
    def __init__(self, full_stories_set_size, chromosome=None):
        ''' Only one kind of mutation is applied, and it is stored together with
            its ratio of application for this problem'''
        self.MUTATIONS = [(self.__mutation1, 0.5)]
        
        if chromosome != None:
            self.__chromosome = deepcopy(chromosome)
        else:
            self.__chromosome = self.__random_init(full_stories_set_size)
            
        self.__changed = True
        
        

    ''' Initialize the element mask, which denotes the subset of the Universe
        of the Stories characterizing a single element.
        The probability distribution over the space of the subsets is uniform.
        @param N:    The size of the Universe
        @return:    A list of 0 and 1, representing a bit mask that denotes
                    a subset of the Universe (i.e. the set of all the Stories
                    in the DB).
    '''
    def __random_init(self, N):
        
        '''
            @return:    0 or 1 with probability 1 over 2.
        '''
        def random_bit():
            if random() < 0.5:
                return 1
            else:
                return 0
              
        return [random_bit() for i in range(N)]


    
    ''' @param full_stories_set:    The Universe, i.e. the set of all the stories
                                    in the DB.
        @return: The subset of stories included in the solution modeled by this individual. 
    '''
    def get_subset(self, full_stories_set):
        #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
        return [full_stories_set[i] for i in range(len(self.__chromosome)) if self.__chromosome[i]]


    ''' Shortcut for a deepcopy of the element.
        @return:    a deepcopy of the individual.
    '''
    def copy(self):
        copy_instance = deepcopy(self)
        return copy_instance


   
    ''' Computes the fitness associated with this subset of __full_stories_set
        The fitness returned is a tuple: 
            The first and most important element is 0 or 1 depending respectively on 
                if the total height of the __full_stories_set chosen is less than or equal the
                available space on the page;
            The second one is the total score of the inserted __full_stories_set for elements
                that do not violate the constrain on height, the score multiplied by
                the ratio between __page_height and total set height otherwise;
            The third element is the reciprocal of the number of __full_stories_set included,
                so that the fewer the __full_stories_set, the higher the rank;
            The fourth and last element of the tuple is a number computed from the
                lexicographic order of the __full_stories_set (with one-to-one lists-to-number
                correspondance).    
        This way the individuals that do not violate the constrains appears at the
        top of the ranking, and they follow the order imposed by the challenge
        specifications, so that at any moment the top element, if valid, is the best
        set of __full_stories_set found; among the individuals that do violate the constrains,
        furthermore, the fitness is higher for those with fewer __full_stories_set, i.e. those
        for which it is likely that removing one story will lead to a valid set.
        
        For performance optimization, if the individual hasn't changed since last time that
        fitness was computed, returns the value that has been stored back then, avoiding
        to recompute it.
        @param __full_stories_set: The complete set of all __full_stories_set
        
        @return:    The indidual's fitness, as the tuple described above.           
    '''           
    def computeFitness(self, full_stories_set, page_height):
        if self.__changed:
            #INVARIANT: len(__full_stories_set) == len(self.__chromosome):
            
            '''
                Transform a binary string into a decimal number.
                It is well known that there is a one-to-one correspondence
                between binary strings and subsets, and if a lexicographic
                order is imposed on the subsets considering earlier defined
                sets smaller, then the set of all possible binary strings
                (and the set of decimal number in which they are converted)
                also naturally reflect that order.
                WARNING:    the lexicographic order will be meaningful only
                            comparing strings of the same length.
                @param sequence:    A list of 1 and 0 (integers);
                @return:    An integer representing the conversion from base
                            2 to base 10 of the input.
            '''
            def sequence2nbr(sequence):
                M = len(sequence)
                tot = 0.
                for i in range(M):
                    tot += sequence[i] * 2 ** (M-1-i)
                return tot
                    
            used_stories = [full_stories_set[i] for i in range(len(self.__chromosome)) if self.__chromosome[i]]
            
            scores_sum = sum(map(lambda s: s.score, used_stories))
            total_height = sum(map(lambda s: s._height, used_stories))
            if total_height < page_height:
                self._fitness = (self.__VALID_SOLUTION, scores_sum, len(used_stories), sequence2nbr(self.__chromosome))
            else:
                self._fitness = (self.__NOT_VALID_SOLUTION, scores_sum, 1./len(used_stories), sequence2nbr(self.__chromosome))   
            self.__changed = False

        return self._fitness

    ''' Crossover    
        Single point Crossover is used for individuals reproduction: it is randomily
        chosen one point in the middle of the chromosome, and the 4 halves created
        by dividing the two individuals' genomes are mixed together to form
        2 new individuals.
        
        @param other:    The other subset that will be used for reproduction;
        @return:    A couple of brand new individuals.
    '''
    def crossover(self, other):
        N = len(self.__chromosome)
        if N<3:
            return self.copy(), other.copy()
        
        point = 1 + randrange(N-2)                  #Crossing point must be non-trivial
        new_mask_1 = self.__chromosome[:point] + other.__chromosome[point:]
        new_mask_2 = other.__chromosome[:point] + self.__chromosome[point:]
        return StorySubset(N, new_mask_1), StorySubset(N, new_mask_2)
    
    ''' Mutation1
        One flag, chosen at random, is flipped, so that one story previously
        included in the set won't be included anymore, or viceversa;
        
        WARNING: Mutation1 changes the modify the object it's called on!
    '''
    def __mutation1(self):
        point = randrange(len(self.__chromosome))
        self.__chromosome[point] = int( copysign(self.__chromosome[point]-1, 1) )
        self.__changed = True    
        


#END of class StorySubset



        
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
            GA = genetic_algorithm(recent_stories, population_size, page_height, time_limit)
            if file_log != None:
                file_log.write('Request at time {}\n'.format(event[1]))
            score, subset = GA.start(file_log)
            
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
