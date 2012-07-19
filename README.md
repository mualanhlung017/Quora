Two versions are given for the challenges:
An elegant, easy to read and fully commented version, and an optimized version, needed to stay eithin the challenges' time constraints, where the use of classes, function calls and redundant data is reduced to the bone.
The second version has been developed to solve the quora challenges on quora.interviewstreet.com, so, since it is evaluated by an automated tool and it's not intended to be read or used by humans, comments and elegance of code are sacrificed for efficiency and effectiveness.

1.: nearby (Python)
	a)	R-trees version (Completely solves the challenge - file nearby_rtree.py)
		The right data structure is often crucial to achieve good performance, and for spatial queries the right DS are R-trees or Voronoi Diagrams (or their duals, Delauney triangulation graphs).
		I decided to go with R-trees, and in particular with a special kind of them, the SS-trees, that uses spheres instead of rectangles to bound points and are therefore
		more intuitive and more versed for spatial vicinity queries.
		In an SS-tree each node is either an intermediate node, a leaf or a feature vecture (i.e. a point in space); only leafs contain actual points from the space and
		leafs and intermediate nodes represents spheres surrounding all the points in their subtrees. Since R-trees are an extension of b-trees, all the leafs are on the same level,
		and each intermediate node but the root has from t to 2t-1 children (actually in my implementation it's form t to 2*t).
		
		First I build an SS-tree of the topics set, allowing at most 16 points for each leaf and splitting nodes along x or y directiong according to which one presents the highest variance.
		
		The topic queries are simply k-nearest neighbours search on the topics tree, where all the topics encountered are pushed in a bounded max-heap which holds at most n_res distances
        (the n_res smallest ones) so that, once the heap is full, its first element is the kth distance discovered so far, and this value can be used to prune the search on the SS-tree.
       
		For question queries, instead, starts a k-nearest neighbours search for the query point, but for each topics encounterd checks the queries for which the topic is relevant and for each of this queries checks if other closer relevant topics have been already found or not.
		When at list k different questions have been met, starts comparing the distance from the query point of farthest one to the distances (from the query point) of the SS-tree nodes' borders, pruning the search on the nodes too far away.

	b)	Original approach (file nearby.py and nearby_fast.py for the optimized version, twice as fast but not as readable)
	
		I decided to use an approach where I create a sorted list of the best topics for every query, because it looked more efficient:
		Suppose we have T topics, Q questions, and N queries;
		If the query is about a topic (t-type query), and we were to compute the distance of each topic's point from the query's center, and then sort the
		topics based on this distance and take the first k (where k is the second parameter of the query), then it would require time
		proportional to O(T + T*log T + k) = O(T*log T), since k<=T and provided we can compute the distance in constant time.
		If, instead, we keep a list of the best k topics, and insert each topic we examine in this ordered list, each step is bounded by
		O(log(k) + k) where O(log k) is needed to find the place to insert the new element and O(k) is a (large!) bound for the elements shift
		needed to insert an element in the middle of a sorted array of size k; for each query it is then required time proportional to O(T*k);
		If k<<T, being k constant, the total amount of time needed is O(T), while if k is close to T, the bound becomes O(T**2).
		Since by definition of the problem k<=10, the bound becomes O(10*T) = O(T) < O(T*log T), so the latter solution is to prefer.

		For q-type queries, the function to compute the distance requires to compute the distances of all the topics related to a question, 
		and then take the min value; for a question with Qn topic references then, supposing the distance can be computed in constant time O(c),
		it is required time O(Qn*c) < O(max{Qn}*c) < O(10*c) by definition of the problem, so it is still required constant time to compute the
		distance of a question from the query center and so the bound for each q-type query is analougous to the t-type query's ones.

		Therefore, since we can expect Q<T (max{Q}=max{T}/10), a pessimistic bound for the whole proximity search algorithm is O(N*T)

2.: Typeahead Search (Java)
	a)	RadixTree (Correctly solves within the allotted time 9 out of 10 test cases of the quora.interviewstreet.com challenge - file Solution.java)
		Radix trees (aka Patricia Trees) and prefix trees are used to speed up the execution.
		Prefix tree, which are basically uncompressed tries, are used in order to keep track of the valid IDs added to the DB so far, in order to quickly recover the item associated with an ID on a delete request.
		Patricia Trees, insetad, are tries where each node has at least 2 children and commom paths (i.e. common substrings) are coupled together in a single node, in order to speed up search.
		For every item, its data field is broken into tokens (i.e. strings without spaces) and every one of them is inserted into a single radix tree that contains all of the prefixes in the DB, and every node of the tree (corrisponding to every prefix in the data) contains a list of the items that matches that particular prefix: for a single query, therefore, it is sufficient to break the query string itself into tokens, then for every one of this query tokens starts a visit of the tree: if there is a path from a token to an intermediate node or leaf whose edges exactly match the token, then all the items linked by that node matches the token. To found the matched for the whole query, the intersection of all the sets of items corresponding to the single token searches is computed.

	b) 	Original approach (file Typeahead.java)
		Here an approach similar to the one developed for the nearby (b version) is used, and if a query or wquery specifies a maximum number of results, let's say M, the item matching the query are temporarily stored in a sorted list that will hold at most M elements.
		To restrain the solution in a single file and avoid creating a package, accessory classes have been implemented as static inner classes.

