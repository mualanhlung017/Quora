import re
#from math import sqrt
from sys import stdin
from array import array
from math import sqrt

INTEGER_RE = "(\d+)"            #Matches any non negative integer
DOUBLE_RE = "(\d+\.\d*)"        #INVARIANT: x,y positive => reg exp supporting negative floating points "([-]?\d+\.\d*)" not needed
SEPARATOR = ' '                 #We consider just spaces as separators
#Regular expression for a topic
TOPIC_REGEXP = INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + '*'
#Regular expression for a query
QUERY_REGEXP = '([a-zA-Z]{1})' + SEPARATOR +  INTEGER_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + DOUBLE_RE + SEPARATOR + '*'

#DEBUG
#file_out = open('nearby_results.txt', 'w')
#file_log = open('nearby_debug.txt', 'w')
   
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

    #Maximum number of points or children for each topic
    max_elements_per_cluster = 16
    split_size = max_elements_per_cluster / 2


    ''' Creates the empty root of an SS-tree.
        @return:     The newly created tree root.
    '''
    def ss_make_tree():
        tree = {'points': [], 'leaf':True, 'parent': None, 'x':0., 'y':0.}
        return tree
    
    
    ''' Inserts a point (topic) in a SS-tree; If necessary, splits the tree node in which the point was inserted
        and fixes the tree structure from that node up to the root.
        
        @param new_point:   The point to be inserted;
                            The point must be a dictionary with three fields:
                            -    'x':    Point's x coordinate;
                            -    'y':    Point's y coordinate;
                            -    't_id':    The topic's ID.
        @param tree:    The root of the tree in which the point is going to be inserted;
        @return tree:    The root of the tree, possibly a new one if the old root has been split.
    '''
    def ss_tree_insert(new_point, tree):
        x_new_point = new_point['x']
        y_new_point = new_point['y']
        
        #Looks for the right leaf (the one with the closest centroid) to which the new_point should be added.
        #INVARIANT:    The empty tree's root is a (empty) leaf.
        node = tree
        while not node['leaf']:
            children = node['children']
            child = children[0]
            min_dist = (child['x'] - x_new_point) ** 2 + (child['y'] - y_new_point) ** 2
            min_index = 0
            for i in range(1,len(children)):
                child = children[i]
                dist = (child['x'] - x_new_point) ** 2 + (child['y'] - y_new_point) ** 2
                if dist < min_dist:
                    min_index = i
                    min_dist = dist
            node = children[min_index]
            

        #Now adds the new point to the leaf it has found.
        
        #INVARIANT: node is a leaf
        points = node['points']
        if len(points) < max_elements_per_cluster:
            #No split neeeded to add the point to this node
            
            #Can add the new_point to this node
            old_x_node = x_node = node['x']
            old_y_node = y_node = node['y']     
            
            #Compute the new centroid for the node
            n_p = len(points)
            x_node *= n_p
            y_node *= n_p
            x_node += x_new_point
            y_node += y_new_point
            points.append(new_point)
            n_p += 1
            x_node /= n_p
            y_node /= n_p
            node['x'] = x_node
            node['y'] = y_node
                
            #Compute node's radius and variance      
            radius = 0.
            x_var = y_var = 0.
            for point in points:
                #INVARIANT: points don't have radius
                x_dist = (x_node - point['x']) ** 2
                y_dist = (y_node - point['y']) ** 2
                radius = max(radius, x_dist + y_dist)
                #We don't need the exact variance, we can do fine with an estimate based on max distance form the centroid
                x_var = max(x_var, x_dist)
                y_var = max(y_var, y_dist)
            node['radius'] = sqrt(radius)
            node['x_var'] = x_var
            node['y_var'] = y_var
            
            #Propagates the change all the way to the root
            node_parent = node['parent']
            while node_parent != None:
                tmp_x = x_node_parent = node_parent['x']
                tmp_y = y_node_parent = node_parent['y'] 
                n_p = len(node_parent['children'])
                x_node_parent *= n_p
                y_node_parent *= n_p
                x_node_parent += x_node - old_x_node
                y_node_parent += y_node - old_y_node
                old_x_node = tmp_x
                old_y_node = tmp_y
                x_node_parent /= n_p
                y_node_parent /= n_p   
                node_parent['x'] = x_node_parent
                node_parent['y'] = y_node_parent 
                                           
                radius = 0.
                x_var = y_var = 0.
                for child_node in node_parent['children']:
                    x_dist = (x_node_parent - child_node['x']) ** 2
                    y_dist = (y_node_parent - child_node['y']) ** 2
                    radius = max(radius, sqrt(x_dist + y_dist) + child_node['radius'])                  
                    #We don't need the exact variance, we can do fine with an estimate based on max distance form the centroid
                    x_var = max(x_var, x_dist + child_node['radius'] ** 2)
                    y_var = max(y_var, y_dist + child_node['radius'] ** 2)
               
                node_parent['radius'] = radius
                node_parent['x_var'] = x_var
                node_parent['y_var'] = y_var
                                                
                node = node_parent
                node_parent = node['parent']
        else:
            #len(children) == max_elements_per_cluster => The leaf must be split
            
            #Splits along the direction with highest variance
            if node['x_var'] >= node['y_var']:
                points.sort(key=lambda p: p['x'])
            else:
                points.sort(key=lambda p: p['y'])
            
            #The new nodes have exactly half the elements of the old one
            new_node_1 = {'points': points[:split_size], 'leaf': True}
            new_node_2 = {'points': points[split_size:], 'leaf': True}          
        
            
            #Compute the centroids for the new nodes
            for new_node in [new_node_1, new_node_2]:
                points = new_node['points']
                x_node = 0.
                y_node = 0.
                for point in points: 
                    x_node += point['x']
                    y_node += point['y']
                n_p = len(points)
                x_node /= n_p
                y_node /= n_p
                
                new_node['x'] = x_node
                new_node['y'] = y_node
    
            #Adds the new point to the one of the two new nodes that is closest to the old centroid
            x_node = node['x']
            y_node = node['y']
            dist_1 = (x_node - new_node_1['x']) ** 2 + (y_node - new_node_1['y']) ** 2 
            dist_2 = (x_node - new_node_2['x']) ** 2 + (y_node - new_node_2['y']) ** 2
            
            if (dist_1 > dist_2):
                new_node = new_node_2
                new_node_2 = new_node_1
                new_node_1 = new_node
            
            #INVARIANT: at this point new_node_1 is the one of the two new nodes closest to the old node's centroid
            #Adds the new point to new_node_1
            points = new_node_1['points']       
            n_p = len(points)  
            #Updates new_node_1's centroid
            x_node = new_node_1['x']
            y_node = new_node_1['y']
            x_node *= n_p
            y_node *= n_p            
            x_node += new_point['x']
            y_node += new_point['y']
            points.append(new_point)
            n_p += 1
            new_node_1['x'] = x_node / n_p
            new_node_1['y'] = y_node / n_p
                        
            #Compute the radius of the new nodes
            for new_node in [new_node_1, new_node_2]:
                
                x_node = new_node['x']
                y_node = new_node['y']
                
                radius = 0.
                x_var = y_var = 0.
                for point in new_node['points']:
                    #INVARIANT: point don't have radius
                    x_dist = (x_node - point['x']) ** 2
                    y_dist = (y_node - point['y']) ** 2
                    radius = max(radius, x_dist + y_dist)
                    #We don't need the exact variance, we can do fine with an estimate based on max distance form the centroid
                    x_var = max(x_var, x_dist)
                    y_var = max(y_var, y_dist)
                    
                new_node['radius'] = sqrt(radius)
                new_node['x_var'] = x_var
                new_node['y_var'] = y_var      
                                
            
            #INVARIANT: at this new_point new_node_1 is the closest to the centroid of node, so it takes its place among the
            #childrens of its parent
            node_parent = node['parent']
            
            if node_parent == None:
                #The node that has just been split was the root: so it must create a new root...
                tree = {'children': [new_node_1, new_node_2], 'leaf':False, 'parent': None, 
                        'x': (new_node_1['x'] + new_node_2['x'])/2,
                        'y': (new_node_1['y'] + new_node_2['y'])/2}
                x_dist_1 = (new_node_1['x'] - tree['x']) ** 2
                x_dist_2 = (new_node_2['x'] - tree['x']) ** 2
                y_dist_1 = (new_node_1['y'] - tree['y']) ** 2
                y_dist_2 = (new_node_2['y'] - tree['y']) ** 2                                
                tree['radius'] = max(sqrt(x_dist_1 + y_dist_1) + new_node_1['radius'],
                                     sqrt(x_dist_2 + y_dist_2) + new_node_2['radius'])
                tree['x_var'] = max(x_dist_1 + new_node_1['radius'] ** 2, 
                                    x_dist_2 + new_node_2['radius'] ** 2)
                tree['y_var'] = max(y_dist_1 + new_node_1['radius'] ** 2,
                                    y_dist_2 + new_node_2['radius'] ** 2)
                
                new_node_1['parent'] = new_node_2['parent'] = tree
                
                #... and return it
                return tree                  
            else:
                #Replaces the old node (the one just split) with the closest of the newly created
                new_node_1['parent'] = node_parent
          
                node_parent['children'].remove(node)
                node_parent['children'].append(new_node_1)
            
    
                while node_parent != None:
                    node = node_parent
                    children = node['children']
                    
                    #Checks if there is still a node resulting from the split of one of its children
                    #INVARIANT:    new_node_2 is the farthest of the two resulting node from the split
                    if new_node_2:
                        
                        if len(children) < max_elements_per_cluster:
                            #No need for farther splits: just append the new node
                            children.append(new_node_2)
                            new_node_2['parent'] = node
                            new_node_2 = None                   
                        else:
                            #Must split this node too
                            old_node = new_node_2
                            
                            #Split the children along the axes with the biggest variance
                            if node['x_var'] >= node['y_var']:
                                children.sort(key=lambda p: p['x'])
                            else:
                                children.sort(key=lambda p: p['y'])                            
                                
                            new_children = children[:split_size]
                            new_node_1 = {'children': new_children, 'leaf': node['leaf']}
                            for child in new_children:
                                child['parent'] = new_node_1

                            new_children = children[split_size:]
                            new_node_2 = {'children': new_children, 'leaf': node['leaf']}
                            for child in new_children:
                                child['parent'] = new_node_2                         
                           
                            #Compute the centroids
                            for new_node in [new_node_1, new_node_2]:
                                x_node = 0.
                                y_node = 0.
                                for child in new_node['children']: 
                                    x_node += child['x']
                                    y_node += child['y']
                                n_p = len(new_node['children'])
                                new_node['x'] = x_node / n_p
                                new_node['y'] = y_node / n_p

                            #Finds the one of the new nodes closest to the original centroid  
                            dist_1 = (node['x'] - new_node_1['x']) ** 2 + (node['y'] - new_node_1['y']) ** 2 
                            dist_2 = (node['x'] - new_node_2['x']) ** 2 + (node['y'] - new_node_2['y']) ** 2
                            
                            if (dist_1 > dist_2):
                                new_node = new_node_2
                                new_node_2 = new_node_1
                                new_node_1 = new_node   
                                
                            #INVARIANT:    At this point new_node_1 is the one of two nodes resulting from the split
                            #                closest to the orginal centroid
                            n_p = len(new_node_1['children'])
                            new_node_1['children'].append(old_node)
                            old_node['parent'] = new_node_1
                            
                            x_node = new_node_1['x']
                            y_node = new_node_1['y']
                            x_node *= n_p
                            y_node *= n_p
                            x_node += old_node['x']
                            y_node += old_node['y']
                            n_p += 1
                            new_node_1['x'] = x_node / n_p
                            new_node_1['y'] = y_node / n_p
                            
                            #Compute the radiuses and the variances
                            for new_node in [new_node_1, new_node_2]:

                                x_node = new_node['x']
                                y_node = new_node['y']
                                
                                radius = 0.
                                x_var = y_var = 0.
                                
                                for child_node in new_node['children']:
                                    x_dist = (x_node - child_node['x']) ** 2
                                    y_dist = (y_node - child_node['y']) ** 2
                                    radius = max(radius, sqrt(x_dist  + y_dist) + child_node['radius'])  
                                    #We don't need the exact variance, we can do fine with an estimate based on max distance form the centroid
                                    x_var = max(x_var, x_dist + child_node['radius'] ** 2)
                                    y_var = max(y_var, y_dist + child_node['radius'] ** 2)
                                
                                new_node['radius'] = radius
                                new_node['x_var'] = x_var
                                new_node['y_var'] = y_var  
                            
                            #Checks whether the root has been split                            
                            node_parent = node['parent']
                            if node_parent == None:
                                #Has just split the root
                                tree = {'children': [new_node_1, new_node_2], 'leaf':False, 'parent': None, 
                                        'x': (new_node_1['x'] + new_node_2['x'])/2,
                                        'y': (new_node_1['y'] + new_node_2['y'])/2}
                                x_dist_1 = (new_node_1['x'] - tree['x']) ** 2
                                x_dist_2 = (new_node_2['x'] - tree['x']) ** 2
                                y_dist_1 = (new_node_1['y'] - tree['y']) ** 2
                                y_dist_2 = (new_node_2['y'] - tree['y']) ** 2                                
                                tree['radius'] = max(sqrt(x_dist_1 + y_dist_1) + new_node_1['radius'],
                                                     sqrt(x_dist_2 + y_dist_2) + new_node_2['radius'])
                                tree['x_var'] = max(x_dist_1 + new_node_1['radius'] ** 2, x_dist_2 + new_node_2['radius'] ** 2)
                                tree['y_var'] = max(y_dist_1 + new_node_1['radius'] ** 2, y_dist_2 + new_node_2['radius'] ** 2)
                                new_node_1['parent'] = new_node_2['parent'] = tree
                                return tree                                  
                            else:
                                new_node_1['parent'] = node_parent   
                          
                                node_parent['children'].remove(node)
                                node_parent['children'].append(new_node_1)
                                
                                #node doesn't exist anymore, and for new_node_1 and new_node_2 everything has been computed
                                #and therefore can go to the next iteration
                                continue
                            
                    #Updates node's centroid, radius and variances                       
                    x_node = 0.
                    y_node = 0.
                    
                    for child_node in children:
                        x_node += child_node['x']
                        y_node += child_node['y']
                    
                    n_p = len(children)
                    x_node /= n_p
                    y_node /= n_p
                    node['x'] = x_node
                    node['y'] = y_node
                                         
                    radius = 0.
                    x_var = y_var = 0.
                    for child_node in children:
                        x_dist = (x_node - child_node['x']) ** 2
                        y_dist = (y_node - child_node['y']) ** 2
                        radius = max(radius, sqrt(x_dist + y_dist) + child_node['radius'])
                        x_var = max(x_var, x_dist + child_node['radius'] ** 2)
                        y_var = max(y_var, y_dist + child_node['radius'] ** 2)
                        
                    node['radius'] = radius
                    node['x_var'] = x_var
                    node['y_var'] = y_var                        
    
                    node_parent = node['parent']
        
        return tree      
    
    #Creates the SS-tree for the topics (points)
    topics_tree = ss_make_tree()

    #List of the questions for which a topic is relevant
    topics_relevant_questions = {}

    #Reads the topics list
    regex = re.compile(TOPIC_REGEXP)
    for i in range(T):
        line = f.readline()
        m = regex.match(line)
        t_id = int(m.group(1))
        (x,y) = map(lambda s: float(s), m.group(2,3))
        topics[t_id] = (x, y)
        #Add the topic to the SS-tree
        topics_tree = ss_tree_insert({'x':x, 'y':y, 't_id':t_id}, topics_tree)
        #List of the questions for which a topic is relevant (initializes it)
        topics_relevant_questions[t_id] = []
 
                                  
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
            for t_id in Qids:
                topics_relevant_questions[t_id].append(q_id)
    
    #Uses a statically allocated array of doubles for the distances' heap, to avoid runtime checks and improve performance   
    heap = array('d', range(100))       #INVARIANT:    no more than 100 results are required for each query
    
  
    #Reads and processes the queries list            
    regex = re.compile(QUERY_REGEXP)
    for i in range(N):
        line = f.readline()
        m = regex.match(line)
        q_type = m.group(1)
        n_res = int(m.group(2))
        if n_res == 0:
            print ''
