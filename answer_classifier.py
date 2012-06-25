'''
@author: mlarocca02
'''
import re
from sys import stdin, stdout, argv

from sklearn import svm, cross_validation, grid_search
from random import seed, randrange
from time import time
from sklearn.preprocessing import Scaler
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.lda import LDA
from numpy import array
from math import floor
from sklearn.linear_model.logistic import LogisticRegression
 
INTEGER_RE = "([+-]?\d+)" 
INTEGER_RE_NOGROUP = "\d+" 
DOUBLE_RE_NOGROUP = "[+-]?\d+\.\d+"
FEATURE_VALUE = '(' + INTEGER_RE_NOGROUP + '|' + DOUBLE_RE_NOGROUP + ')'
STRING_RE = "([a-zA-Z0-9]{1,10})"
SEPARATOR = "\s+" 
FEATURES_SEPARATOR = ':'


'''
    Generates a partiotion of indices from 0 to n-1 into two sets of k and n-k elements
'''
def split_indices(n, k):
    indices = range(n)
    #Creates a random permutation of the indices, based upon uniform distribution
    for i in range(0, n-1):
        j = randrange(i,n)
        tmp = indices[i]
        indices[i] = indices[j]
        indices[j] = tmp
    
    return indices[:k], indices[k:]


def shuffle(x,y):
    n = len(x)
    #Creates a random permutation of the indices, based upon uniform distribution
    for i in range(0, n-1):
        j = randrange(i,n)
        tmp = x[i]
        x[i] = x[j]
        x[j] = tmp
        tmp = y[i]
        y[i] = y[j]
        y[j] = tmp
        

'''Trains a SVM classifier on a training set, cross validating  on its parameters.
   Once trained, uses the SVM to predict the label on a new set, and returns the resulting list of labels.
   @param X_in:    The (input) feature vector;
   @param y_in:    The (input) label vector;
   @param X_out:    The vector of point that needs to be classified;
   @param gammas:    Set of values to be cross-validated for the parameter gamma of the SVM's RBF Kernel;
   @param cs:    Set of values to be cross-validated fot the parameter C of the SVM.
   @param file_log:    If specified, a file upon which the log stream should be written;
   return:    A list of the predicted labels for the points that needs to be classified.
'''
def SVM_train(X_in, y_in, X_out, gammas, cs, file_log=None):    
    if file_log:        
        file_log.writelines('# of Samples: {}, # of Features: {}\n'.format(len(X_in), len(X_in[0])))
    M = len(X_in[0])   #Number of features
    seed(time())
    
    #To prevent data snooping, breaks the input set into train. cross validation
    #and scale sets, with sizes proportional to 8-1-1
    
    #First puts aside 10% of the data for the tests
    scale_set_indices, train_indices = split_indices(len(X_in), int(round(0.1*len(X_in))))

