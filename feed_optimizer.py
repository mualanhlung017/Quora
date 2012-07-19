'''
@author: mlarocca
'''

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
        

''' Returns the list of the ids of the stories corresponding to ones in the mask; 
    @param mask: A binary mask corresponding to a subset of the stories:
    @return: The corresponding list of ids.
'''
def get_subset_ids(stories_set, mask, n):
    return [stories_set[i]._id for i in xrange(n) if mask[i]]


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
def compareSolutions(stories_set,
                       solution_1_score, solution_1_size, solution_1_mask,
                       solution_2_score, solution_2_size, solution_2_mask):
    
    #INVARIANT: all solutions tested are valid
    if solution_1_score > solution_2_score:
        return -1
    elif solution_1_score < solution_2_score:
        return 1
    else:
        if solution_1_size < solution_2_size:
            return -1
        elif solution_1_size > solution_2_size:
            return 1
        else:
            n = len(solution_1_mask)
            stories_ids_1 = sorted(get_subset_ids(stories_set, solution_1_mask, n))
            stories_ids_2 = sorted(get_subset_ids(stories_set, solution_2_mask, n))
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
def horowitz_sahni(stories_set, N, c, best_solution_mask, best_solution_size, best_solution_score, best_solution_height):
    
    if N == 0:
        return 0, 0, []

    

#    critical_height = stories_set[0]._height
#    critical_score = stories_set[0]._score
#    s = 1
#    while  s < N  and critical_height <= c:
#        critical_height += stories_set[s]._height
#        critical_score += stories_set[s]._score
#        s += 1
#    s -= 1
    
#    if s == N:
#        return critical_score, critical_height, [1] * N
#    elif s == N - 1:
#        scaled_score = 0
#    else:
#        scaled_score = stories_set[s+1]._scaled_score        
 
#    story = stories_set[s]
#    c_bar = critical_height - story._height
#    critical_score - story._score   
    
#    sigma_0 = 0
#    sigma_1 = 0
    
#    sigma_0_height = 0
#    sigma_0_score = 0
#    sigma_1_height = story._height
#    sigma_1_score = story._score
    
#    while sigma_0 < N:
#        if sigma_1_height <= c:
#            story = stories_set[sigma_1]
#            sigma_1 += 1
#            sigma_0 = sigma_1
#            sigma_1_height += story._height
#            if sigma_0 != s:
#                sigma_0_height += story._height
#                sigma_0_score += story._score
#            
#        elif sigma_0_height < c:
#            if sigma_0 != s:
#                story = stories_set[sigma_1]
#                sigma_0_height += story._height
#                sigma_0_score += story._score
#            sigma_0 += 1
#        else:
#            break
#    if sigma_1 < N:
#        story_1 = stories_set[sigma_1]
#        sigma_1_height -= story_1._height
#        sigma_1_score -= story_1._score
    
#        U_bar_1 = sigma_1_score + (c-sigma_1_height) * story_1._scaled_score
#    else:
#        U_bar_1 = sigma_1_score
        
#    if sigma_0 < N:
#        story_0 = stories_set[sigma_0]
#        sigma_0_height -= story_0._height
#        sigma_0_score -= story_0._score
#        U_bar_0 = sigma_0_score + (c-sigma_0_height) * story_0._scaled_score
#    else:
#        U_bar_0 = sigma_0_score
    