#DEBUG        file_out.write('\n')
            continue    
        
        (x0,y0) = map(lambda s: float(s), m.group(3,4))
        
        ''' Compares two elements of the solution: each element is a tuple (distance, ID),
            If the two distances are within a tolerance of 0.001 they are (by specs)
            considered equals, so in that case the couple with the highest ID is
            smaller; otherwise the order is determined by the two distances.
            
            @param (da,ia):     The first tuple to compare;
            @param (db,ib):     The second tuple to compare;
            @return:    An integer n:
                        < 0     <=>    (da,ia) < (db,ib)     [da-db < -0.001 or ia > ib]
                        > 0     <=>    (da,ia) > (db,ib)     [da-db > 0.001 or ia < ib]
                        0       <=>    (da,ia) == (db,ib)    [fabs(da-db) < 0.001 and ia == ib]            
        '''
        def compare_items((da,ia), (db,ib)):
            #checks the distances first: must be greater than the threshold (distances are non-negatives!)
            if da < db - 0.001:
                return -1
            elif da > db + 0.001:
                return 1
            else:
                #if the distances are within threshold, then compares ids
                return ib - ia
        
        #Switches the type of query
        if q_type == 't':
            #Init the heap to an empty max-heap
            heap_size = 0
            #Keeps track of the candidates to nearest neighbours found
            heap_elements = []          

            #Starts a search in the topics SS-tree;
            #All the topics are pushed in a bounded max-heap which holds at most n_res distances
            #(the n_res smallest ones) so that, once the heap is full, its first element is
            #the kth distance discovered so var, and this value can be used to prune the search
            #on the SS-tree.
            
            if topics_tree['leaf']:
                #The tree has only one node, the root: so every point must be examined
                points = topics_tree['points']
                for p in points:
                    t_id = p['t_id']
                    x = p['x']
                    y = p['y']

                    new_dist = sqrt((x - x0) ** 2 + (y - y0) ** 2)

                    if heap_size == n_res:
                        if new_dist > heap[0]:
                            #The heap is full: if the new value is greather than the kth distance,
                            #then it can't be one of the k nearest neighbour's distances                               
                            continue
                    
                        heap_elements.append((new_dist, t_id))                
                        pos = 0
                        # Bubble up the greater child until hitting a leaf.
                        child_pos = 2 * pos + 1    # leftmost child position
                        while child_pos < heap_size:
                            # Set childpos to index of greater child.
                            right_pos = child_pos + 1
                            if right_pos < heap_size and heap[child_pos] < heap[right_pos]:
                                child_pos = right_pos
                            # Move the greater child up.
                            if heap[child_pos] <= new_dist:
                                break
                            heap[pos] = heap[child_pos]
                            pos = child_pos
                            child_pos = 2*pos + 1
                        heap[pos] = new_dist           
                    else:
                        heap_elements.append((new_dist, t_id))                
                        heap[heap_size] = new_dist
                        pos = heap_size
                        heap_size += 1
                        # Follow the path to the root, moving parents down until finding a place
                        # newitem fits.
                        while pos > 0:
                            parent_pos = (pos - 1) >> 1
                            parent = heap[parent_pos]
                            if new_dist > parent:
                                heap[pos] = parent
                                pos = parent_pos
                            else:
                                break
                        heap[pos] = new_dist                    
            else:
                queue = []
                #Adds all the root's children to the queue, and examines them in order of increasing distance
                #of their border from the query point
                children = topics_tree['children']
                for child in children:
                    dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                    radius = child['radius']
                    if dist <= radius:
                        dist = 0
                    else:
                        dist -= radius
                    queue.append((dist, radius, child))

                queue.sort(key=lambda q:q[0], reverse=True)
                
                while len(queue) > 0:
                    (d, r, node) = queue.pop()
                    
                    if node['leaf']:
                        points = node['points']
                        for p in points:
                            t_id = p['t_id']
                            x = p['x']
                            y = p['y']

                            new_dist = sqrt((x - x0) ** 2 + (y - y0) ** 2)
                        
                            if heap_size == n_res:    
                                #The heap is full: if the new value is greather than the kth distance,
                                #then it can't be one of the k nearest neighbour's distances                       
                                if new_dist > heap[0]:                                   
                                    continue
                                
                                heap_elements.append((new_dist, t_id))
                                #heap[0] = new_dist
                                pos = 0
                                # Bubble up the greater child until hitting a leaf.
                                child_pos = 2 * pos + 1    # leftmost child position
                                while child_pos < heap_size:
                                    # Set childpos to index of greater child.
                                    right_pos = child_pos + 1
                                    if right_pos < heap_size and heap[child_pos] < heap[right_pos]:
                                        child_pos = right_pos
                                    # Move the greater child up.
                                    if heap[child_pos] <= new_dist:
                                        break
                                    heap[pos] = heap[child_pos]
                                    pos = child_pos
                                    child_pos = 2*pos + 1
                                heap[pos] = new_dist           
                            else:
                                heap_elements.append((new_dist, t_id))
                                heap[heap_size] = new_dist
                                pos = heap_size
                                heap_size += 1
                                # Follow the path to the root, moving parents down until it finds a place
                                #where new_item fits.
                                while pos > 0:
                                    parent_pos = (pos - 1) >> 1
                                    parent = heap[parent_pos]
                                    if new_dist > parent:
                                        heap[pos] = parent
                                        pos = parent_pos
                                    else:
                                        break
                                heap[pos] = new_dist
                                
                        #Checks if now the queue is full
                        if heap_size == n_res:
                            #If it is so, filters the queue
                            #The heap is full: if the distance of the border of the node from the query point
                            #is greather than the kth distance then no point in that node can be one of the
                            #k nearest neighbour's                              
                            d_max = heap[0]                                  
                            queue = [(d, r, n) for (d, r, n) in queue if d <= d_max]                                
                    else:
                        if heap_size < n_res:
                            for child in node['children']:
                                dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                                radius = child['radius']
                                if dist <= radius:
                                    dist = 0
                                else:
                                    dist -= radius
                                queue.append((dist, radius, child))
                             
                            queue.sort(key=lambda q:q[0], reverse=True)
                        else:
                            d_max = heap[0]        
                            queue = [(d, r, n) for (d, r, n) in queue if d <= d_max]                            
                            for child in node['children']:
                                dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                                radius = child['radius']
                                if dist <= radius:
                                    dist = 0
                                else:
                                    dist -= radius
                                
                                if dist <= d_max:
                                    #The heap is full: if the distance of the border of the node from the query point
                                    #is greather than the kth distance then no point in that node can be one of the
                                    #k nearest neighbour's                                       
                                    queue.append((dist, radius, child))

                            queue = sorted([(d, r, n) for (d, r, n) in queue if d <= d_max],
                                           key=lambda q:q[0], reverse=True)
                                                            
            #Filters the possible nearest neighbours such that their distance is not greater than the the distance of the kth
            #nearest neighbour (plus the tolerance)
            s = ['{} '.format(i_d) for (d, i_d) in 
                        sorted([(d, i_d) for (d, i_d) in heap_elements if d <= heap[0] + 0.001], 
                               cmp=compare_items)[:n_res]]
            
            print ''.join(s)
