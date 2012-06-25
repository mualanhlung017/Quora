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
#from math import sqrt
from sys import stdin

INTEGER_RE = "(\d+)"            #Matches any non negative integer
DOUBLE_RE = "(\d+\.\d*)"        #INVARIANT: x,y positive => reg exp supporting negative floating points "([-]?\d+\.\d*)" not needed
SEPARATOR = ' '                 #We consider just spaces as separators
#Regular expression for a topic
TOPIC_REGEXP = INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + '*'
#Regular expression for a query
QUERY_REGEXP = '([a-zA-Z]{1})' + SEPARATOR +  INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + '*'
    
'''Constraints - grouped in one dictionary for sake of clarity'''
CONSTRAINTS = {'T_limit': 10000, 'Q_limit':1000, 'N_limit':10000, 'Qn_limit':10, 'Coordinate_limits':{'min':0, 'max':10e6} }    

   
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
def read_and_process_input(f):
    line = f.readline()
        
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the specs above
    [T,Q,N]  = regex.findall(line)
    
    T = int(T)
    Q = int(Q)
    N = int(N)

    topics = {}
    questions = []

    #Reads the topics list
    regex = re.compile(TOPIC_REGEXP)
    for i in range(T):
        line = f.readline()
        m = regex.match(line)
        t_id = int(m.group(1))
        (x,y) = map(lambda s: float(s), m.group(2,3))
        topics[t_id] = (x, y)
   
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
        (x0,y0) = map(lambda s: float(s), m.group(3,4))
        

        def compare_items((ia,da), (ib,db)):
            #checks the distances first: must be greater than the threshold (distances are non-negatives!)
            if da < db - 0.001:
                return -1
            elif da > db + 0.001:
                return 1
            else:
                #if the distances are within threshold, then compares ids
                return ib-ia
        
        if q_type.lower()=='t':
            queue = []
                                  
           
            append = queue.append   #Optimization
            for t_id, (x,y) in topics.iteritems():
                append((t_id, (x-x0)**2 + (y-y0)**2))
                
            queue = [it for (it,d) in sorted(queue, cmp=compare_items)][:n_res]
            
            s = []
            for it in queue:
                s .append( '{} '.format(it) )    
            s = ''.join(s)          #Optimization
            print s
        elif q_type.lower()=='q':
            queue = []
            
            append = queue.append   #Optimization                

            for (q_id, Qn) in questions:
                dist = 1e13      #x,y <= 10**6 => dist**2 <= 2 * 10**12
                for t_id in Qn:
                    (x, y) = topics[t_id]
                    dist = min(dist, (x-x0)**2 + (y-y0)**2)        
            
                append((q_id, dist))
                
            queue = [it for (it,d) in sorted(queue, cmp=compare_items)][:n_res]
            
            s = []
            for it in queue:
                s .append( '{} '.format(it) )    
            s = ''.join(s)          #Optimization
            print s

    return  
    




''' Main.
    Reads the input from stdin (DEFAULT) or a file and output the results on stdout.
    Usage:
        -f filename     Specifies a file from where the input should be read. If the option is not used or misused or the requested file
                        doesn't exist, the input is read from stdin.
'''
if __name__ == '__main__':
    read_and_process_input(stdin)
