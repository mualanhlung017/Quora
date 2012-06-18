// Quora_DC_Cooling.cpp : Defines the entry point for the console application.
//

#include <malloc.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#define CELL_LEN 2
#define CELL_START '2'
#define CELL_END '3'
#define CELL_EMPTY '0'
#define CELL_BUSY '1'
#define CELL_USED '*'
#define CELL_LOCKED '+'


typedef struct cell{
	unsigned int row;
	unsigned int col;
}CELL;

typedef struct stack_entry{
	unsigned int row;
	unsigned int col;
	char next_cell;
}STACK_ENTRY;

//Global variables are really really REALLY despised, an exception has been made just to seek maximum performance, after careful pros and cons evaluation,
//considering this is a standalone problem solver that is not going to end up in any module or library
CELL *_marked_cells = NULL;
STACK_ENTRY * _stack;
unsigned int W, H;
char **matrix;

/** Checks if there are cells in the matrix that cannot be reached from the current configuration
    Although it uses backtracking as well, this function is much faster than the main one because it doesn't distinguish among the
	differents ways to reach a cell, what matters is only if it can be reached: basically it is the same difference as between
	dispositions and combinations, and hence it is faster by a ratio of n! (if the matrix has n empty cells).
	By introducing this heuristic, the average speed on the sample problem gained a factor of 20!
	It also checks if the end cell can be reached - by introducing this check, it had another improvement by a factor of 3
	Reengineering it from recursive tu iterative style was worth a saving of a couple of seconds on the test case
	@param row - the current cell's row
	@param col - the current cell's col
	@param free_cells_left - how many cells are still free? This is decremented until it reaches 0 or there is no more cells to be examined are in the call stack queue
*/
char check_for_blocked_cells(unsigned int row, unsigned int col, unsigned int free_cells_left){
	unsigned int _marked_cells_size = 0;	//No cell has been marked yet

	char end_reached = 0;
	unsigned int queue_head = 0;


	do{
		

		//Checks surrounding cells, in the order: left, top, right, bottom
		if ( col > 0 && matrix[row][col-1] == CELL_EMPTY ){
			//Keeps track of the cell both to make the recursive call on it and to unmark it at the end of the recursion
			_marked_cells[_marked_cells_size].row = row;
			_marked_cells[_marked_cells_size++].col = col-1;

			//Mark the cell as used
			free_cells_left--;	
			matrix[row][col-1] = CELL_LOCKED;
		}else if ( col > 0 && matrix[row][col-1] == CELL_END ){
			//If there was a cell on the left but it wasn't free, checks if it is the goal cell (to understand if in this configuration the end point can be reached or not)
			end_reached = 1;
		}

		if (row > 0 && matrix[row-1][col] == CELL_EMPTY){
			_marked_cells[_marked_cells_size].row = row-1;						
			_marked_cells[_marked_cells_size++].col = col;

			free_cells_left--;
			matrix[row-1][col] = CELL_LOCKED;
		}else if (row > 0 && matrix[row-1][col] == CELL_END ){
			end_reached = 1;
		}

		if (col < W-1 && matrix[row][col+1] == CELL_EMPTY){
			_marked_cells[_marked_cells_size].row = row;
			_marked_cells[_marked_cells_size++].col = col+1;

			free_cells_left--;
			matrix[row][col+1] = CELL_LOCKED;
		}else if (col < W-1 && matrix[row][col+1] == CELL_END ){
			end_reached = 1;
		}

		if (row < H-1 && matrix[row+1][col] == CELL_EMPTY){
			_marked_cells[_marked_cells_size].row = row+1;						
			_marked_cells[_marked_cells_size++].col = col;

			free_cells_left--;
			matrix[row+1][col] = CELL_LOCKED;
		}else if (row < H-1 && matrix[row+1][col] == CELL_END ){
			end_reached = 1;
		}

		if ( free_cells_left == 0 && end_reached  || queue_head >= _marked_cells_size ){
			break;
		}
		row = _marked_cells[queue_head].row;	//Decrement the index first: being the size of the stack, it is 1 + the index of the last element
		col = _marked_cells[queue_head++].col;
		
	}while (  1  );


	for (queue_head=0; queue_head<_marked_cells_size; queue_head++){	//queue_head is not needed anymore, so we can reuse it
		//Unmark all marked cells
		matrix[_marked_cells[queue_head].row][_marked_cells[queue_head].col] = CELL_EMPTY;
	}
	
	return ! (free_cells_left == 0 && end_reached);

}


