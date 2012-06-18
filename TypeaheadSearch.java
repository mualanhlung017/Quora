//package mlr.dev.challenges;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.util.Vector;
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
public class TypeaheadSearch {

	// REGULAR EXPRESSIONS:
	private static final String INTEGER_RE = "[0-9]+"; // Matches any non
														// negative integer
	private static final String INTEGER_GROUP_RE = "(" + INTEGER_RE + ")"; // Group
																			// version
	private static final String FLOAT_RE = "[0-9]+.[0-9]*"; // INVARIANT: always
															// positive
	private static final String FLOAT_GROUP_RE = "(" + FLOAT_RE + ")"; // Group
																		// version
	private static final String ID_RE = "[A-Za-z]+\\w*"; // NOTE: we assume that
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
	private static final String STRING_GROUP_RE = "(\\S+.*)"; // Strings starts
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
	private static final Vector<Item> records = new Vector<>();
	private static final Vector<String> output = new Vector<>();
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

		while (counter++ < N && (inputLine = in.readLine()) != null
				&& inputLine.length() != 0) {
			// Tries to read N lines

			// INVARIANT: input is inserted correctly formatted according to
			// challenge specs
			Matcher commandMatcher = pCommand.matcher(inputLine);
			if (!commandMatcher.matches()) {
				throw new Error("Input error: Command not recognized");
			}
			command = commandMatcher.group(1);

			switch (command) {
			case "ADD":
				processAddCommand(inputLine);
				break;
			case "DEL":
				processDelCommand(inputLine);
				break;
			case "QUERY":
				output.add(processQueryCommand(inputLine));
				break;
			case "WQUERY":
				output.add(processWQueryCommand(inputLine));
				break;
			default:
				continue;
			}

			// WARNING: An empty line or Ctrl-Z terminates the program without
			// producing any output!!!
		}

		// Prints the generated output on standard output
		for (String s:output) {
			System.out.println(s);
		}

