'''
@author: mlarocca
Suppose we have T topics, Q questions, and N queries;
If the query is about a topic (t-type query), if we were to compute the distance of each topic's point from the query's center, and then sort the
topics based on this distance and take the first k (where k is the second parameter of the query), then it would require time
proportional to O(T + T*log T + k) = O(T*log T), since k<=T and provided we can compute the distance in constant time.
If, instead, we keep a list of the best k topics, and insert each topic we examine in this ordered list, each step is bounded by
O(log k + k) where O(log k) is needed to find the place to insert the new element and O(k) is a (large!) bound for the elements shift
needed to insert an element in the middle of a sorted array of size k; for each query it is then required time proportional to O(T*k);
If k<<T, being k constant, the total amount of time needed is O(T), while if k is close to T, the bound becomes O(T**2).
Since by definition of the problem k<=10, the bound becomes O(10*T) = O(T) < O(T*log T), so the latter solution is to prefer.

For q-type queries, the function to compute the distance requires to compute the distances of all the topics related to each question, 
and then take the min value for each question; for a question with Qn topic references then, supposing the distance can be computed in costant time O(c),
it is required time O(Qn*c) < O(max{Qn}*c) < O(10*c) by definition of the problem, so it is still required constant time to compute the
distance of a question from the query center and so the bound for each q-type query is analougus to the t-type query's ones.

Therefore, since we can expect Q<T (max{Q}=max{T}/10), a pessimistic bound for the whole proximity search algorithm is O(N*T)

'''
import re
from math import sqrt
from sys import stdin, argv

'''A list of element sorted upon insertion whose max size may be fixed at inizialization.
   The list is sorted in ascending order (see inner function compare_items)
   If n is the value fixed for its max size, then from the n+1 insertion the largest element will be removed from the list
   after a new element is interted
'''
class SortedList():
    
    '''Constructor
        @param metric: The metric defined to compute the distance of each element from a common minimum
        @param threshold: The minimum difference in the distance to consider one element to be further or closer to another with 
                            respect to the common minimum
        @param max_size: If specified, impose a positive maximum constraint on the maximum size of the list
    '''
    def __init__(self, metric, threshold, full_stories_set_size=0 ):
        self.metric = metric
        self.threshold  = threshold 
        self.items = []
        self.max_size = full_stories_set_size
        
    ''' - Add the item element to the list
        - Sort the list
        - Check if the number of elements in the list excedes max_size (if it is defined and positive), and in that case remove the largest element
        @param item:    The item that has to be appended to the list;
        
    '''
    def append(self, item) : 
        
        ''' Order elemnts by distance and then by id (greather ids are considered smaller)
        '''
        def compare_items((ia,da),(ib,db)):
            #checks the distances first: must be greater than the threshold (distances are non-negatives!)
            if da < db - self.threshold:
                return -1
            elif da > db + self.threshold:
                return 1
            else:
                #if the distances are within threshold, then compares ids
                return ib[0]-ia[0]
        #Add the item to the list, coupled with its distance, computed according to the metric passed upon construction
        i = 0
        item = (item, self.metric(item))
        while i < len(self.items) and compare_items(self.items[i], item) < 0:
            i += 1

        self.items.insert(i, item) 

        self.trim(self.max_size)        #If a max number of elements for the list is defined, it starts trimming the list, so that next insertions will be more efficient

  
    ''' If only n elements are allowed to stay in the list, removes the exceding ones
        @param n:    The number of elements allowed
    '''  
    def trim(self, n):
        
        if n> 0:
            for i in range(n, len(self.items)):
                self.items.pop()
            
    ''' Checks whether the list is empty
        @return:     True iff the list is empty
    '''        
    def is_empty(self) : 
        return (self.items == [])
    

    ''' Returns the items stored in this container; Since every entry is contains an item and its distance attribute coupled together,
        items must be decoupled first;
        @return:    A list composed of every item in the list
    '''   
    def get_items(self):
        return [it for (it,d) in self.items ]


INTEGER_RE = "(\d+)"            #Matches any non negative integer
DOUBLE_RE = "(\d+\.\d*)"        #INVARIANT: x,y positive => reg exp supporting negative floating points "([-]?\d+\.\d*)" not needed
SEPARATOR = ' '                 #We consider just spaces as separators
#Regular expression for a topic
TOPIC_REGEXP = INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE
#Regular expression for a query
QUERY_REGEXP = '([a-zA-Z]{1})' + SEPARATOR +  INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE
    
