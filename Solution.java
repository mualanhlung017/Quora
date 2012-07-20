import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
//import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Arrays;
//import java.util.HashMap;
import java.util.HashSet;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

/**
 * 
 * @author mlarocca
 * 
 *         Requires JRE 1.7.0
 * 
 *         An instance of this class is intended to solve, beginning to end, the
 *         "Typehead Search" challenge from Quota Challenge page.
 */
public class Solution {

	// REGULAR EXPRESSIONS:
	private static final String INTEGER_RE = "[0-9]+"; // Matches any non
														// negative integer
	private static final String INTEGER_GROUP_RE = "(" + INTEGER_RE + ")"; // Group
																			// version
	private static final String FLOAT_RE = "[0-9]+(?:.[0-9]*)?"; // INVARIANT: always
															// positive
	private static final String FLOAT_GROUP_RE = "(" + FLOAT_RE + ")"; // Group
																		// version
	private static final String ID_RE = "\\w+"; // NOTE: we assume that
															// an ID must start
															// with a letter,
															// and can be
															// composed of
															// letters, numbers
															// and underscores
															// only
	private static final String ID_GROUP_RE = "(" + ID_RE + ")"; // Group
																	// version
	private static final String SEPARATOR_RE = "(?: |\\t)"; // We consider just spaces
													// as separators
	private static final String STRING_GROUP_RE = "(\\S*.*)"; // Strings starts
																// with a char
																// and can have
																// spaces
	private static final String COMMAND_RE = "(ADD)|(DEL)|(W?QUERY)"; // Matches
																		// all
																		// the 4
																		// possible
																		// command
																		// instructions
	private static final String COMMAND_GROUP_RE = "(" + COMMAND_RE + ")"
			+ SEPARATOR_RE + STRING_GROUP_RE; // Matches any command line,
												// grouping the command
	private static final String TYPE_RE = "user|topic|question|board"; // Matches
																		// one
																		// of
																		// the 4
																		// types
	private static final String TYPE_GROUP_RE = "(" + TYPE_RE + ")"; // Group
																		// version
	private static final String BOOST_GROUP_RE = "((?:" + TYPE_RE + "|(?:"
			+ ID_RE + ")):" + FLOAT_RE + SEPARATOR_RE + ")"; // Matches a boost
	private static final String TYPE_BOOST_RE = TYPE_GROUP_RE + ":"
			+ FLOAT_GROUP_RE; // Matches a "type" boost
	private static final String ID_BOOST_RE = ID_GROUP_RE + ":"
			+ FLOAT_GROUP_RE; // Matches an "id" boost

	// REGULAR EXPRESSIONS for the four possible command lines:
	// Add statements format: ADD <type> <id> <score> <data string that can
	// contain spaces>
	private static final String ADD_STMT_RE = "ADD" + SEPARATOR_RE
			+ TYPE_GROUP_RE + SEPARATOR_RE + ID_GROUP_RE + SEPARATOR_RE
			+ FLOAT_GROUP_RE + SEPARATOR_RE + STRING_GROUP_RE;
	// Del statements format: DEL <id>
	private static final String DEL_STMT_RE = "DEL" + SEPARATOR_RE
			+ ID_GROUP_RE;
	// Query statements format: QUERY <number of results > <query string that
	// can contain spaces>
	private static final String QUERY_STMT_RE = "QUERY" + SEPARATOR_RE
			+ INTEGER_GROUP_RE + SEPARATOR_RE + STRING_GROUP_RE;
	// WQuery statements format: WQUERY <number of results> <number of boosts>
	// (<type>:<boost>)* (<id>:<boost>)* <query string that can contain spaces>
	private static final String WQUERY_STMT_RE = "WQUERY" + SEPARATOR_RE
			+ INTEGER_GROUP_RE + SEPARATOR_RE + INTEGER_GROUP_RE + SEPARATOR_RE
			+ BOOST_GROUP_RE + "*+" + STRING_GROUP_RE;

