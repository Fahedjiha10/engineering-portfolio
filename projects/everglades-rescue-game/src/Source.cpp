/*
Fahed Jiha
Kerweins Astre 
Intro to C++
Febuary 24,2023
---------------
EVERGLADES RPG GAME 
This File creates  5x5 matrix game in which the Ranger (r) objective is to save the tourist (t)
*/
// Import the necessary libraries
#include <iostream>
#include <string>
#include <cstdlib>
#include <ctime>
#include <iomanip>
using namespace std;


//Define Columns and Rows of the Matrix to be printed 
const int MAP = 5;


// Define the function prototypes that will be called when user selects an input 
void setGameRules();
void setDangersRandomly(int[][MAP]);
void dispMap(char[][MAP]);
int validateSelectedMove(int, int, int, int);
void inDanger(char[][MAP], int, int, int&, int&, int&, char&);

int main()
{
	// Define variables
	int menuChoice, row, col, error;
	int x = 0;
	int y = 0;

	string move = "\nEnter Next Cell(row & column): ";
	char ranger = 'R', tourist = 'T';

	// Define the logic of holding the Ranger location in the matric
	int key[MAP][MAP] = { {0,0,0,0,0},{0,0,0,0,0},{0,0,0,0,0},{0,0,0,0,0},{0,0,0,0,0} };

	// Define Game Title
	cout << "----------------------------------------" << endl;
	cout << "\tLOST IN EVERGLADES" << endl;
	cout << "----------------------------------------" << endl;


	do
	{
		// Define gong counter and game matrix
		int gong = 12;
		char everglades[MAP][MAP] = { {' ', '*', '*', '*', '*'},
										{'*', '*', '*', '*', '*'},
										{'*', '*', '*', '*', '*'},
										{'*', '*', '*', '*', '*'},
										{'*', '*', '*', '*', ' '}
		};

		// Display User Menu
		cout << "\nChoose one of the following options:" << endl
			<< "\n\t1. See Rules" << endl
			<< "\t2. Play Game" << endl
			<< "\t3. Quit" << endl
			<< "\n\tMy choice: ";
		cin >> menuChoice;

		switch (menuChoice)
		{

		case 1:
			// Print Game Rules
			setGameRules();
			break;

		case 2:

			cout << "\nGood luck finding the Tourist." << endl;

			// initialize placement (not even sure if this is a good idea)
			everglades[0][0] = ranger;
			everglades[4][4] = tourist;

			// Set the dangers
			setDangersRandomly(key);

			while (gong > 0)
			{
				// display map
				dispMap(everglades);
				cout << "\nGongs Left: " << gong << endl;

				// send input to validation function
				do
				{
					cout << move;
					cin >> row >> col;

					error = validateSelectedMove(row, col, x, y);

					if (error == 1)
						cout << "\nEntered cell is out of bounds. Please try again." << endl;
					else if (error == 2)
						cout << "\nEntered cell is not adjacent! Try again." << endl;

				} while (error != 0);

				// check for danger
				if (key[row][col] == 1)
					inDanger(everglades, row, col, gong, x, y, ranger);
				else
				{
					// if no danger, move ranger to cell and gong--
					everglades[row][col] = ranger;
					gong--;

					// update previous position
					everglades[x][y] = ' ';
					x = row;
					y = col;
					cout << "\nCell (" << row << "," << col << ") is free...you advance!\n" << endl;
				}

				// Probability of winning
				if (ranger == everglades[4][4])
				{
					for (int i = 0; i < 55; i++)
						cout << '*';
					cout << "\n*" << setw(15) << " " << "Congratulations, Ranger!" << setw(15) << '*'
						<< "\n* You found the lost tourists and led them to safety! *" << endl;
					for (int i = 0; i < 55; i++)
						cout << '*';
					cout << endl;
					break;
				}
			}

			// losing message
			if (gong <= 0 && ranger != everglades[4][4])
				cout << "\nSorry...you ran out of time." << endl;

			// reset ranger and tourist positions
			everglades[0][0] = ranger;
			everglades[4][4] = tourist;
			x = 0;
			y = 0;

			break;
		case 3:

			// quit
			cout << "\n------------------------------------------------" << endl;
			cout << "Thank you for playing lost in Everglades." << endl;
			cout << "------------------------------------------------" << endl;
			cout << "\n\n" << endl;
			break;
		default:

			// error
			cout << "\nERROR: Invalid selection. Please try again." << endl;
		}
	} while (menuChoice != 3);

	return 0;
}

