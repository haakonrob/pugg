# pugg (in progress)
Pugg is a Norwegian word meaning "to study", or "to memorise". This app helps facilitate this. 

## What it does
Pugg is a command line application that will parse your notes (assuming they're written in Markdown), extract blocks of text that you've marked, and convert them to flashcards that you can later review.

## How it does it
The application will walk the directory tree that you give it, passing any markdown files it finds through a pandoc filter that leaves only the notes that you've marked for review (see how below). It will then attempt to turn this into a flashcard with a front and back, at which point it is added to a database in the root directory (if it is not already in the database that is), where it is categorised using its path. For example, "notes/Mathematics/Linear Algebra/determinants.md" becomes ('Mathematics', 'Linear Algebra', 'determinants'). When the user wants to review their notes, they can specify a topic corresponding to some category, or they can specify nothing at all. The application will then select the relevant parts of the database and start quizzing the user on the lowest scoring cards it finds, updating the scores as it goes. 

## How do I use this
BLocks of text are marked for review by putting them inside a BlockQuote. This is done by putting a '>' at the start of each line. For example:
![How to mark some text for review](/images/basic_card.png)

Note that the front and the back of the card are separated by a single blank line. This is required! However, only the first blank line is used as a separator, the back part of the card can have as many blank lines as desired. 
*This might be changed to a horizontal rule, which is written as at 3+ dashes alone on a line, like ---.*  


## Motivation
Many existing apps use a flashcard system that lets you create multi-sided "cards" that you can then review later. Generally the app will present you with the front side of the card, at which point you try to remember the back of the card. You then let the app know if you where successful or not. Often the card is selected based on how well you've managed to remember it in the past, and how long its been since the last viewing, which means that the program can help you find the gaps in your knowledge and stenghten the "weakest links". This is an excellent system for studying, or maintaining your level of knowledge in some area. 

However, most of these apps require the user to interact with their cards one-by-one through some kind of GUI, which I personally find a bit clunky. The time it takes to click through, inspect, and edit individual cards tends to build up, especially when you start to accumulate hundreds, if not thousands of cards. Whenever I used these apps, I found myself wondering whether the time it took to convert my notes into reviewable flashcards would be better spent just reading my notes. Pugg is an attempt to make this process *convenient* by letting you review your notes instead of making lots of flashcards.