	// PATTERNS (compiled only once to improve performance):
	private static final Pattern pAddCommand = Pattern.compile(ADD_STMT_RE);
	private static final Pattern pDelCommand = Pattern.compile(DEL_STMT_RE);
	private static final Pattern pQueryCommand = 
			Pattern.compile(QUERY_STMT_RE);
	private static final Pattern pWQueryCommand = 
			Pattern.compile(WQUERY_STMT_RE);
	private static final Pattern pTypeBoost = Pattern.compile(TYPE_BOOST_RE);
	private static final Pattern pIdBoost = Pattern.compile(ID_BOOST_RE);
	// Matches just the command string (any of the 4 legal commands)	
	private static final Pattern pCommand = Pattern.compile(COMMAND_GROUP_RE); 

	
	// DB and Output are stored as vectors
//	private static final PrefixTree prefixTree = new PrefixTree();
	private static final PatriciaTree prefixTree = new PatriciaTree();
	private static final Trie keyTrie = new Trie();
//	private static HashMap<String, Item> recordsMap;

	private static final ArrayList<Boost> typeBoosts = new ArrayList<Boost>(26);
	private static final ArrayList<Boost> idBoosts = new ArrayList<Boost>(26);

	// The collected while commands are inserted from stdin but printed
	// only once all commands have been completed

	/**
	 * Main method: handles IO and, for each line inserted from System.in, calls the
	 * right function to process the command.
	 * When all the input has been read and processed, outputs the results of the queries on System.out
	 * 
	 * @param args:	Possible arguments for the class (none processed at the
	 *            moment).
	 */
	public static void main(String[] args) throws IOException {
		BufferedReader in = new BufferedReader(new InputStreamReader(System.in));
		String inputLine;
		String command;
		int N;		//Number of commands to expect from the input
		int counter = 0;

		if ((inputLine = in.readLine()) == null || inputLine.length() == 0) {
			throw new Error(
					"Bad formatted input: need to insert the number of commands first");
		} else {
			// INVARIANT: input is inserted correctly formatted according to
			// challenge specs
			N = Integer.parseInt(inputLine);
		}

//		recordsMap = new HashMap<String, Item>(N/2, 0.5f);
		
		while (counter++ < N) {
			// Tries to read N lines
			inputLine = in.readLine();
			// INVARIANT: input is inserted correctly formatted according to
			// challenge specs
			Matcher commandMatcher = pCommand.matcher(inputLine);
			commandMatcher.matches();
			command = commandMatcher.group(1);

			if (command.equals("ADD")) {
				processAddCommand(inputLine);
			}else if (command.equals("DEL")) {
				processDelCommand(inputLine);
			}else if (command.equals("QUERY")) {
				//output.add(
				processQueryCommand(inputLine);
			}else if (command.equals("WQUERY")) {
				//output.add(
				processWQueryCommand(inputLine);
			}
			// WARNING: An empty line or Ctrl-Z terminates the program without
			// producing any output!!!
		}

		// Prints the generated output on standard output
		//for (String s:output) {
		//	System.out.println(s);
		//}

		//DEBUG://printDB();
	}

	/**
	 * Takes an ADD command line and, if everything is properly formatted,
	 * performs the insertion of a new element in the DB.
	 * 
	 * @param addCommand:	The command line, as received from the input.
	 */
	private static void processAddCommand(String addCommand) {

		Matcher commandMatcher = pAddCommand.matcher(addCommand);
		commandMatcher.matches();
		//String type = ;
		//String id = ;
		//float score = ;
		//String data = ;
		//Keeps record sorted
		String id = commandMatcher.group(2);
		Item newItem = new Item(commandMatcher.group(1), id, Float.parseFloat(commandMatcher.group(3)), commandMatcher.group(4));
//		recordsMap.put(id, newItem);
		keyTrie.insertString(id, newItem);
		
		for (String s: newItem.data){
			prefixTree.insertString(s, newItem);
		}
//		printDB();
//		System.out.println("-----------------------------");
	}

