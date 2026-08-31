PRAGMA foreign_keys = ON;

-- Expand position 1: first word, based on first-name initial.
INSERT OR IGNORE INTO nickname_words (letter, word_position, word) VALUES
('A',1,'Awesome'),('A',1,'Astro'),('A',1,'Aqua'),('A',1,'Ace'),('A',1,'Angry'),('A',1,'Alley'),('A',1,'Alien'),
('B',1,'Blasty'),('B',1,'Bingo'),('B',1,'Bubble'),('B',1,'Banjo'),('B',1,'Boogie'),('B',1,'Blazing'),
('C',1,'Crazy'),('C',1,'Crispy'),('C',1,'Cheesy'),('C',1,'Clever'),('C',1,'Chaos'),('C',1,'Cotton'),('C',1,'Cranky'),
('D',1,'Danger'),('D',1,'Doodle'),('D',1,'Dragon'),('D',1,'Disco'),('D',1,'Dusty'),('D',1,'Daring'),
('E',1,'Epic'),('E',1,'Echo'),('E',1,'Emerald'),('E',1,'Exploding'),('E',1,'Eager'),
('F',1,'Fizzy'),('F',1,'Fluffy'),('F',1,'Flying'),
('G',1,'Goofy'),('G',1,'Golden'),('G',1,'Giant'),('G',1,'Gummy'),
('H',1,'Happy'),('H',1,'Hiccup'),('H',1,'Hero'),('H',1,'Hollow'),
('I',1,'Invisible'),('I',1,'Iron'),
('J',1,'Jumpy'),('J',1,'Jazzy'),('J',1,'Jumbo'),('J',1,'Jolly'),('J',1,'Jungle'),('J',1,'Jetpack'),('J',1,'Junkyard'),('J',1,'Jester'),('J',1,'Juicy'),
('K',1,'Kooky'),('K',1,'Kinetic'),('K',1,'King'),('K',1,'Ketchup'),('K',1,'Karate'),('K',1,'Kraken'),
('L',1,'Laser'),('L',1,'Loopy'),('L',1,'Lightning'),('L',1,'Lunar'),('L',1,'Lumpy'),('L',1,'Legend'),
('M',1,'Magic'),('M',1,'Mighty'),('M',1,'Mango'),('M',1,'Mystery'),('M',1,'Monster'),('M',1,'Moon'),('M',1,'Mad'),('M',1,'Muffin'),('M',1,'Magnetic'),
('N',1,'Nifty'),('N',1,'Neon'),('N',1,'Nutty'),('N',1,'Noble'),
('O',1,'Odd'),('O',1,'Orange'),
('P',1,'Pogo'),('P',1,'Pickle'),('P',1,'Plasma'),('P',1,'Purple'),
('Q',1,'Quick'),
('R',1,'Rad'),('R',1,'Robo'),('R',1,'Rainbow'),('R',1,'Rascal'),('R',1,'Rumble'),('R',1,'Rapid'),('R',1,'Royal'),
('S',1,'Sneaky'),('S',1,'Super'),('S',1,'Sparkle'),('S',1,'Spicy'),('S',1,'Speedy'),('S',1,'Squishy'),('S',1,'Solar'),('S',1,'Slippery'),('S',1,'Secret'),
('T',1,'Tiny'),('T',1,'Taco'),('T',1,'Thunder'),('T',1,'Twisty'),('T',1,'Tough'),
('U',1,'Unreal'),
('V',1,'Vortex'),('V',1,'Victory'),
('W',1,'Wild'),('W',1,'Wiggly'),('W',1,'Wizard'),('W',1,'Waffle'),
('X',1,'Xtreme'),
('Y',1,'Yellow'),
('Z',1,'Zany');

-- Expand position 2: second word, based on last-name initial.
INSERT OR IGNORE INTO nickname_words (letter, word_position, word) VALUES
('A',2,'Avenger'),('A',2,'Acrobat'),('A',2,'Alligator'),('A',2,'Artist'),
('B',2,'Bandit'),('B',2,'Builder'),('B',2,'Blob'),('B',2,'Burrito'),('B',2,'Beast'),('B',2,'Boomer'),('B',2,'Burger'),('B',2,'Bouncer'),('B',2,'Boss'),
('C',2,'Cookie'),('C',2,'Crab'),('C',2,'Champion'),('C',2,'Cactus'),('C',2,'Commander'),('C',2,'Clown'),('C',2,'Cyclone'),('C',2,'Cannon'),
('D',2,'Detective'),('D',2,'Donut'),('D',2,'Daredevil'),('D',2,'Drummer'),('D',2,'Dragon'),('D',2,'Doodle'),
('E',2,'Explorer'),('E',2,'Engineer'),('E',2,'Emperor'),
('F',2,'Falcon'),('F',2,'Frog'),('F',2,'Firecracker'),('F',2,'Fighter'),
('G',2,'Gator'),('G',2,'Gadget'),('G',2,'Ghost'),('G',2,'Genius'),('G',2,'Giant'),
('H',2,'Hero'),('H',2,'Hacker'),('H',2,'Hotdog'),('H',2,'Hurricane'),('H',2,'Hunter'),('H',2,'Hippo'),('H',2,'Howler'),
('I',2,'Inspector'),
('J',2,'Jellybean'),('J',2,'Joker'),('J',2,'Jet'),
('K',2,'King'),('K',2,'Knight'),('K',2,'Kid'),('K',2,'Kangaroo'),
('L',2,'Legend'),('L',2,'Lizard'),('L',2,'Laser'),('L',2,'Launcher'),('L',2,'Llama'),
('M',2,'Magician'),('M',2,'Monster'),('M',2,'Mastermind'),('M',2,'Monkey'),('M',2,'Meteor'),('M',2,'Muffin'),('M',2,'Mayor'),('M',2,'Mechanic'),('M',2,'Mantis'),
('N',2,'Navigator'),('N',2,'Noodle'),('N',2,'Nomad'),
('O',2,'Outlaw'),('O',2,'Operator'),('O',2,'Ogre'),
('P',2,'Pirate'),('P',2,'Professor'),('P',2,'Pancake'),('P',2,'Pilot'),('P',2,'Panda'),('P',2,'Phantom'),
('Q',2,'Queen'),
('R',2,'Ranger'),('R',2,'Racer'),('R',2,'Raptor'),('R',2,'Rookie'),('R',2,'Rocket'),('R',2,'Riddler'),
('S',2,'Sidekick'),('S',2,'Shark'),('S',2,'Samurai'),('S',2,'Sprinkler'),('S',2,'Sasquatch'),('S',2,'Squirrel'),('S',2,'Sheriff'),('S',2,'Sneaker'),('S',2,'Sorcerer'),
('T',2,'Tiger'),('T',2,'Trickster'),('T',2,'Turtle'),('T',2,'Taco'),('T',2,'Titan'),
('U',2,'Underdog'),
('V',2,'Villain'),('V',2,'Voyager'),
('W',2,'Wizard'),('W',2,'Wombat'),('W',2,'Winner'),('W',2,'Warrior'),('W',2,'Waffle'),('W',2,'Whiz'),('W',2,'Wanderer'),
('X',2,'Xplorer'),
('Y',2,'Yodeler'),('Y',2,'Yardbird'),
('Z',2,'Zapper');

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('006', 'expand_nickname_words');