#    shuffle(X_in, y_in)
    
    X_scale = [X_in[i] for i in scale_set_indices]
    y_scale = [y_in[i] for i in scale_set_indices]
    X_in = [X_in[i] for i in train_indices]
    y_in = [y_in[i] for i in train_indices]
        
    #Scale data first
    scaler = Scaler(copy=False)             #WARNING: copy=False => in place modification
    #Normalize the data and stores as inner parameters the mean and standard deviation
    #To avoid data snooping, normalization is computed on a separate subsetonly, and then reported on data
    scaler.fit(X_scale, y_scale)
    X_scale = scaler.transform(X_scale)
    X_in = scaler.transform(X_in)
    X_out = scaler.transform(X_out)         #uses the same transformation (same mean_ and std_) fit before
    
    std_test = X_scale.std(axis=0)
    f_indices = [j for j in range(M) if std_test[j] > 1e-7]
    
    #Removes feature with null variance    
    X_in = [[X_in[i][j] for j in f_indices] for i in range(len(X_in))]
    X_scale = [[X_scale[i][j] for j in f_indices] for i in range(len(X_scale))]
    X_out = [[X_out[i][j] for j in f_indices] for i in range(len(X_out))]
    
    
    if file_log:        
        file_log.writelines('Initial features :{}, Features used: {}\n'.format(M, len(X_in[0])))
    
    M = len(f_indices)
    best_cv_accuracy = 0.
    best_gamma = 0.
    best_c = 0.

     
    #Then, on the remaining data, performs a ten-fold cross validation over the number of features considered
    for c in cs:
        for g in gammas:
            #Balanced cross validation (keeps the ratio of the two classes as
            #constant as possible across the k folds).
            kfold = cross_validation.StratifiedKFold(y_in, k=10)        
            svc = svm.SVC(kernel='rbf', C=c, gamma=g, verbose=False, cache_size=4092, tol=1e-5)
                                
            in_accuracy = 0.
            cv_accuracy = 0.
            for t_indices, cv_indices in kfold:
        
                X_train = array([X_in[i][:] for i in t_indices])
                y_train = [y_in[i] for i in t_indices]
                X_cv = array([X_in[i][:] for i in cv_indices])
                y_cv = [y_in[i] for i in cv_indices]                
                
                svc.fit(X_train, y_train)
                in_accuracy += svc.score(X_train, y_train)
                cv_accuracy += svc.score(X_cv, y_cv)
            
            in_accuracy /= kfold.k
            cv_accuracy /= kfold.k
            if file_log:        
                file_log.writelines('C:{}, gamma:{}\n'.format(c, g))           
                file_log.writelines('\tEin= {}\n'.format(1. - in_accuracy))
                file_log.writelines('\tEcv= {}\n'.format(1. - cv_accuracy))
    
            if (cv_accuracy > best_cv_accuracy):
                best_gamma = g
                best_c = c
                best_cv_accuracy = cv_accuracy
            
    if file_log:        
        file_log.writelines('\nBEST result: E_cv={}, C={}, gamma={}\n'.format(1. - best_cv_accuracy, best_c, best_gamma))
    
    
    svc = svm.SVC(kernel='rbf', C=best_c, gamma=best_gamma, verbose=False, cache_size=4092, tol=1e-5)

    svc.fit(X_in, y_in)
    if file_log:        
        file_log.writelines('Ein= {}\n'.format(1. - svc.score(X_in, y_in)))
        file_log.writelines('Etest= {}\n'.format(1. - svc.score(X_scale, y_scale)))      
        
    y_out = svc.predict(X_out)
#DEBUG:    output = ['{} {:+}\n'.format(id_out[i], int(y_scale[i])) for i in range(len(X_out))]
#DEBUG:    file_log.writelines('------------------------')    
    return y_out



'''Trains a SVM classifier on the given training set, using the parameters passed.
   Once trained, uses the SVM to predict the label on a new set, and returns the resulting list of labels.
   @param X_in:    The (input) feature vector;
   @param y_in:    The (input) label vector;
   @param X_out:    The vector of point that needs to be classified;
   @param gamma:    The parameter gamma of the SVM's RBF Kernel;
   @param c:    The parameter C of the SVM.
   return:    A list of the predicted labels for the points that needs to be classified.
'''
def SVM_fit(X_in, y_in, X_out, gamma, C):    

    M = len(X_in[0])   #Number of features
    seed(time())
    
    #To prevent data snooping, breakes the input set into train. cross validation and test sets, with sizes proportional to 8-1-1
    
    #First puts aside 10% of the data for the tests
    test_indices, train_indices = split_indices(len(X_in), int(round(0.1*len(X_in))))

    shuffle(X_in, y_in)
    
    X_test = [X_in[i] for i in test_indices]
    y_test = [y_in[i] for i in test_indices]
    X_in = [X_in[i] for i in train_indices]
    y_in = [y_in[i] for i in train_indices]
  
    
    #scale data first
    scaler = Scaler(copy=False) #in place modification
    #Normalize the data and stores as inner parameters the mean and standard deviation
    #To avoid data snooping, normalization is computed on training set only, and then reported on data
    scaler.fit(X_test, y_test)
    X_in = scaler.transform(X_in)
    X_test = scaler.transform(X_test)
    X_out = scaler.transform(X_out) #uses the same transformation (same mean_ and std_) fit before

    std_test = X_test.std(axis=0)
    f_indices = [j for j in range(M) if std_test[j] > 1e-7]
    
    #Removes feature with null variance    
    X_in = [[X_in[i][j] for j in f_indices] for i in range(len(X_in))]
    X_test = [[X_test[i][j] for j in f_indices] for i in range(len(X_test))]
    X_out = [[X_out[i][j] for j in f_indices] for i in range(len(X_out))]

    M = len(f_indices)
    #Then, on the remaining data, performs a ten-fold cross validation over the number of features considered    
    svc = svm.SVC(kernel='rbf', C=C, gamma=gamma, verbose=False, cache_size=4092, tol=1e-5)   
    svc.fit(X_in, y_in)      
        
    y_out = svc.predict(X_out)
    return y_out