	/**
	 * Takes a DEL command line and, if everything is properly formatted,
	 * performs the deletion of the element with the given ID from the DB.
	 * 
	 * @param delCommand: 	The command line, as received from the input.
	 */
	private static void processDelCommand(String delCommand) {

		Matcher commandMatcher = pDelCommand.matcher(delCommand);
		commandMatcher.matches();
		String id = commandMatcher.group(1);

//		Item item = recordsMap.get(id);
		Item item = keyTrie.search(id);
		for (String s: item.data){
			prefixTree.removeString(s, item);
		}
		//keyTrie.removeKey(id);
		// INVARIANT: all requests are legitimate, so execution should never
		// reach this point.
		// At the moment ignores possible unlegitimate ones (should throw
		// exception on id not found?)
	}

	/**
	 * Takes a QUERY command line and, if everything is properly formatted,
	 * performs the required query on the DB. To improve performance, while
	 * examining the DB for data matching the query, only the best n results are
	 * kept in a sorted vector, where n is the maximum number of results
	 * accepted by the query (specified in the command line).
	 * 
	 * @param queryCommand:	The command line, as received from the input;
	 * @return: A string containing the list of the IDs matching the query,
	 *          separated by spaces, and sorted according to: 1) Score 2)
	 *          Creation time (when there is a tie on the score, most recents
	 *          elements go first)
	 */
	private static void processQueryCommand(String queryCommand) {

		Matcher commandMatcher = pQueryCommand.matcher(queryCommand);
		commandMatcher.matches();
		int numberOfResults = Integer.parseInt(commandMatcher.group(1));
		if (numberOfResults == 0){
			System.out.println("");
			return;
		}
		
		String queryString = commandMatcher.group(2);
		String[] tokens = queryString.toLowerCase().split(SEPARATOR_RE); // INVARIANT:
																		// Search
																		// is
																		// case
																		// insensitive
		//SortedVector<Item> resultsVector = new SortedVector<Item>();
		Item[] resultsHeap = new Item[numberOfResults];

		int heapSize = 0, i;
		int pos, childPos, rightPos, parentPos;
		
		//resultsVector.setMaxSize(numberOfResults);
		try{
			for (Item item : prefixTree.search(tokens)) {
				
				if (heapSize == numberOfResults){
									
					if (item.score < resultsHeap[0].score){
						//This item is too big for the queue
						continue;
					}	
					
	
					// Creates a new item with the proper score, given by the
					// original item's score multiplied by the boost that can be
					// applied.
					
	                pos = 0;
	                // Bubble up the greater child until hitting a leaf.
	                childPos = 2 * pos + 1;    // leftmost child position
	                while (childPos < heapSize){
	                    // Set childpos to index of greater child.
	                    rightPos = childPos + 1;
	                    if (rightPos < heapSize && resultsHeap[childPos].compareTo(resultsHeap[rightPos]) < 0){
	                        childPos = rightPos;
	                    }
	                    // Move the greater child up.
	                    if (resultsHeap[childPos].compareTo(item) < 0){
	                    	break;
	                    }
	                    
	                    resultsHeap[pos] = resultsHeap[childPos];
	                    
	                    pos = childPos;
	                    childPos = 2*pos + 1;
	                }
	                resultsHeap[pos] = item; 			      
				}else {
					// Creates a new item with the proper score, given by the
					// original item's score multiplied by the boost that can be
					// applied.
					
	                resultsHeap[heapSize] = item;
	                pos = heapSize++;
	                // Follow the path to the root, moving parents down until it finds a place
	                // where new_item fits.
	                while (pos > 0){
	                    parentPos = (pos - 1) >> 1;
	                    if (item.compareTo(resultsHeap[parentPos]) > 0){
	                        resultsHeap[pos] = resultsHeap[parentPos];
	                        pos = parentPos;
	                    }else {
	                        break;
	                    }
	                }
	                resultsHeap[pos] = item;	                
										      
				}				
			}
		}catch(NullPointerException e){
			System.out.println("");
			return;
		}
		
		if (heapSize == 0){
			System.out.println("");
			return;
		}

		Arrays.sort(resultsHeap, 0, heapSize);	

		// Creates the output string
		StringBuilder out = new StringBuilder();
		for (i=0; i<heapSize-1; i++) {
			Item item = resultsHeap[i];
			out.append(item.id);
			out.append(" ");
		}
		Item item = resultsHeap[i];
		out.append(item.id);		
		System.out.println(out.toString());
	}