3.: Scrabble Stepladder (Python)

	a) 	Backtracking + heuristic pruning (Completely solves the challenge - file stepladder_fast.py)
		For each word in the dictionary is computed an upperbound on the possible score (since the scores on each ladder's element must be lower than its predecessor score, the max score is twice the sum of the integers between 1 and the score of the central ladder minus one); if the upperbound is lower than the best score found so far, backtracking is performed.
		The same heuristic may be applied after each step in which the ladder is grown by adding two elements to its sides.

	b)	Simulated annealing (file stepladder_annealing.py)
		The second approach uses simulated annealing: while it cannot guarantee an optimal result, since the problem space has several local maxima, in practice it always find the optimal solution in a very short amount of time. I made a variant with respect to classic randomized-restart simulated annealing so that a single annealing cycle stops, as usual, when a critically low temperature is reached, but the number of cycles isn't specified as a parameter: the routine keeps performing annealing cycles until the allotted amount of time (passed as a parameter) is consumed. This way, if one needs an answer in a shorter amount of time than the backtracking procedure execution time (that in particular for huge dictionaries can be relevant), it is possible to have a semi-optimal solution in a few seconds, or a minute, or however long we can wait. 
		The heuristic pruning could be used here as well to better channel the evolutionary algorithms torwards global maximum.
		
4.: Feed Optimizer (Python)

	The problem is an instance of 0-1 Knapsack problem, and that problem is NP-Hard.
	
	a)	Exact solution (Horowitz-Sahni, Martello-Toth algorithms - Solves 8 out of 10 test cases - file feed_optimizer.py)
		The Horowitz-Sahni algorithm works quite well even for large inputs. The main cycle of the algorithm tries further optimization using the structure of the problem, i.e. the incremental construction of the set of items: when a new item is added, for example, first it is checked if it can added to the current solution, otherwise it is checked whether a solution containing the new item would lead to a higher aggregate value.
		To speed up the algorithm, elements from the Martello Toth algorithm are used as well especially to improve the upperbound estimate used in the pruning and to avoid backtracking on useless solutions.
		
	b)	Simulated Annealing / Genetic Algorithms (file feed_optimizer_annealing, feed_optimizer_GA)
		For smaller inputs, two randomized solutions, a simulated annealing and a genetic algorithm, are also provided, although they are clearly outperformed by the exact backtracking algorithm.
		 

		From command line, a few parameters can be passed:

			-f filename: Reads input from a file [by default it reads input from stdin]
			-o filename: Writes output to a file [by default it writes output on stdout]
			-l filename: Logs debug info, like intermediate results, on a log file
							NOTE: for -o option only, it is possible to specify 'stdout' explicitly as the output stream;
			-tl time_limit: Set a (approximate) time limit in seconds for the global execution [Default is 4.5 seconds]
								The mechanism used is very simple and far from giving high resolution control on the execution time, but should ensure an execution time reasonably close to the limit provided, without degrading the global performance.
			-ps population_size: Set the dimension of the population evolved by the GA [Default is 25];
									Larger population means getting to the optimal result in fewer generations,
									but also allows fewer generation to be trained in a fixed time.

		The program accepts a parameter from command line that specifies an approximate execution time limit (by default is set to 4.5 seconds, in order to contain the total running time within the 5 seconds mentioned in the description of the challenge). Different values can be specified using the '-tl time_limit' option (See the sketched manual inside the Python module); although the algorithm appears to converge very quickly to the optimal solution, an estimate of the required execution time of the genetic algorithm to always get the optimal solution requires a real-size test case.

5.: Answer classifier (Python, libsvm, scikit-learn)

Different options are available, with an execution time going from a few seconds to several hours. Please refer to the USAGE section inside the file to choose the most appropriate usage according to the goal of the challenge. At the moment, the default option performs a training on the input set with cross-validation on some of the classifier parameters. It usually requires a few minutes to run. It is also provided a fast version with uses, for the parameters above, the best value found training on the test case: of course it will have lower precision and recall in comparison to the regular "anew" classification.
A "thorough" mode is also provided: in this case a bigger set of values will be cross-validated for each parameter, and it will also be used Principal Component Analysis to reduce the number of features (with the number of features kept learned itself through cross-validation).
Finally, 'tree' and 'logistic' mode are available to use Tree Decision Classifiers or Logistic Regression instead of SVMs as classifiers.

The solution provided is based on the scikit-learn libsvm implementation.
The learning algorithm used is a Support Vector Machine Classifier with rbf Kernel; the input's features are normalized before being passed to SVC, but to avoid data snooping the scaling is decided on a separated subset of the input (about 10% of the input) that isn't used anymore in cross validation (when in thorough mode, PCA is performed as well only on this subset, again to avoid data snooping).
Cross validation is performed on gamma and C parameters: gamma controls how far the influence of a single point extends (low values meaning far, high values close) while C controls the "hardness" of the SVM's margin (the higher the value of C the hardest the margin, hence SVM gives better Ein, but worse generalization).

If the train set is very large, SVM might not be the best choice and logistic regression could be a valid alternative; a function that perform logistic regression instead of SVC is provided as well (option -m logistic).

A possible further solution could be to use aggregation, and then train different types of classifiers, or several different SVM with higher/softer margins, but experiments in that direction haven't shown significant improvements.

6.: Data center Cooling (ANSI C)

The best solution I got so far, requires around 21 seconds on a 2GHz Quad core, Windows 7 operative system, using gcc compiler with -Ofast optimizing option, and 17 seconds on the same machine with a Visual C++ 2010 compiler.
I use backtracking with 2 pruning heuristics:
Checks that every not yet visited cell can be reached from the current configuration;
Checks that the goal cell can be reached from the current configuration.
The first heuristic alone gave an improvement of a factor 20 in comparison to naive backtracking, adding the second gave another factor 3, and then some code tuning allowed to cut a few more seconds.
23/06/2012:	Added a third heuristics that looks for culs-de-sac, i.e. free rooms surrounded on 3 sides by walls, busy rooms or rooms already used on the path: this gives an improvent of a factor 5 (under 5 seconds!).
			A little extra optimization bought it another second (less than 4 secs of total runtime).