''' Trains a Tree Decision classifier cross validating  on the number of features used
    Once trained, uses it to predict the label on a new set, and returns a list of
    the labels predicted by the classifier.
    @param min_meaningful_features_ratio:    the minimum ratio of features that should
                                                be considered meaningful: default 100%
'''
def tree_train(X_in, y_in, X_out, min_meaningful_features_ratio=1., file_log=None):    
    if file_log:        
        file_log.writelines('# of Samples: {}, # of Features: {}\n'.format(len(X_in), len(X_in[0])))

    M = len(X_in[0])   #Number of features
    seed(time())
    
    #To prevent data snooping, breaks the input set into train. cross validation and test sets, with sizes proportional to 8-1-1
    
    #First puts aside 10% of the data for the tests
    test_indices, train_indices = split_indices(len(X_in), int(round(0.1*len(X_in))))
   
    X_scaler = [X_in[i] for i in test_indices]
    y_scaler = [y_in[i] for i in test_indices]
    X_in = [X_in[i] for i in train_indices]
    y_in = [y_in[i] for i in train_indices]
    
    #scale data first
    scaler = Scaler(copy=False) #in place modification
    #Normalize the data and stores as inner parameters the mean and standard deviation
    #To avoid data snooping, normalization is computed on training set only, and then reported on data
    scaler.fit(X_scaler, y_scaler)  
    X_scaler = scaler.transform(X_scaler)
    X_in = scaler.transform(X_in)
    X_out = scaler.transform(X_out) #uses the same transformation (same mean_ and std_) fit before
    
    std_test = X_scaler.std(axis=0)
    f_indices = [j for j in range(M) if std_test[j] > 1e-7]
    
    #Removes feature with null variance
    
    X_in = [[X_in[i][j] for j in f_indices] for i in range(len(X_in))]
    X_scaler = [[X_scaler[i][j] for j in f_indices] for i in range(len(X_scaler))]
    X_out = [[X_out[i][j] for j in f_indices] for i in range(len(X_out))]
  
    M = len(f_indices)
    #Then, on the remaining data, performs a ten-fold cross validation over the number of features considered
    best_cv_accuracy = 0.
    best_features_number = M
                
    for features_number in range(int(floor(M * min_meaningful_features_ratio)), M + 1):
    
        
        # kfold = cross_validation.KFold(len(y_in), k=10, shuffle=True)
        kfold = cross_validation.StratifiedKFold(y_in, k=10)
        svc = ExtraTreesClassifier(criterion='entropy', max_features=features_number)

                            
        in_accuracy = 0.
        cv_accuracy = 0.
        for t_indices, cv_indices in kfold:
    
            X_train = array([[X_in[i][j] for j in range(M)] for i in t_indices])
            y_train = [y_in[i] for i in t_indices]
            X_cv = array([[X_in[i][j] for j in range(M)] for i in cv_indices])
            y_cv = [y_in[i] for i in cv_indices]        
            

            svc.fit(X_train, y_train)
            in_accuracy += svc.score(X_train, y_train)
            cv_accuracy += svc.score(X_cv, y_cv)
   
        
        in_accuracy /= kfold.k
        cv_accuracy /= kfold.k
        if file_log:        
            file_log.writelines('# of features: {}\n'.format(len(X_train[0])))   
            file_log.writelines('\tEin= {}\n'.format(1. - in_accuracy))
            file_log.writelines('\tEcv= {}\n'.format(1. - cv_accuracy))
    
        if (cv_accuracy > best_cv_accuracy):
            best_features_number = features_number
            best_cv_accuracy = cv_accuracy
            
    #Now tests the out of sample error
    if file_log:        
        file_log.writelines('\nBEST result: E_cv={}, t={}\n'.format(1. - best_cv_accuracy, best_features_number))
    
    
    svc = ExtraTreesClassifier(criterion='entropy', n_estimators=features_number)
    svc.fit(X_in, y_in)
    if file_log:        
        file_log.writelines('Ein= {}\n'.format(1. - svc.score(X_in, y_in)))
        file_log.writelines('Etest= {}\n'.format(1. - svc.score(X_scaler, y_scaler)))    
        
    y_out = svc.predict(X_out)
    return y_out