	/**
	 * Takes a WQUERY command line and, if everything is properly formatted,
	 * performs the required query on the DB. Weighted queries requires a few
	 * extra steps than regular queries: 
	 * 		1) 	Boost criteria must be identified from the command line;
	 * 		2) 	For every record in the DB matching the query string, the
	 * 			weighted score must be computed.
	 * 
	 * To improve performance, while examining the DB for data matching the
	 * query, only the best n results are kept in a sorted vector, where n is
	 * the maximum number of results accepted by the query (specified in the
	 * command line). Since a different score must be computed for each wquery
	 * and DB elements' score shouldn't be modified, for each matching record a
	 * new Item object is created, inheriting all attributes from the original
	 * one but the score, which is instead computed as the weighted version
	 * according to the query's boosts factors. An alternative could have been
	 * creating coupling each Item with its weight factor or weighted score, and
	 * defining a different external comparison methods for Entities, but,
	 * besides violating encapsulation and complicating the design, the benefits
	 * of this approach wouldn't be clearly significant.
	 * 
	 * @param wqueryCommand: The command line, as received from the input;
	 * @return: A string containing the list of the IDs matching the query,
	 *          separated by spaces, and sorted according to: 
	 *          		1) 	Score 
	 *          		2)	Creation time (when there is a tie on the score, 
	 *          			most recent elements go first)
	 */
	private static void processWQueryCommand(String wqueryCommand) {

		Matcher commandMatcher = pWQueryCommand.matcher(wqueryCommand);
		commandMatcher.matches();
		Matcher boostMatcher;

		int numberOfResults = Integer.parseInt(commandMatcher.group(1));		
		if (numberOfResults == 0){
			System.out.println("");
			return;
		}
		
		int i_numberOfBoosts = Integer.parseInt(commandMatcher.group(2));

		// (boost)* captures as a group only the last occurence of boost, so we
		// need to take the substring from the end of the previous group
		// to the end of the last occurrence of a boost
		if (i_numberOfBoosts > 0) {
			idBoosts.clear();
			typeBoosts.clear();
			// INVARIANT: Input is well formed, so the third group exists and
			// matches the last boost in the input line.
			String[] as_boosts = wqueryCommand.substring(
					commandMatcher.end(2) + 1, commandMatcher.end(3)).split(SEPARATOR_RE);

			// Additional check (redundant assuming the input is well formatted)
			/*if (as_boosts.length != i_numberOfBoosts) {
				throw new Error(
						"Bad formatted input: please check the challenge specifications for WQUERY commands");
			}*/

			int counter = 0;
			// Creates the lists of boosts
			// INVARIANT: According to specifications, first comes type-boosts,
			// and then id-boosts, but they are not mixed with each other.
			while (counter < i_numberOfBoosts
					&& (boostMatcher = pTypeBoost.matcher(as_boosts[counter]))
							.matches()) {
				counter++;
				typeBoosts.add(new Boost(boostMatcher.group(1), Float.parseFloat(boostMatcher.group(2))));
			}

			while (counter < i_numberOfBoosts) {
				boostMatcher = pIdBoost.matcher(as_boosts[counter]);
				boostMatcher.matches();
				// INVARIANT: types descriptor are reserved words and so they can't
				// appear as IDs
				/*if (pTypeBoost.matcher(as_boosts[counter]).matches()){
					throw new Error(
							"Bad formatted input: types are reserved words and can't " +
							"be used as ID; Please check the challenge specifications " +
							"for WQUERY commands");					
				}*/
				counter++;
				idBoosts.add(new Boost(boostMatcher.group(1), Float.parseFloat(boostMatcher.group(2))));
			}

			// Additional check (redundant assuming the input is well formatted)
			/*if (counter != i_numberOfBoosts) {
				throw new Error(
						"Bad formatted input: please check the challenge specifications for WQUERY commands");
			}*/
		}

		String queryString = commandMatcher.group(4);
		String[] tokens = queryString.toLowerCase().split(SEPARATOR_RE); 
		// INVARIANT: Search is case insensitive

		ItemResult[] resultsHeap = new ItemResult[numberOfResults];
		
		int heapSize = 0, i;
		int pos, childPos, rightPos, parentPos;
		
		try{
			for (Item item : prefixTree.search(tokens)) {
	
				if (heapSize == numberOfResults){
					
					// Computes the boost factor first
					float mul = 1.0f;
					for (Boost boost : typeBoosts) {
						if (item.type.equals(boost.pattern)) {
							mul *= boost.mul;
							// INVARIANT: assuming each type boost can match only once
							break;
						}
					}
					for (Boost boost : idBoosts) {
						if (item.id.equals(boost.pattern)) {
							mul *= boost.mul;
							// INVARIANT: assuming each ID boost can match only once
							break;
						}
					}
					
					if (item.score * mul < resultsHeap[0].score){
						//This item is too big for the queue
						continue;
					}	
					
					// Creates a new item with the proper score, given by the
					// original item's score multiplied by the boost that can be
					// applied.
					
					ItemResult itemR = new ItemResult(item.id, item.score * mul, item.creationTime);
				
	                pos = 0;
	                // Bubble up the greater child until hitting a leaf.
	                childPos = 2 * pos + 1;    // leftmost child position
	                while (childPos < heapSize){
	                    // Set childpos to index of greater child.
	                    rightPos = childPos + 1;
	                    if (rightPos < heapSize && resultsHeap[childPos].compareTo(resultsHeap[rightPos]) < 0){
	                        childPos = rightPos;
	                    }
	                    // Move the greater child up.
	                    if (resultsHeap[childPos].compareTo(itemR) < 0){
	                    	break;
	                    }
	                    
	                    resultsHeap[pos] = resultsHeap[childPos];
	                    
	                    pos = childPos;
	                    childPos = 2*pos + 1;
	                }
	                resultsHeap[pos] = itemR; 			      
				}else {
					//The Heap isn't full yet
					
					// Computes the boost factor first
					float mul = 1.0f;
					for (Boost boost : typeBoosts) {
						if (item.type.equals(boost.pattern)) {
							mul *= boost.mul;
							// INVARIANT: assuming each type boost can match only once
							break;
						}
					}
					for (Boost boost : idBoosts) {
						if (item.id.equals(boost.pattern)) {
							mul *= boost.mul;
							// INVARIANT: assuming each ID boost can match only once
							break;
						}
					}
				
					// Creates a new item with the proper score, given by the
					// original item's score multiplied by the boost that can be
					// applied.
					
					ItemResult itemR = new ItemResult(item.id, item.score * mul, item.creationTime);
	                resultsHeap[heapSize] = itemR;
	                pos = heapSize++;
	                // Follow the path to the root, moving parents down until it finds a place
	                // where new_item fits.
	                while (pos > 0){
	                    parentPos = (pos - 1) >> 1;
	                    if (itemR.compareTo(resultsHeap[parentPos]) > 0){
	                        resultsHeap[pos] = resultsHeap[parentPos];
	                        pos = parentPos;
	                    }else {
	                        break;
	                    }
	                }
	                resultsHeap[pos] = itemR;	                
										      
				}				
			}
		}catch(NullPointerException e){
			System.out.println("");
			return;
		}
		
		if (heapSize == 0){
			System.out.println("");
			return;
		}

		Arrays.sort(resultsHeap, 0, heapSize);	
		
		// Creates the output string
		StringBuilder out = new StringBuilder();
		for (i=0; i<heapSize-1; i++) {
			ItemResult item = resultsHeap[i];
			out.append(item.id);
			out.append(" ");
		}
		ItemResult item = resultsHeap[i];
		out.append(item.id);		
		System.out.println(out.toString());
	}


	
	private static class PatriciaTree{