#    U = max(U_bar_0, U_bar_1)
#    U = critical_score + max((int)(c_bar * scaled_score ),
#                             (int)(story._score - (story._height - c_bar) * stories_set[s-1]._scaled_score))
 
        
    mask = [0] * N
    
    score = 0
    height = 0
    size = 0
    
    j = 0
    while True:
        while j < N:
            
            #Tries a forward move        
            pos = j
            
            initial_score = score
            initial_heigh = height
            initial_size = size
            
            while pos < N:
                story = stories_set[pos]
                
                #First tries a forward move, if possible
                if story._height > c - height:
                    break
                else:
                    size += 1
                    mask[pos] = 1
                    score += story._score
                    height += story._height
                    pos += 1

            try:
                #Estimates Dantzig's upper bound
                story = stories_set[pos]
            except IndexError:
                #Completed one "depth first search" visit in the solution 
                #space tree: now must break off the while cycle
                break

            upper_bound = score + (int)(story._scaled_score * (c - height))
            
            if best_solution_score > upper_bound or (
                best_solution_score == upper_bound and
                 best_solution_size <= size):
                #The forward move would not led us to a better solution,
                #so it performs backtracking

                #Brings the situation back at before the forward move
                #k = j
                #while k < pos:
                for k in xrange(j,N):
                    mask[k] = 0
                    #k += 1
                
                score = initial_score 
                height = initial_heigh
                size = initial_size

                #Looks for a possible backtracking move
                pos = j - 1
                while True:
                    try:
                        while mask[pos] == 0:
                            pos -= 1
                    except IndexError:
                        #if pos < 0:
                        #No more backtracking possible
                        return best_solution_score, best_solution_height, best_solution_mask
                    else:
                        #Exclude the element from the knapsack
                        mask[pos] = 0
                        size -= 1
                        story = stories_set[pos]
                        score -= story._score
                        height -= story._height
                        j = pos + 1

                        #i = j
                        bound_height = height
                        score_bound = 0
                        #while i < N:
                        for i in xrange(j, N):
                            story = stories_set[i]
                            if story._height > c - bound_height:
                                break
                            
                            score_bound += story._score
                            bound_height += story._height
                            #i += 1
                        
                        try:
                            story = stories_set[i]
                            score_bound += (int)(story._scaled_score * (c - bound_height))
                        except IndexError:
                            pass
                            
                        upper_bound = score + score_bound
                        
                        if best_solution_score <= upper_bound:
                            break               
            else:
                #The forward move was successful: discards the next element
                #(which couldn't have been added because violates the
                #knapsack capacity) and tries to perform more f. moves.
                j = pos + 1
            #else IndexError:
                #Completed one "depth first search" visit in the solution 
                #space tree: now must break off the while cycle
            #    break
                
        #INVARIANT: j == self.__N:
        #Completed one "depth first search" visit in the solution space tree.
        if compareSolutions(stories_set,
                            score, size, mask,
                            best_solution_score, best_solution_size, best_solution_mask
                            ) < 0:
            #Checks current solution
            best_solution_mask = mask[:]
            best_solution_size = size
            best_solution_height = height
            best_solution_score = score
            
            if best_solution_size == N: #best_solution_score == U or 
                return best_solution_score, best_solution_height, best_solution_mask
        
        try:   
            story = stories_set[N-1] 
            if mask[N-1] == 1:
                mask[N-1] = 0
                size -= 1               
                score -= story._score
                height -= story._height 
            
        except IndexError:
            pass
        
        #Tries a backtracking move
        pos = N - 2
        while True:
            try:
                while mask[pos] == 0:       #pos >= 0 and 
                    pos -= 1
            except IndexError:
                #if pos < 0:
                #No more backtracking possible
                return best_solution_score, best_solution_height, best_solution_mask
            else:
                #Exclude the element from the knapsack
                mask[pos] = 0
                size -= 1
                story = stories_set[pos]
                score -= story._score
                height -= story._height
                #score_bound -= story._score
                j = pos + 1
                
                #i = j
                bound_height = height
                score_bound = 0
                #while i < N:
                for i in xrange(j, N):
                    story = stories_set[i]
                    if story._height > c - bound_height:
                        break
                    
                    score_bound += story._score
                    bound_height += story._height
                    #i += 1
                
                try: #if i < N:
                    story = stories_set[i]
                    score_bound += (int)(story._scaled_score * (c - bound_height))
                except IndexError:
                    pass
                    
                upper_bound = score + score_bound
                
                if best_solution_score <= upper_bound:
                    break
          
        
'''REGULAR EXPRESSIONS'''

'''Regular Expression: Matches any non negative integer'''
INTEGER_RE = '(\d+)'
'''Regular Expression: Matches a space character (the only separator admitted)'''
SEPARATOR_RE = ' '                 #We consider just spaces as separators
'''Regular Expression: Matches a "story"-type line of input'''
STORY_RE = 'S' + (SEPARATOR_RE + INTEGER_RE)*3
'''Regular Expression: Matches a "reload" type line of input'''
RELOAD_RE = 'R' + SEPARATOR_RE + INTEGER_RE