''' Logistic Regression classifier
    @param X_in:    The (input) feature vector;
    @param y_in:    The (input) label vector;
    @param X_out:    The vector of point that needs to be classified;
    @param cs:    Set of values to be cross-validated fot the parameter C of the SVM.
    @param file_log:    If specified, a file upon which the log stream should be written;
    return:    A list of the predicted labels for the points that needs to be classified.
'''
def Logistic_train(X_in, y_in, X_out, cs, file_log=None):    
    if file_log:        
        file_log.writelines('# of Samples: {}, # of Features: {}\n'.format(len(X_in), len(X_in[0])))
    M = len(X_in[0])   #Number of features
    seed(time())
    
    #To prevent data snooping, breakes the input set into train. cross validation and test sets, with sizes proportional to 8-1-1
    
    #First puts aside 10% of the data for the tests
    test_indices, train_indices = split_indices(len(X_in), int(round(0.1*len(X_in))))
    
    X_scaler = [X_in[i] for i in test_indices]
    y_scaler = [y_in[i] for i in test_indices]
    X_in = [X_in[i] for i in train_indices]
    y_in = [y_in[i] for i in train_indices]
    
    
    
    #scale data first
    scaler = Scaler(copy=False) #in place modification
    #Normalize the data and stores as inner parameters the mean and standard deviation
    #To avoid data snooping, normalization is computed on training set only, and then reported on data
    scaler.fit(X_scaler, y_scaler)  
    X_scaler = scaler.transform(X_scaler)
    X_in = scaler.transform(X_in)
    X_out = scaler.transform(X_out) #uses the same transformation (same mean_ and std_) fit before
    
    std_test = X_scaler.std(axis=0)
    f_indices = [j for j in range(M) if std_test[j] > 1e-7]
    
    #Removes feature with null variance
    
    X_in = [[X_in[i][j] for j in f_indices] for i in range(len(X_in))]
    X_scaler = [[X_scaler[i][j] for j in f_indices] for i in range(len(X_scaler))]
    X_out = [[X_out[i][j] for j in f_indices] for i in range(len(X_out))]   
    
    M = len(X_in[0])
    #Then, on the remaining data, performs a ten-fold cross validation over the number of features considered
    best_cv_accuracy = 0.
    best_c = 0.



    for c in cs:
        kfold = cross_validation.StratifiedKFold(y_in, k=10)
        lrc = LogisticRegression(C=c, tol=1e-5)
                            
        in_accuracy = 0.
        cv_accuracy = 0.
        for t_indices, cv_indices in kfold:
    
            X_train = array([X_in[i][:] for i in t_indices])
            y_train = [y_in[i] for i in t_indices]
            X_cv = array([X_in[i][:] for i in cv_indices])
            y_cv = [y_in[i] for i in cv_indices]            
            
            lrc.fit(X_train, y_train)
            in_accuracy += lrc.score(X_train, y_train)
            cv_accuracy += lrc.score(X_cv, y_cv)
              
        in_accuracy /= kfold.k
        cv_accuracy /= kfold.k
        
        if file_log:
            file_log.writelines('C: {}\n'.format(c))  
            file_log.writelines('\tEin= {}\n'.format(1. - in_accuracy))
            file_log.writelines('\tEcv= {}\n'.format(1. - cv_accuracy))

        if (cv_accuracy > best_cv_accuracy):
            best_c = c
            best_cv_accuracy = cv_accuracy
            
    #Now tests the out of sample error
    if file_log:        
        file_log.writelines('\nBEST result: E_cv={}, C={}\n'.format(1. - best_cv_accuracy, best_c)) 
    
    lrc = LogisticRegression(C=best_c, tol=1e-5)

    lrc.fit(X_in, y_in)
    if file_log:        
        file_log.writelines('Ein= {}\n'.format(1. - lrc.score(X_in, y_in)))
        file_log.writelines('Etest= {}\n'.format(1. - lrc.score(X_scaler, y_scaler)))     
        
    y_out = lrc.predict(X_out)
    return y_out