		private static class PatriciaTreeNode{
			private String label;
			
			public PatriciaTreeNode(){
				
			}
			
			public PatriciaTreeNode(String l, Item item){
				this.label = l;
				this.items.add(item);
			}
			
			@SuppressWarnings("unchecked")
			public PatriciaTreeNode(String label, ArrayList<PatriciaTreeNode> childrenReference, HashSet<Item> items){
				this.label = label;
				this.children = childrenReference;
				this.items = (HashSet<Item>)(items.clone());
			}

			private ArrayList<PatriciaTreeNode> children = new ArrayList<PatriciaTreeNode>();
			private HashSet<Item> items = new HashSet<Item>();
			
			public PatriciaTreeNode search(String s){
				int l = 0, r = children.size()-1, pos = 0;
				char tmp_c, c;
				try{
					c = s.charAt(0);
				}catch(StringIndexOutOfBoundsException e){
					return null;
				}
				while (l <= r){
					pos = (l+r)/2;
					PatriciaTreeNode child = children.get(pos);
					String label = child.label;
					int l_len = label.length();
					tmp_c = label.charAt(0);
					if (tmp_c == c){
						int i = 1;
						int s_len = s.length();
						
						int n = Math.min(s_len, l_len);
						for (; i < n; i++){
							if (s.charAt(i) != label.charAt(i)){
								break;
							}
						}
						if (i == s_len){
							return child;
						}else if (i == l_len){
							return child.search(s.substring(i));
						}else{
							return null;
						}
					}else if (tmp_c < c){
						l = pos + 1;
					}else{
						r = pos - 1;
					}
				}

				return null;
			}

			
			public void insertChild(String s, Item item){
				int size = children.size(), l = 0, r = size - 1, pos = 0;
				int s_len = s.length();
				char tmp_c, c;
				try{
					c = s.charAt(0);
				}catch(StringIndexOutOfBoundsException e){
					return ;
				}
				while (l <= r){
					pos = (l+r)/2;
					PatriciaTreeNode child = children.get(pos);
					String label = child.label;
					int l_len = label.length();
					
					tmp_c = label.charAt(0);
					if (tmp_c == c){
						
						int n = Math.min(l_len, s_len);
						int i = 1;
						for (; i < n; i++){
							if (label.charAt(i) != s.charAt(i)){
								break;
							}
						}
						if (i < l_len){
							String restOfl = label.substring(i);
							child.label = s.substring(0, i);
							
							PatriciaTreeNode new_child = new PatriciaTreeNode(restOfl, child.children, child.items);
							child.children = new ArrayList<PatriciaTreeNode>(2);	//old var has exausted its life
							child.children.add(new_child);
							child.items.add(item);
							if (i < s_len){
								String restOfs = s.substring(i);
								new_child = new PatriciaTreeNode(restOfs, item);
								if ( restOfl.compareTo(restOfs) < 0){
									child.children.add(new_child);
								}else{
									child.children.add(0, new_child);
								}
							}
						}else if (i < s_len){
							child.items.add(item);
							String restOfs = s.substring(i);
							child.insertChild(restOfs, item);
						}else{
							child.items.add(item);
						}
						return ;
					}else if (tmp_c < c){
						l = pos + 1;
					}else{
						r = pos - 1;
					}
				}

				
				PatriciaTreeNode node = new PatriciaTreeNode(s, item);
				this.children.add(l, node);
				return ;
			}
			