void setDangersRandomly(int key[][MAP])
{
	// Define function local variables
	int danger = 1;
	int row, col;
	srand(time(NULL));

	// Generate 10 times to get the random locations
	for (int i = 0; i < 10; i++)
	{
		row = rand() % 4;
		col = rand() % 4;
		key[row][col] = danger;
	}
	return;
}


void setGameRules()
{

	// Set the title
	cout << "\n" << endl;

	for (int i = 1; i <= 100; i++)
		cout << '-';
	cout << endl;

	cout << setw(30);
	cout << "GAME RULES" << endl;

	for (int i = 1; i <= 100; i++)
		cout << '-';
	cout << endl;

	// Game Rules
	cout << "Hello Ranger!,"
		<< "\nA group of tourist got lost in the Everglades and need to be rescued"
		<< " before time runs out!" << endl;
	cout << "\nTo locate them, you need to use a map provided but beware of dangers along the way!" << endl;

	cout << "\nMany wild and dangerous creatures such as alligators, giant mosquitos,venemous spiders" << endl
		<< "and enormous pythons! are in the way. If you do encounter one of these dangers, you will " << endl;
	cout << "have two choices: (Fight or Wait.)"
		<< "\n\n\tCHOOSE TO WAIT => you will move to your desired cell but lose 5 gongs of time"
		<< "\n\tFIGHT AND WIN =>  you will move to your desired cell & lose 2 gongs of time"
		<< "\n\tFIGHT AND LOSE => you will not move, lose 3 gongs of time, and the danger will remain in the cell"
		<< "\n " << endl;

	cout << "\nThe game ends when either:" << endl
		<< "\t* The ranger rescues the group of tourists." << endl
		<< "\t* The time expires and the fate of the tourists is forever unknown." << endl;

	for (int i = 1; i <= 100; i++)
		cout << '-';
	cout << endl;
}


void dispMap(char ev[][MAP])
{
	// Print the matrix
	string ib = " | ";
	cout << "     0   1   2   3   4" << endl;
	for (int i = 0; i < MAP; i++) {
		cout << i << " " << ib;
		for (int j = 0; j < MAP; j++) {
			cout << ev[i][j] << ib;
		}
		cout << endl;
	}

	return;
}


int validateSelectedMove(int row, int col, int x, int y)
{
	int error;

	// if row is out of boundaries
	if (row < 0 || row > 4)
		error = 1;
	// if column is out of boundaries
	else if (col < 0 || col > 4)
		error = 1;
	// if row input is not adjacent
	else if (x < --row || x > ++row)
		error = 2;
	// if column input is not adjacent
	else if (y < --col || y > ++col)
		error = 2;
	else
		error = 0;

	return error;
}


void inDanger(char ev[][MAP], int row, int col, int& gong, int& x, int& y, char& pc)
{
	/* Since Danger is randomly placed in the matrix, generate a random number to pick (0,3)
	 to define the index that we will use to randomly select the danger in the array */
	srand(time(NULL));
	int danger = rand() % 3;
	string dName[] = { "Hungry Alligator", "Swarm of Giant Mosquitos", "Venemous Spider", "Python" };
	char icon[] = { 'A', 'M', 'S', 'P' };
	int move, outcome;

	// danger sequence
	cout << "\nWatch out! There is a " << dName[danger] << " ahead!" << endl
		<< "\nChoose your next move?\n\t1 - Wait until it leaves.\n\t2 - Fight it." << endl;

	// validate
	do
	{
		cout << "My Decision: ";
		cin >> move;

		if (move < 1 || move > 2)
		{
			cout << "\nInvalid choice. Please choose 1 or 2." << endl;
		}
	} while (move < 1 || move > 2);

	switch (move)
	{
	case 1:
		// wait
		cout << "\n... ... ...\n... ... ..." << endl
			<< "-----> The " << dName[danger] << " is gone...you advance!" << endl;
		gong = gong - 3;
		// update player position and previous position
		ev[row][col] = pc;
		ev[x][y] = ' ';
		x = row;
		y = col;
		break;
	case 2:
		// fight
		outcome = rand() % 2;

		//lost
		if (outcome == 0)
		{
			cout << "\nYou fought the " << dName[danger] << " and lost..." << endl
				<< "You'll have to retreat and find a way around." << endl;
			cout << "\n" << endl;
			gong = gong - 5;
			// update map with danger character
			ev[row][col] = icon[danger];
		}
		else
		{
			cout << "\nYou fought the " << dName[danger] << " and won! You advance." << endl;
			gong = gong - 2;
			// update player position and previous position
			ev[row][col] = pc;
			ev[x][y] = ' ';
			x = row;
			y = col;
		}
		break;
	}
	return;
}