''' Reads the program input from a file (by default stdin)
    @param f:    The file containing the input;
    @return:    (X_train, y_train, answers), (X_out, queries)
                    X_train:    The input vector;
                    y_train:    The labels for each of the input points
                                (i.e. for each input answer);
                    train_id_set:    The list of all the answers ID, in
                                       the same order as they are inserted in X_train;
                                        
                    X_out:    List of point (answers) to be classified;
                    out_id_set:    List of the id of the answers to
                                        classify.
'''
def read_input(f):
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    #INVARIANT: the input is assumed well formed and adherent to the challenge specs
    
    line = f.readline()
    m = regex.findall(line)
    #Number of points
    N = int(m[0])
    #Number of features
    M = int (m[1])
    answer_regex = STRING_RE + SEPARATOR + INTEGER_RE + (SEPARATOR + INTEGER_RE_NOGROUP + FEATURES_SEPARATOR + FEATURE_VALUE) * M
    
    queries_regex = STRING_RE + (SEPARATOR + INTEGER_RE_NOGROUP + FEATURES_SEPARATOR + FEATURE_VALUE) * M
    
    y_train = []
    X_train = []
    train_id_set = []
    
    #Reads the train_id_set list
    regex = re.compile(answer_regex)
    for i in range(N):
        line = f.readline()
        m = regex.match(line)
        answer_id = m.group(1)
        label = int(m.group(2))
        features = map(lambda f: float(f), m.groups()[2:M + 2])
        X_train.append(features)
        y_train.append(label)
        #Stores the answer id in a separate structure
        train_id_set.append(answer_id)
    
    regex = re.compile(INTEGER_RE)  #Regular Expression for integers
    line = f.readline()
    #Number of features
    m = regex.findall(line)
    q = int(m[0])
    
    out_id_set = []
    X_out = []
    #Reads the train_id_set list
    regex = re.compile(queries_regex)
    for i in range(q):
        line = f.readline()
        m = regex.match(line)
        answer_id = m.group(1)
        features = map(lambda f: float(f), m.groups()[1:M + 2])
        X_out.append(features)
        #Stores the answer id in a separate structure (not strictly needed according to problem formulation)
        out_id_set.append(answer_id)

    return (X_train, y_train, train_id_set), (X_out, out_id_set)

''' Polynomial transform:
    Transformation between linear feature space and quadratic features space.
    (To be used with logistic regression).
    @param x:    The input vector (corresponds to one point to classify);
    @return:    The transformed vector.
'''
def polynomial_transform(x):
    pol = []
    m = len(x)
    for i in range(m):
        pol.append(x[i]**2)
        for j in range(i+1,m):
            pol.append(2*x[i]*x[j])
            
    return pol