			public void removeItem(String s, Item item){
				int l = 0, r = children.size()-1, pos = 0;
				char tmp_c, c;
				try{
					c = s.charAt(0);
				}catch(StringIndexOutOfBoundsException e){
					return ;
				}
				while (l <= r){
					pos = (l+r)/2;
					PatriciaTreeNode child = children.get(pos);
					String label = child.label;
					int l_len = label.length();
					tmp_c = label.charAt(0);
					if (tmp_c == c){
						child.items.remove(item);
						int i = 1;
						int s_len = s.length();
						
						int n = Math.min(s_len, l_len);
						for (; i < n; i++){
							if (s.charAt(i) != label.charAt(i)){
								break;
							}
						}
						if (i == l_len && i < s_len){
							child.removeItem(s.substring(i), item);
							return ;
						}else{
							return ;
						}
					}else if (tmp_c < c){
						l = pos + 1;
					}else{
						r = pos - 1;
					}
				}

			}
		}
		
		private PatriciaTreeNode root = new PatriciaTreeNode();
		
		public void insertString(String label, Item item){
			root.insertChild(label, item);
		}

		public void removeString(String s, Item item){
			root.removeItem(s, item);
		}
		
		public HashSet<Item> search(String s){
			try {
				return root.search(s).items;
			}catch(NullPointerException e){
				return null;
			}
		}
		