'''Reads the input from a file f
   The input is assumed to be formatted as follows:
   First line: 3 integers N  W  H
   N lines representing events, and so composed by 1 char (the event type) followed by either 1 or 3 integers
   @param f:    The file from which the input should be read;
   @return: 
               events:    The list of events.
               W:    The _time window to use to distinguish recent stories from too old ones
               H:    The page _height, in pixel
'''
def read_input(f):
    import re

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
    
    for cycle in xrange(N):

        line = f.readline()
        m_story = regex_story.match(line)
        
        try:        #if m_story != None:
            events.append(('S', int(m_story.group(1)), int(m_story.group(2)), int(m_story.group(3))))
        
        except:     #else:
            m_reload = regex_reload.match(line)
            #if m_reload != None:
            events.append(('R', int(m_reload.group(1))))
    return events, W, H

''' Main flow of the program.
    Reads the input from the input file (stdin by default), collects every command
    in a separate element of a list, and then executes them one by one.
    For every reload command, runs the Horowitz-Sahni backtracking algorithm.
'''
def main_handler(file_in):
    
    #Reads the events in advance in order to plan the best actions
    events_set, W, H = read_input(file_in)

    stories_set = []
    story_insert = stories_set.insert   #optimization
    story_pop = stories_set.pop         #optimization
    
    best_solution_score = 0
    best_solution_height = 0
    best_subset = []
    best_solution_mask = []
    best_solution_size = 0

    recompute = False

    N = len(events_set)
    for event_index in xrange(N):
        event = events_set[event_index]
        
        if event[0] == 'S':
            #It's a story that must be added to DB
            new_story = Story(event[1], event[2], event[3])
            
            if new_story._height <= H:
                # If the new story can be added without crossing the limit, then it belongs to the best solution

                if not recompute:

                    if best_solution_height + new_story._height <= H:
                        i = len(stories_set) - 1
                        try:
                            while new_story._scaled_score > stories_set[i]._scaled_score:
                                    i -= 1
                        except:
                            pass
                        i += 1
                        story_insert(i, new_story)
                                            
                        best_solution_mask.insert(i, 1)
                        best_subset.append(new_story._id)
                        best_solution_size += 1
                        best_solution_score += new_story._score 
                        best_solution_height += new_story._height                       
                    elif event_index < N-1 and events_set[event_index + 1][0] == 'R':        
                        #If at least another story is going to be added before the reload,
                        #then it is not worth it
                        stories_set_size = len(stories_set)

                        #horowitz_sahni

                        (tmp_solution_score, 
                         tmp_solution_height, 
                         tmp_solution_mask) = horowitz_sahni(stories_set, stories_set_size, H - new_story._height, 
                                                        best_solution_mask, 
                                                        best_solution_size, 
                                                        best_solution_score - new_story._score - 1, 
                                                        best_solution_height)
                        
             
                                                         
                        tmp_solution_score += new_story._score
                        
                        if tmp_solution_score < best_solution_score:
                            new_story_bitmask = 0 
                        elif tmp_solution_score > best_solution_score:
                            if (tmp_solution_mask != best_solution_mask):
                                best_subset = sorted(get_subset_ids(stories_set, tmp_solution_mask, stories_set_size))
                                best_solution_mask = tmp_solution_mask
                                
                            best_subset.append(new_story._id)
                            best_solution_score = tmp_solution_score
                            best_solution_height = tmp_solution_height + new_story._height
                            best_solution_size = len(best_subset)
                            
                            new_story_bitmask = 1                            
                        else:
                            if (tmp_solution_mask != best_solution_mask):
                                tmp_subset = sorted(get_subset_ids(stories_set, tmp_solution_mask, stories_set_size))
                            else:
                                tmp_subset = best_subset[:]
                                
                            tmp_subset.append(new_story._id)
                            tmp_solution_size = len(tmp_subset)

                            if tmp_solution_size < best_solution_size:
                                best_subset = tmp_subset
                                best_solution_score = tmp_solution_score
                                best_solution_height = tmp_solution_height + new_story._height
                                best_solution_mask = tmp_solution_mask
                                best_solution_size = tmp_solution_size
                                new_story_bitmask = 1
                            elif tmp_solution_size == best_solution_size and tmp_subset < best_subset:
                                best_subset = tmp_subset
                                best_solution_score = tmp_solution_score
                                best_solution_height = tmp_solution_height + new_story._height
                                best_solution_mask = tmp_solution_mask
                                best_solution_size = tmp_solution_size
                                new_story_bitmask = 1
                            else:
                                new_story_bitmask = 0   
                                

                              
                        new_story_index = stories_set_size - 1
                       
                        try:
                            while new_story._scaled_score > stories_set[new_story_index]._scaled_score:
                                new_story_index -= 1
                        except:
                            pass
                        
                        new_story_index += 1
                        story_insert(new_story_index, new_story)  
                       
                        best_solution_mask.insert(new_story_index, new_story_bitmask)
                    else:
                        recompute = True
                        i = len(stories_set) - 1
                        try:
                            while new_story._scaled_score > stories_set[i]._scaled_score:
                                    i -= 1
                        except IndexError:
                            pass
                        
                        i += 1
                        story_insert(i, new_story)
                        
                        if best_solution_height + new_story._height <= H:
                            best_solution_mask.insert(i, 1)
                            best_subset.append(new_story._id)
                            best_solution_size += 1                               
                            best_solution_score += new_story._score 
                            best_solution_height += new_story._height
                        else:
                            best_solution_mask.insert(i, 0)
                   
                else:
                    i = len(stories_set) - 1
                    try:
                        while new_story._scaled_score > stories_set[i]._scaled_score:
                                i -= 1
                    except IndexError:
                        pass
                    
                    i += 1
                    story_insert(i, new_story)
                    
                    if best_solution_height + new_story._height <= H:
                        best_solution_mask.insert(i, 1)
                        best_subset.append(new_story._id)
                        best_solution_size += 1                               
                        best_solution_score += new_story._score 
                        best_solution_height += new_story._height
                    else:
                        best_solution_mask.insert(i, 0)
                        
        elif event[0] == 'R':
            current_time = event[1] 
            min_time = current_time - W
             
            i  = len(stories_set) - 1
            while i >= 0:
                story = stories_set[i]
                if (story._time < min_time):
                    if best_solution_mask[i]:
                        
                        #If the story that became too old didn't belong to the best solution, then nothing changes
                        #Otherwise the old solution is no longer valid
                        best_solution_height -= story._height
                        best_solution_score -= story._score
                        best_solution_size -= 1
                        recompute = True
                    best_solution_mask.pop(i)
                    
                    story_pop(i)
                i -= 1
            
            if recompute:
                stories_set_size = len(stories_set)
                
                (best_solution_score, 
                 best_solution_height, 
                 best_solution_mask) = horowitz_sahni(stories_set, stories_set_size, H, 
                                                      best_solution_mask, 
                                                      best_solution_size, 
                                                      best_solution_score, 
                                                      best_solution_height)


                best_subset = sorted(get_subset_ids(stories_set, best_solution_mask, stories_set_size))
                best_solution_size = len(best_subset)
                
                recompute = False

            
            print '{} {}'.format(best_solution_score, best_solution_size), ' '.join(map(str, best_subset))
                    
            #file_out.write('{} {} '.format(best_solution_score, best_solution_size))
            #file_out.write(' '.join(map(str, best_subset)))
            #file_out.write('\n')
            #file_out.flush()



#file_out = open('f_test.txt','w')
#DEBUG
from time import time
if __name__ == '__main__':
    from sys import stdin, setcheckinterval
    
    setcheckinterval(100000000)
    file_in = stdin

#DEBUG    
    profiler = False
    if not profiler:
        file_in = open('feed_test_2.txt','r')
        file_out = open('f_test.txt','w')
    #DEBUG
        start_time = time()
        #read_and_process_input(file_in)
        main_handler(file_in)
        print time() - start_time
   
    else:
            
        file_in = open('feed_test_2.txt','r')
        file_out = open('f_test.txt','w')

        
        import profile
        pr = profile.Profile()
        for i in range(5):
            print pr.calibrate(10000)
        profile.run('main_handler(file_in)', 'feed_profile.txt')    