/**Start the backtracking search over the problem space
	Uses the recursion stack as the stack for the problem, modifying in place the world matrix
	(Since we just need to check if the nearby cells are free to use them, it marks each cell before entering it, runs the recursion over that cell,
	 and then, when the recursive call returns, unmark the cell, tries all the different remaining moves from the current cell, and then returns to the
	 previous recursive call)
*/
unsigned long backtrack(unsigned int row, unsigned int col,  unsigned int free_cells_left){
	unsigned long paths = 0;


	if (free_cells_left == 0){	//No more moves available: it can only check that a surrounding cell is the endpoint
		
		//Checks surrounding cells, in the order: left, top, right, bottom
		if ( (col > 0 && matrix[row][col-1] == CELL_END) || (row > 0 && matrix[row-1][col] == CELL_END)  || 
			 (col < W-1 && matrix[row][col+1] == CELL_END) || (row < H-1 && matrix[row+1][col] == CELL_END) ){
			//Found a valid path
			paths++;
		}
	}else if(check_for_blocked_cells(row, col, free_cells_left)){
		return 0;	//No valid path can be found from this configuration
	}
	else{
		//Checks surrounding cells, in the order: left, top, right, bottom
		if ( col > 0 && matrix[row][col-1] == CELL_EMPTY ){
			matrix[row][col-1] = CELL_USED;
			paths += backtrack(row, col-1, free_cells_left-1);
			matrix[row][col-1] = CELL_EMPTY;
		}

		if (row > 0 && matrix[row-1][col] == CELL_EMPTY){
			matrix[row-1][col] = CELL_USED;
			paths += backtrack(row-1, col, free_cells_left-1);
			matrix[row-1][col] = CELL_EMPTY;
		}

		if (col < W-1 && matrix[row][col+1] == CELL_EMPTY){
			matrix[row][col+1] = CELL_USED;
			paths += backtrack(row, col+1, free_cells_left-1);
			matrix[row][col+1] = CELL_EMPTY;
		}

		if (row < H-1 && matrix[row+1][col] == CELL_EMPTY){
			matrix[row+1][col] = CELL_USED;
			paths += backtrack(row+1, col, free_cells_left-1);
			matrix[row+1][col] = CELL_EMPTY;
		}
	}
	return paths;
}


int main(int argc, char* argv[])
{
	unsigned int i,j;
	unsigned int start_row, start_col;
	unsigned int free_cells;	//Used to understand if the recursion has come to an acceptable path (Unless W,H > 65535, an int will be fine)

	time_t start,end;
	float elapsedTime;

	scanf("%d %d\n", &W, &H);
	if (W<=0 || H<=0){
		printf("Error: The input is not properly formatted");
	}
	free_cells = W * H - 2;	//At the moment we suppose that all cells but start and end ones are free
	char *input_row = (char *)malloc(sizeof(char)*CELL_LEN*(W+2));	//Each cell is one char wide
	matrix = (char **) malloc(H * sizeof(char *));	//H rows

	for (i= 0; i<H; i++){
		matrix[i] = (char *) malloc(W*sizeof(char));
		fgets(input_row, sizeof(char)*CELL_LEN*(W+2), stdin);
		//INVARIANT: Cells must be separated by a single space
		for (j=0; j<W; j++){
			matrix[i][j] = input_row[2*j];
			//Now checks whether we can identify the start and goal state
			if (matrix[i][j] == CELL_START){
				start_row = i;
				start_col = j;
			}else if(matrix[i][j] == CELL_BUSY){
				free_cells -= 1;
			}
		}
	}

	//Alloc the memory for the stack of cells marked by one of the heuristics: only free_cells can be marked and pushed on this stack
	_marked_cells = (CELL *)malloc(free_cells*sizeof(CELL));
	//Alloc the memory for the stack of cells used by the heuristic
	_stack = (STACK_ENTRY *)malloc(free_cells*sizeof(STACK_ENTRY));

	time(&start);

	unsigned long paths = backtrack(start_row, start_col, free_cells);
	
	time(&end);
	elapsedTime = difftime(end,start);

	printf("%d",paths);
	
	for (i= 0; i<H; i++){
		free(matrix[i]);
	}
	free(matrix);
	free(input_row);
	free(_marked_cells);
	return 0;
}
