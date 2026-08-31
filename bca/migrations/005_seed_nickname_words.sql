PRAGMA foreign_keys = ON;

-- Position 1: first word, based on first-name initial.
INSERT OR IGNORE INTO nickname_words (letter, word_position, word) VALUES
('A', 1, 'Atomic'),
('B', 1, 'Bouncy'),
('C', 1, 'Cosmic'),
('D', 1, 'Dizzy'),
('E', 1, 'Electric'),
('F', 1, 'Funky'),
('G', 1, 'Glitter'),
('H', 1, 'Hyper'),
('I', 1, 'Icy'),
('J', 1, 'Jello'),
('K', 1, 'Kaboom'),
('L', 1, 'Lucky'),
('M', 1, 'Mega'),
('N', 1, 'Noodle'),
('O', 1, 'Orbit'),
('P', 1, 'Pixel'),
('Q', 1, 'Quantum'),
('R', 1, 'Rocket'),
('S', 1, 'Silly'),
('T', 1, 'Turbo'),
('U', 1, 'Ultra'),
('V', 1, 'Velcro'),
('W', 1, 'Wacky'),
('X', 1, 'X-Ray'),
('Y', 1, 'Yodel'),
('Z', 1, 'Zippy');

-- Position 2: second word, based on last-name initial.
INSERT OR IGNORE INTO nickname_words (letter, word_position, word) VALUES
('A', 2, 'Astronaut'),
('B', 2, 'Banana'),
('C', 2, 'Captain'),
('D', 2, 'Dinosaur'),
('E', 2, 'Eagle'),
('F', 2, 'Fireball'),
('G', 2, 'Goblin'),
('H', 2, 'Hamster'),
('I', 2, 'Inventor'),
('J', 2, 'Juggler'),
('K', 2, 'Koala'),
('L', 2, 'Lobster'),
('M', 2, 'Machine'),
('N', 2, 'Ninja'),
('O', 2, 'Octopus'),
('P', 2, 'Penguin'),
('Q', 2, 'Quarterback'),
('R', 2, 'Robot'),
('S', 2, 'Scientist'),
('T', 2, 'Tornado'),
('U', 2, 'Unicorn'),
('V', 2, 'Viking'),
('W', 2, 'Waiter'),
('X', 2, 'Xylophone'),
('Y', 2, 'Yeti'),
('Z', 2, 'Zombie');

INSERT OR IGNORE INTO schema_migrations (version, name)
VALUES ('005', 'seed_nickname_words');