''' Main.    
    USAGE:
    -f filename: Reads input from a file [by default it reads input from stdin]
    -o filename: Writes output to a file [by default it writes output on stdout]
    -l filename: Logs debug info, like In-samples, and Cross-validation Errors for every parameters combination, on a log file
                    NOTE: for -o option only, it is possible to specify 'stdout' explicitly as the output stream;
    - m mode: enable one of the 3 working modes. Mode must be one of the following values:
        - normal [Default]:    Normal training will be conducted on the input (requires several minutes)
        - fast:    The best parameters cross-validated on the test case will be used (very quick, but just for testing)
        - tree:    A (extra randomized) Decision Tree classifier is used instead of SVM;
        - logistic:    Logistic Regression is used instead fo SVM;
        - thorough: additional parameters will be tested, and PCA will also be attempted on the training set, cross-validating
                    the number of features kept by PCA (Estimate Execution Time: about 2 to 3 hours)
'''
if __name__ == '__main__':
    
    file_in = stdin
    file_out = stdout
    file_log = None
    
    fast_mode = logistic_regression_mode = tree_mode = False
    
    #Set of values from which c and gamma parameters of the SVM will be chosen during cross validation
    #These are the default values: in thorough mode, however, larger sets will be used to train the classifier
    c_set = [0.1, 0.3, 0.5, 1, 3, 5,  7.5, 10, 12.5, 15, 17.5, 20]
    gamma_set = [0.001, 0.005, 0.01, 0.015, 0.03, 0.05] 

    
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
        if (argv[i] == '-m'):
            i += 1
            if i >= len(argv):
                print 'Error using option -m: mode name required'
                break
            mode = argv[i]
            if mode == 'fast':
                #Fast mode: only a subset of the default values will be tested
                fast_mode = True   
            elif mode == 'logistic':
                logistic_regression_mode = True
            elif mode == 'tree':
                tree_mode = True
            elif mode == 'thorough':
                #Thorough mode: more values will be tested, and PCA will be performed on the training set (starting from 2/5 of the original
                #features number
                c_set = [0.1, 0.3, 0.5, 1, 2, 3, 4, 5, 5.5, 6, 7, 7.5, 8, 9, 10, 11.25, 12.5, 13.75, 15, 17.5, 20, 25]
                gamma_set = [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.075, 0.1]
            elif mode != 'normal':
                print 'Error using -m option: valid modes are thorough, normal, logistic, tree and fast'

    (X_train, y_train, id_train), (X_out, id_out) = read_input(file_in)


#TODO: DELETE:
    y_out = []
    regex = re.compile(STRING_RE + SEPARATOR + INTEGER_RE)
    f = open('output00.txt', 'r')
    for i in range(len(X_out)):
        line = f.readline()
        m = regex.match(line)
        y_out.append(int(m.group(2)))
    f.close()
#TODO: END DELETE 


    if fast_mode:
        output_labels = SVM_fit(X_train[:], y_train[:], X_out[:], 0.05, 3)
    elif logistic_regression_mode:
        output_labels = Logistic_train(X_train[:], y_train[:], X_out[:], c_set, file_log)
    elif tree_mode:
        output_labels = tree_train(X_train[:], y_train[:], X_out[:], .4, file_log);
    else:
        output_labels = SVM_train(X_train[:], y_train[:], X_out[:], gamma_set, c_set, file_log);

#TODO: DELETE:        
    if file_log:    
        score = 0.
        for i in range(len(y_out)):
            if y_out[i] == output_labels[i]:
                score += 1
        file_log.write('Tot E_out: {}\n'.format(1. - score / len(y_out)))
                    
    output = ['{} {:+}\n'.format(id_out[i], int(output_labels[i])) for i in range(len(output_labels))]
#TODO: END DELETE 
    
    file_out.writelines(output)
    file_out.close()
    file_in.close()
    if file_log:
        file_log.close()