#DEBUG            
#            file_out.write(''.join(s))
#            file_out.write('\n')        
        else:    
            #query type 'q'
            
            #Starts a query on the topics, and as soon as it encounters new topics
            #(from the closest ones to the query point to the farthest) 
            
            questions_heap = []
            heap_elements = {}
            
            if topics_tree['leaf']:
                #The SS-tree for topics is just made of a root node:
                #All the points must be checked
   
                points = topics_tree['points']
                for p in points:
                    t_id = p['t_id']
                    (x,y) = topics[t_id]

                    new_dist = sqrt((x - x0) ** 2 + (y - y0) ** 2)

                    if len(heap_elements) >= n_res:
                        if new_dist > questions_heap[n_res-1] + 0.001:
                            continue
                        
                        useful = False
                        for q_id in topics_relevant_questions[t_id]:
                            if q_id in heap_elements and heap_elements[q_id] <= new_dist:
                                continue
                            else:
                                useful = True
                                heap_elements[q_id] = new_dist
                        
                        if useful:
                            questions_heap = sorted(heap_elements.itervalues())
                    else:
                        
                        for q_id in topics_relevant_questions[t_id]:
                            if q_id in heap_elements and heap_elements[q_id] <= new_dist:
                                    continue
                            else:
                                heap_elements[q_id] = new_dist
                        if len(heap_elements) >= n_res:
                            questions_heap = sorted(heap_elements.itervalues())      
            else:
                queue = []
                
                #Adds all the root's children to the queue, and then examine them one by one from the closest points to the
                #query point to the farthest ones: for each one checks the queries for which the topic is relevant
                #and for each of this queries checks if other closer relevant topics have been already found or not.
                #When at list n_res different questions have been met, starts comparing the distance from the query point
                #of farthest one to the distances (from the query point) of the SS-tree nodes' borders, pruning the search
                #on the nodes too far away.
                children = topics_tree['children']
                for child in children:
                    dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                    radius = child['radius']
                    if dist <= radius:
                        dist = 0
                    else:
                        dist -= radius
                    queue.append((dist, radius, child))

                queue.sort(key=lambda q:q[0], reverse=True)
                
                while len(queue) > 0:
                    (d, r, node) = queue.pop()
                    
                    if node['leaf']:
                        points = node['points']
                        for p in points:
                            t_id = p['t_id']
                            (x,y) = topics[t_id]

                            new_dist = sqrt((x - x0) ** 2 + (y - y0) ** 2)                           
                                              
                            if len(heap_elements) >= n_res:
                                if new_dist > questions_heap[n_res-1] + 0.001:
                                    continue
                                
                                useful = False
                                for q_id in topics_relevant_questions[t_id]:
                                    if q_id in heap_elements and heap_elements[q_id] <= new_dist:
                                        continue
                                    else:
                                        useful = True
                                        heap_elements[q_id] = new_dist
                                
                                if useful:
                                    questions_heap = sorted(heap_elements.itervalues())
                            else:
                                
                                for q_id in topics_relevant_questions[t_id]:
                                    if q_id in heap_elements and heap_elements[q_id] <= new_dist:
                                        continue
                                    else:
                                        heap_elements[q_id] = new_dist
                                        
                                if len(heap_elements) >= n_res:
                                    questions_heap = sorted(heap_elements.itervalues())
                                
                        #Checks if it has already found at least n_res questions
                        if len(heap_elements) >= n_res:
                            #If it is so, filters the queue
                            d_max = questions_heap[n_res-1] + 0.001                                  
                            queue = [(d, r, n) for (d, r, n) in queue if d <= d_max]                                
                    else:
                        
                        if len(heap_elements) < n_res:
                            for child in node['children']:
                                dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                                radius = child['radius']
                                if dist <= radius:
                                    dist = 0
                                else:
                                    dist -= radius
                                queue.append((dist, radius, child))
                              
                            queue.sort(key=lambda q:q[0], reverse=True)
                        else:
                            for child in node['children']:
                                dist = sqrt((child['x'] - x0) ** 2 + (child['y'] - y0) ** 2)
                                radius = child['radius']
                                if dist <= radius:
                                    dist = 0
                                else:
                                    dist -= radius
                                d_max = questions_heap[n_res-1] + 0.001
                                if dist <= d_max:
                                    queue.append((dist, radius, child))

                            queue = sorted([(d, r, n) for (d, r, n) in queue if d <= d_max], key=lambda q:q[0], reverse=True)
  


                
            s = ['{} '.format(i_d) for (d, i_d) in 
                 sorted([(d, i_d) for (i_d, d) in heap_elements.iteritems()],
                        cmp=compare_items)[:n_res] ]
            
            print ''.join(s)
#DEBUG            
#            file_out.write(''.join(s))
#            file_out.write('\n')        

    return  

if __name__ == '__main__':
  
    read_and_process_input(stdin)