'''Constraints - grouped in one dictionary for sake of clarity'''
CONSTRAINTS = {'T_limit': 10000, 'Q_limit':1000, 'N_limit':10000, 'Qn_limit':10, 'Coordinate_limits':{'min':0, 'max':10e6} }    

'''
   Checks if the constraints are met
   All checking is grouped in one function to be executed at the end of the reading procedure so that constraint checking can be disabled
   easily, and program can run faster, if the input is guaranteed to be well-formed.
   @param T:    The number of topics, as it's read from the input
   @param Q:    The number of questions, as it's read from the input
   @param N:    The number of queries, as it's read from the input
   @param topics:    The list of topics, as it's read from the input
   @param questions:    The list of questions, as it's read from the input
   @param queries:    The list of queries, as it's read from the input
   @return:     True iff all the constraints are met
'''
def check_constraints(T,Q,N, topics, questions, queries):
    if T < 1 or T > CONSTRAINTS['T_limit']:     # NOT NEEDED: len(topics)!=T  would raise an exception while reading input
        return False
    if Q < 1 or Q > CONSTRAINTS['Q_limit']:      # NOT NEEDED: len(questions)!=Q  would raise an exception while reading input
        return False
    if N < 1 or N > CONSTRAINTS['N_limit']:      # NOT NEEDED: len(queries)!=N  would raise an exception while reading input
        return False
    
    #Checks the point in the list of topics
    for (t_id,x,y) in topics:
        if (x<CONSTRAINTS['Coordinate_limits']['min'] or x > CONSTRAINTS['Coordinate_limits']['max'] or 
            y<CONSTRAINTS['Coordinate_limits']['min'] or y > CONSTRAINTS['Coordinate_limits']['max']):
                return False

    #Checks that the topic id references in the questions list entries are all valid
    for (q_id,t_list) in questions:
        for t_id in t_list:
            if not t_id in topics:
                return False
            
    #Checks the point in the list of queries
    for (q_type,n_ref,x,y) in queries:
        if (x<CONSTRAINTS['Coordinate_limits']['min'] or x > CONSTRAINTS['Coordinate_limits']['max'] or
            y<CONSTRAINTS['Coordinate_limits']['min'] or y > CONSTRAINTS['Coordinate_limits']['max']):
                return False

    return True
    
'''Reads the input from a file f
   The input is assumed to be formatted as follows:
   First line: 3 integers T  Q  N
   T lines composed by an integer and 2 doubles
   Q lines composed by 2 integers q_id Qn and then another Qn integers
   N lines composed by 1 char, 1 int and 2 doubles
   @param f:    The file from which the input should be read;
   @return: (topics, questions, queries)
           Three lists containing the topics, questions and queries read from the input channel.
'''
def read_input(f):
    line = f.readline()
        
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the specs above
    [T,Q,N]  = regex.findall(line)
    
    T = int(T)
    Q = int(Q)
    N = int(N)

    topics = {}
    questions = []
    queries = []

    #Reads the topics list
    regex = re.compile(TOPIC_REGEXP)
    for i in range(T):
        line = f.readline()
        m = regex.match(line)
        t_id = int(m.group(1))
        (x,y) = map(lambda s: float(s), m.group(2,3))
        topics[t_id] = ((t_id, x, y))
   
    #Reads the questions list
    regex = re.compile(INTEGER_RE)
    for i in range(Q):
        line = f.readline()
        m = regex.findall(line)
        
        q_id = int(m[0])
        Qn = int(m[1])
        if (Qn!=0):
            Qids = map(lambda s: int(s), m[2:Qn+2])        #could have been [2:len(m)], but it is better to trigger an exception if the input is not well formed
            questions.append((q_id, Qids))
    
    #Reads the queries list            
    regex = re.compile(QUERY_REGEXP)
    for i in range(N):
        line = f.readline()
        m = regex.match(line)
        q_type = m.group(1)
        n_res = int(m.group(2))
        (x,y) = map(lambda s: float(s), m.group(3,4))
        queries.append((q_type, n_res, x, y))
    
    #Checks that contraints are met - disabled when input is trusted to be well-formed (for example if it has already been checked before passing it over)
    #NOTE: decomment if the input might not be well-formed
    #if not check_constraints(T,Q,N, topics, questions, queries) :       #DEBUG
    #    raise Exception("Malformed input")                                         #DEBUG
  
    return (topics, questions, queries)   