		public HashSet<Item> search(String[] sArray){
			HashSet<Item> results, tmp_result, tmp;
			try{
				results = search(sArray[0]);
			}catch(IndexOutOfBoundsException e){
				return null;
			}
			
			int n = sArray.length;
			for (int i = 1; i < n; i++){
				try{
					if (results.isEmpty()){
						return results;
					}
					tmp_result = search(sArray[i]);
					tmp = new HashSet<Solution.Item>(results.size());
					for (Item item: tmp_result){
						if (results.contains(item)){
							tmp.add(item);
						}
					}
					results = tmp;				
				}catch(NullPointerException e){
					return null;
				}
			}
			return results;
		}

	
	}	
	
	

	
	private static class Trie{

		private static class TrieNode{
			private char c;
			private final ArrayList<TrieNode> children = new ArrayList<TrieNode>();
			private Item item = null;
			
			
			public TrieNode(){
				
			}
			
			public TrieNode(char c){
				this.c = c;
			}
			
			public TrieNode search(char c){
				int l = 0, r = children.size()-1, pos = 0;
				char tmp_c;
				while (l <= r){
					pos = (l+r)/2;
					tmp_c = children.get(pos).c;
					if (tmp_c == c){
						return children.get(pos);
					}else if (tmp_c < c){
						l = pos + 1;
					}else{
						r = pos - 1;
					}
				}

				return null;
			}

			
			public TrieNode insertChild(char c){
				int size = children.size(), l = 0, r = size - 1, pos = 0;
				char tmp_c;
				while (l <= r){
					pos = (l+r)/2;
					TrieNode child = children.get(pos);
					tmp_c = child.c;
					if (tmp_c == c){
						return child;
					}else if (tmp_c < c){
						l = pos + 1;
					}else{
						r = pos - 1;
					}
				}

				TrieNode node = new TrieNode(c);
				this.children.add(l, node);
				return node;
			}
			
			public void setItem(Item item){
				this.item = item;
			}
/*			
			public void removeItem(Item item){
				item = null;
			}
*/
		}
		
		private TrieNode root = new TrieNode();
		
		public void insertString(String s, Item item){
			char[] cArray = s.toCharArray();
			TrieNode node = root;
			for (char c: cArray){
				node = node.insertChild(c);
			}
			node.setItem(item);
		}

		/*
		public void removeKey(String s, Item item){
			char[] cArray = s.toCharArray();
			TrieNode node = root;
			for (char c: cArray){
				node = node.search(c);
			}
			node.removeItem(item);
		}*/
		
		public Item search(String s){
			char[] cArray = s.toCharArray();
			TrieNode node = root, child;
			for (char c: cArray){
				try{
					child = node.search(c);
					node = child;
				}catch(NullPointerException e){
					return null;
				}
			}
			return node.item;			
		}
		
	}	
	
	/**
	 * class Item
	 * 
	 * @author mlarocca 
	 * Models an item (either a topic, an user, a board or a
	 *        question) stored in the local DB.
	 * 
	 */
	private static class Item implements Comparable<Item> {
		protected String type;
		protected String id;
		protected float score;
		protected final String[] data;
		private int creationTime;

		private static int time = 0;