		//DEBUG://printDB();
	}

	// DEBUG
	/**
	 * Utility method to print all the entities stored at any moment
	 */
	@SuppressWarnings("unused")
	private static void printDB() {
		for (Item e : records) {
			e.print(System.out);
		}
	}

	/**
	 * Takes an ADD command line and, if everything is properly formatted,
	 * performs the insertion of a new element in the DB.
	 * 
	 * @param addCommand:	The command line, as received from the input.
	 */
	private static void processAddCommand(String addCommand) {

		Matcher commandMatcher = pAddCommand.matcher(addCommand);
		if (!commandMatcher.matches()) { // Additional check (redundant assuming the input is
							// well formatted)
			throw new Error(
					"Bad formatted input: please check the challenge specifications for ADD commands");
		}

		String type = commandMatcher.group(1);
		String id = commandMatcher.group(2);
		float score = Float.parseFloat(commandMatcher.group(3));
		String data = commandMatcher.group(4);

		Item rec = new Item(type, id, score, data);
		records.add(rec);
	}

	/**
	 * Takes a DEL command line and, if everything is properly formatted,
	 * performs the deletion of the element with the given ID from the DB.
	 * 
	 * @param delCommand: 	The command line, as received from the input.
	 */
	private static void processDelCommand(String delCommand) {

		Matcher commandMatcher = pDelCommand.matcher(delCommand);
		if (!commandMatcher.matches()) { // Additional check (redundant assuming the input is
							// well formatted)
			throw new Error(
					"Bad formatted input: please check the challenge specifications for DEL commands");
		}
		String id = commandMatcher.group(1);

		for (Item e : records) {
			// INVARIANT: ID are unique
			if (e.getID().equals(id)) {
				records.remove(e);
				return;
			}
		}
		// INVARIANT: all requests are legitimate, so execution should never
		// reach this point.
		// At the moment ignores possible illegitimate ones (should throw
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
	private static String processQueryCommand(String queryCommand) {

		Matcher commandMatcher = pQueryCommand.matcher(queryCommand);
		if (!commandMatcher.matches()) { // Additional check (redundant assuming the input is
							// well formatted)
			throw new Error(
					"Bad formatted input: please check the challenge specifications for QUERY commands");
		}
		int numberOfResults = Integer.parseInt(commandMatcher.group(1));
		String resultsString = ""; // The string containing the results of the
									// query (the one that has to be returned)
		String queryString = commandMatcher.group(2);
		String[] tokens = queryString.toLowerCase().split(SEPARATOR_RE); // INVARIANT:
																		// Search
																		// is
																		// case
																		// insensitive
		String data;
		Boolean match;

		SortedVector<Item> resultsVector = new SortedVector<>();
		resultsVector.setMaxSize(numberOfResults);

		for (Item item : records) {
			data = item.getData();
			match = true;

			for (String token : tokens) {
				if (!data.toLowerCase().contains(token)) { 
					// INVARIANT: Search is case insensitive
					match = false;
					break;
				}
			}
			if (match) {
				resultsVector.add(item);
			}
		}
		for (Item item : resultsVector) {
			resultsString += item.getID() + " ";
		}
		// Removes the trailing space first
		return resultsString.substring(0, Math.max(resultsString.length() - 1, 0));
		// resultsVector.print(System.out);
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
	private static String processWQueryCommand(String wqueryCommand) {

		Matcher commandMatcher = pWQueryCommand.matcher(wqueryCommand);
		Matcher boostMatcher;
		Vector<Boost> vo_type_boosts = new Vector<>();
		Vector<Boost> vo_id_boosts = new Vector<>();

		if (!commandMatcher.matches()) { // Additional check (redundant assuming the
									// input is well formatted)
			throw new Error(
					"Bad formatted input: please check the challenge specifications for WQUERY commands");
		}
		int numberOfResults = Integer.parseInt(commandMatcher.group(1));
		int i_numberOfBoosts = Integer.parseInt(commandMatcher.group(2));

		// (boost)* captures as a group only the last occurence of boost, so we
		// need to take the substring from the end of the previous group
		// to the end of the last occurrence of a boost
		if (i_numberOfBoosts > 0) {
			// INVARIANT: Input is well formed, so the third group exists and
			// matches the last boost in the input line.
			String[] as_boosts = wqueryCommand.substring(
					commandMatcher.end(2) + 1, commandMatcher.end(3)).split(SEPARATOR_RE);

			// Additional check (redundant assuming the input is well formatted)
			if (as_boosts.length != i_numberOfBoosts) {
				throw new Error(
						"Bad formatted input: please check the challenge specifications for WQUERY commands");
			}

			int counter = 0;
			// Creates the lists of boosts
			// INVARIANT: According to specifications, first comes type-boosts,
			// and then id-boosts, but they are not mixed with each other.
			while (counter < i_numberOfBoosts
					&& (boostMatcher = pTypeBoost.matcher(as_boosts[counter]))
							.matches()) {
				counter++;
				vo_type_boosts.add(new Boost(boostMatcher.group(1), Float
						.parseFloat(boostMatcher.group(2))));
			}

			while (counter < i_numberOfBoosts
					&& (boostMatcher = pIdBoost.matcher(as_boosts[counter]))
							.matches()) {
				// INVARIANT: types descriptor are reserved words and so they can't
				// appear as IDs
				if (pTypeBoost.matcher(as_boosts[counter]).matches()){
					throw new Error(
							"Bad formatted input: types are reserved words and can't " +
							"be used as ID; Please check the challenge specifications " +
							"for WQUERY commands");					
				}
				counter++;
				vo_id_boosts.add(new Boost(boostMatcher.group(1), Float
						.parseFloat(boostMatcher.group(2))));
			}

			// Additional check (redundant assuming the input is well formatted)
			if (counter != i_numberOfBoosts) {
				throw new Error(
						"Bad formatted input: please check the challenge specifications for WQUERY commands");
			}

		}
		String resultsString = ""; // The string containing the results of the
									// wquery (the one that has to be returned)
		String queryString = commandMatcher.group(4);
		String[] tokens = queryString.toLowerCase().split(SEPARATOR_RE); 
		// INVARIANT: Search is case insensitive
		String data;
		Boolean match;

		// Perform the query
		SortedVector<Item> resultsVector = new SortedVector<>();
		resultsVector.setMaxSize(numberOfResults);
		for (Item item : records) {
			data = item.getData();
			match = true;

			for (String token : tokens) {
				if (!data.toLowerCase().contains(token)) { 
					// INVARIANT: Search is case insensitive
					match = false;
					break;
				}
			}
			if (match) {
				// Computes the boost factor first
				float mul = 1.0f;
				for (Boost boost : vo_type_boosts) {
					if (item.getType().equals(boost.getPattern())) {
						mul *= boost.getMultiplier();
						// It is not clear if type boost would be unique (1
						// boost top for each type). In that case, break here.
					}
				}
				for (Boost boost : vo_id_boosts) {
					if (item.getID().equals(boost.getPattern())) {
						mul *= boost.getMultiplier();
						// It is not clear if id boost would be unique (1 boost
						// top for each id). In that case, break here.
					}
				}
				// Creates a new item with the proper score, given by the
				// original item's score multiplied by the boost that can be
				// applied.
				resultsVector.add(new Item(item.getType(), item.getID(), item
						.getScore() * mul, item.getData()));
			}
		}
		// Creates the output string
		for (Item item : resultsVector) {
			resultsString += item.getID() + " ";
		}
		// Removes the trailing space first
		return resultsString.substring(0, Math.max(resultsString.length() - 1, 0)); 
		// results.print(System.out);
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
		private String type;
		private String id;
		private float score;
		private String data;
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
			this.data = data;
			this.creationTime = ++time; 	// Keeps track of the creation time
											// to make it easy to check which of
											// two Entities is newer
		}

		/**
		 * Type getter
		 * 
		 * @return: The type of this item (either 'topic', 'user', 'board' or
		 *          'question').
		 */
		public String getType() {
			return this.type;
		}

		/**
		 * ID getter
		 * 
		 * @return: The ID of this item.
		 */
		public String getID() {
			return this.id;
		}

		/**
		 * Score getter
		 * 
		 * @return: The score associated with this item.
		 */
		public float getScore() {
			return this.score;
		}

		/**
		 * Data getter
		 * 
		 * @return: The data associated with this item.
		 */
		public String getData() {
			return data;
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
		 */
		private void print(PrintStream out) {
			out.println("ID: " + this.id + " of type " + this.type);
			out.println("\t creation time: " + this.creationTime
					+ "; score: " + this.score);
			out.println("\t " + this.data);
		}

	}

	/**
	 * Models a vector whose elements are kept ordered. On creation, a parameter
	 * must be passed to specify the maximum number of elements that can be
	 * stored in the newly created instance; when this number is reached, after
	 * every insertion the element with the work rank will be removed from the
	 * container, in order not to overcome this limit.
	 * 
	 * @author mlarocca
	 * 
	 * @param <T>: The container is modeled as a generic one, and it can contain
	 *        elements of any type T that is comparable.
	 */
	private static class SortedVector<T extends Comparable<T>> extends
																Vector<T> {

		private static final long serialVersionUID = 3889173077848756734L;

		private int maxSize = -1;

		/**
		 * Sets the maximum number of elements that this vector can contain.
		 * If this values is less than zero, no limit is considered.
		 * 
		 * @param maxSize: 	The maximum number of elements that this vector can
		 *            		contain.
		 */
		public synchronized void setMaxSize(int maxSize){
			this.maxSize = maxSize;
		}

		/**
		 * Adds an element to the container; the newly inserted element will be
		 * positioned in such a way that the container will maintain a proper
		 * order of its elements. 
		 * WARNING: If maxSize elements are already stored in this container, 
		 * 			then after the insertion the element with
		 * 			the worst rank will be removed.
		 * 
		 * @param element: The element to insert in the container.
		 */
		@Override
		public synchronized boolean add(T element) {

			int pos = 0;
			for (pos = 0; pos < this.size(); pos++) {
				if (element.compareTo(this.get(pos)) < 0) {
					break;
				}
			}
			
			// The limit on the maximim size is only valid if it is a positive integer,
			// otherwise it means that no limit is set.
			if (maxSize < 0 || pos < maxSize) {
				super.add(pos, element);
				// Now has to prune exceding elements
				if (maxSize >= 0 && this.size() > maxSize) {
					// INVARIANT: vector's size can be at most 1 + maxSize
					this.remove(maxSize);
				}
				return true;
			} else {
				return false;
			}

		}

		/**
		 * This method inherited by Vector class is deprecated and shouldn't be
		 * used: the index of the newly inserted element is decided according to
		 * its rank, and hence cannot be specified at insertion.
		 */
		@Deprecated
		@Override
		public synchronized void add(int index, T element) {
			throw new Error("This method is deprecated");
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
		String pattern;
		float mul;

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

		/**
		 * Pattern getter
		 * 
		 * @return: The string pattern.
		 */
		public String getPattern() {
			return this.pattern;
		}

		/**
		 * Score boost getter
		 * 
		 * @return: The boost factor to be applied to items' scores.
		 */
		public float getMultiplier() {
			return this.mul;
		}
	}

}