''' Given a center point, creates a metric function that returns the euclidean distance of a generic point to this center
    @param (x0,y0):    The cartesian coordinates of the center;
    @return: metric
            A function that takes a topic entry and returns its distance from the center
'''
def define_topic_metric((x0,y0)):
    '''Computes the distance of a "topic" element from (x0,y0)
       The first element in the tuple is needed because of the structure of the records used in SortedList class.
       @param (t_id, x,y):   The topic whose metric has to be computed; Passing this tuple instead of just the topics coordinates
                            allows reusability of the same functions in the SortedList class both for topics and questions;
       @return:     The euclidean distance in R^2 between the designated center and the topic.
       '''
    def metric((t_id, x,y)):
        return sqrt((x-x0)**2 + (y-y0)**2)                                     
    
    return metric

''' Given a center point and a list of topics, creates a metric function that returns 
    minimum euclidean distance to this center of the points associated with a subset of those topics
    @param (x0,y0):    The cartesian coordinates of the center;
    @return: metric
            A function that takes a question entry and returns its distance from the center   
'''
def define_question_metric((x0,y0), topics):
    #reuses the metrics defined for topics
    topic_metric = define_topic_metric((x0,y0))
    
    '''Computes the distance of a "question" element from (x0,y0)
       The first element in the tuple is needed because of the structure of the records used in SortedList class.
       @param (q_id, relevant_topics):   The question whose metric has to be computed, composed of its id and the list of topics
                                        relevant to the question: the final value is the minimum distance from the designated center
                                        of any topic relevant for this question.
       @return:     The euclidean distance in R^2 between the designated center and the question.       
    '''
    def metric( (q_id, relevant_topics) ):
        try:
            dists = [topic_metric(topic) for topic in [ topics[t_id] for t_id in relevant_topics ]]
        except:
            dists = [topic_metric(topic) for topic in [ topics[t_id] for t_id in relevant_topics if t_id < len(topics)]]
                
            #    for t_id in relevant_topics:
            #        print t_id, ' -> ' , topics[t_id]
            #except:
            #    raise Exception('failed on {} Topics #:  {}' .format( t_id, len(topics)) )
        if len(dists) > 0:
            return min(dists)
        else:
            return 1e20
    
    return metric

''' Takes the input data and, for each query, finds the requested number of elements.
    @param topics:    List of all the topics in the input;
    @param questions:    List of all the questions in the input;
    @param queries:    List of all the queries in the input;
    @return:     A properly formatted string, containing for each query the list of relevant topics' id sorted by ascending distance and descending topic id
'''
def process_queries(topics, questions, queries):  
    s = '' 
    for (q_type, n_res, x, y) in queries:
            if q_type.lower()=='t':
                metric = define_topic_metric((x,y))                   #Distance to the query point of interest
                queue = SortedList(metric, 0.001, n_res)            #keeps just n_res elements in the list
                for t in topics:
                    queue.append(topics[t])
                
                for it in queue.get_items():
                    s += str(it[0]) + ' '    
                s +='\n'
            elif q_type.lower()=='q':
                metric = define_question_metric((x,y), topics)                    #Distance to the query point of interest
                queue = SortedList(metric, 0.001, n_res)                        #keeps just n_res elements in the list
                for q in questions:
                    queue.append(q)
                
                for it in queue.get_items():
                    s += str(it[0]) + ' '    
                s +='\n'
            else:
                pass
                #DEBUG#raise exception    #It is assumed that the input is well formatted: otherwise, this line could be uncommented to check
    return s


''' Main.
    Reads the input from stdin (DEFAULT) or a file and output the results on stdout.
    Usage:
        -f filename     Specifies a file from where the input should be read. If the option is not used or misused or the requested file
                        doesn't exist, the input is read from stdin.
'''
if __name__ == '__main__':
    
    if (len(argv) > 2 and argv[1] == '-f'):
        try:
            filein = open(argv[2],'r')
        except:
            print 'The requested file: {} does not exist. Please insert your input from the terminal.'.format( argv[2])
            filein = stdin
    else:
        filein = stdin
    
    #DEBUG: De-comment the following lines if the input needs to be checked (please leave commented if the input may not be ill-formatted)
    #try:
    #    (topics,questions, queries) = read_input(filein)
    #except:
    #    print 'Malformed input'
    #    return
    
    (topics,questions, queries) = read_input(filein)
    if filein!=stdin:
        filein.close()

    print process_queries(topics,questions, queries)