		/**
		 * Constructor: copy the attributes of the item from the input
		 * parameters and inits the creation time according to a private
		 * 'clock'. The attributes are designed as 'final', and so there is no
		 * setter available to change their values.
		 * 
		 * @param type
		 *            : The item's type;
		 * @param id
		 *            : The item's ID;
		 * @param score
		 *            : The score associated to the item;
		 * @param data
		 *            : The data associated to the item.
		 */
		public Item(String type, String id, float score, String data) {
			// INVARIANT: ID are unique
			this.type = type;
			this.id = id;
			this.score = score;

			this.data = data.toLowerCase().split(SEPARATOR_RE);
			//Arrays.sort(this.data);
			this.creationTime = ++time; 	// Keeps track of the creation time
											// to make it easy to check which of
											// two Entities is newer
		}


		/**
		 * Implemented to achieve compatibility with Comparable Interface. Items
		 * are ordered according to the following criteria: 1) Score: higher
		 * score means lower (better) rank; 2) Novelty: when two items have the
		 * same score, the newest has lower (better) rank.
		 * 
		 * @param o_i_other: the item to be compared to;
		 * @return: An int indicating which of the two items has lower rank: -
		 *          If the returned value is <0, it is this item; - If the
		 *          returned value is >0, it is the other item; - The case in
		 *          which the two items have the same rank is not possible.
		 */
		@Override
		public int compareTo(Item other) {
			if (this.score > other.score) {
				return -1; // Highest score "wins"
			} else if (this.score < other.score) {
				return 1;
			} else {
				return other.creationTime - this.creationTime;
			}
		}

		/**
		 * Utility function: prints the item in an informative format to a
		 * specific PrintStream.
		 * 
		 * @param out:	The output stream on which the data has to be printed.
		private void print(PrintStream out) {
			out.println("ID: " + this.id + " of type " + this.type);
			out.println("\t creation time: " + this.creationTime
					+ "; score: " + this.score);
			out.println("\t " + this.data);
		}
		 */

	}
		
	/**
	 * class Item
	 * 
	 * @author mlarocca 
	 * Models an item (either a topic, an user, a board or a
	 *        question) stored in the local DB.
	 * 
	 */
	private static class ItemResult implements Comparable<ItemResult> {
		protected String id;
		protected float score;
		private int creationTime;

		/**
		 * Constructor: copy the attributes of the item from the input
		 * parameters and inits the creation time according to a private
		 * 'clock'. The attributes are designed as 'final', and so there is no
		 * setter available to change their values.
		 * 
		 * @param type
		 *            : The item's type;
		 * @param id
		 *            : The item's ID;
		 * @param score
		 *            : The score associated to the item;
		 * @param data
		 *            : The data associated to the item.
		 */
		public ItemResult(String id, float score, int creationTime) {
			// INVARIANT: ID are unique

			this.id = id;
			this.score = score;
			this.creationTime = creationTime;
		}


		/**
		 * Implemented to achieve compatibility with Comparable Interface. Items
		 * are ordered according to the following criteria: 1) Score: higher
		 * score means lower (better) rank; 2) Novelty: when two items have the
		 * same score, the newest has lower (better) rank.
		 * 
		 * @param o_i_other: the item to be compared to;
		 * @return: An int indicating which of the two items has lower rank: -
		 *          If the returned value is <0, it is this item; - If the
		 *          returned value is >0, it is the other item; - The case in
		 *          which the two items have the same rank is not possible.
		 */
		@Override
		public int compareTo(ItemResult other) {
			if (this.score > other.score) {
				return -1; // Highest score "wins"
			} else if (this.score < other.score) {
				return 1;
			} else {
				return other.creationTime - this.creationTime;
			}
		}


	}
	

	/**
	 * class Boost
	 * 
	 * @author mlarocca Models a pair composed by a String and a float, in order
	 *         to represent a generic boost (either a type boost or an ID
	 *         boost).
	 */
	private static class Boost {
		private String pattern;
		private float mul;

		/**
		 * Constructor: inits the Boost's attributes
		 * 
		 * @param pattern: 	The string pattern that specify when the 
		 * 					boost should be applied;
		 * @param multiplier: The score boost factor.
		 */
		public Boost(String pattern, float multiplier) {
			this.pattern = pattern;
			this.mul = multiplier;
		}
	}
}