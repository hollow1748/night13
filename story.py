"""Original hotel story data. Stable identifiers keep old saves compatible."""
ROLES = {
 'clerk': dict(name='Night Clerk', skill='Room Register', uses=3,
   ability='Mark this floor\'s residents and evidence for 10 seconds. Each use adds 5 seconds to the run clock.',
   task='Read the handover book on Floor 1 and collect all six testimonies.',
   warning='There are only six residents. Never sign the seventh line.'),
 'mechanic': dict(name='Maintenance Worker', skill='Barricade', uses=2,
   ability='Stand beside a guest-room doorway to seal it for 10 seconds. It blocks you as well as the pursuers.',
   task='Take the toolbox on Floor 2, then repair the power box on Floor 3.',
   warning='The elevator has more than a wiring fault. Someone keeps holding the door shut.'),
 'amnesiac': dict(name='Amnesiac Guest', skill='Memory Echo', uses=3,
   ability='Read one undiscovered clue within three tiles. Your sight shrinks for the next 10 seconds.',
   task='Find your own old photograph on Floor 3.',
   warning='If someone calls your name, first make sure it is not your own voice.'),
}
RESIDENTS = {
 'mother': dict(floor=1,room='101',name='Lin Wan · The Mother',pos=(5,3),evidence=(8,4),item='Faded Family Photograph',
   intro='Three places are set at a table. The food has long gone cold.\n"My two children are not back yet. The manager says they will find me if I keep renewing my stay."',
   proof='A mother holds hands with two children. On the back:\n"Mum, we have grown up. Stop waiting for the rain to end."\nThe date is thirty years old. Three seats, one for the living; two remain for those she awaits.',
   resolution='She remembers that her children left long ago.\n"Three places, but only one for the living. The others are for the ones I wait for."\nShe puts away two sets of cutlery. She will never hunt you.',
   clue='Floor 1: three seats minus one seat for the living.'),
 'elder': dict(floor=1,room='102',name='Mr Zhou · The Letter Writer',pos=(20,3),evidence=(17,4),item='Two Returned Letters',
   intro='He copies the same address again and again.\n"I promised to post letters for the two children next door. Every morning, the letters are back in my drawer."',
   proof='There are only two original letters. Everything else is a copy ordered by the manager.\nBoth are addressed to Lin Wan in Room 101. A red stamp covers the postmark:\n"Posting constitutes checkout. Request denied."',
   resolution='He offers you the originals.\n"She waits for two children. Do not count the copies. Count the letters that never arrived."\nFor a moment, his hands stop shaking.',
   clue='Floor 1 confirmation: two original letters, not the copies.'),
 'bride': dict(floor=2,room='201',name='Xu Qing · The Bride',pos=(5,3),evidence=(8,4),item='Candles and Wedding Invoice',
   intro='A wedding dress lies across the bed. She lights the candles one by one.\n"The ceremony should have begun. The manager says no one may leave until every flame is out."',
   proof='The invoice lists seven candles. Two have burned away.\nOn the reverse:\n"Do not count the ashes. The lights still waiting are the number this room remembers."',
   resolution='She brushes away the ashes, leaving five small flames.\n"I was not waiting for him. I simply could not end the wedding."\nShe removes her veil and stops mistaking visitors for the groom.',
   clue='Floor 2: seven wedding candles minus two burned out.'),
 'actor': dict(floor=2,room='202',name='Shen Yan · The Actor',pos=(20,3),evidence=(17,4),item='Five Defaced Stage Photographs',
   intro='He faces away from the mirror, repeating a single line.\n"The manager says he will return my face if I perform one more time."',
   proof='Five stage photographs. A face has been blacked out in every one.\nRed writing on the back: "Floor 2 code digit: the number of remaining performances."\nThe seventh and second shows were cancelled. Five remain.\nScratched below: "Do not let him see his face."',
   resolution='You hand him the photographs. His signatures prove who he is.\nHe sees the erased faces and grabs your wrist.\n"You think I have no face? You are laughing at me too!"\nHe tears the pictures towards the mirror. Five surviving performances are visible among the scraps.',
   clue='Floor 2 confirmation: five photographs and five remaining shows.'),
 'doctor': dict(floor=3,room='301',name='Dr Gu · The Night Doctor',pos=(5,3),evidence=(8,4),item='Thirteen Bed Cards',
   intro='The doctor refuses to leave the corridor.\n"Thirteen bed cards, but the manager changes the list every day. I can never find everyone I must take home."',
   proof='Of thirteen bed cards, six have no names, only the manager\'s stamp.\nThe remaining seven bear their owners\' handwriting. The last says:\n"Those who never checked in must not be registered."',
   resolution='You point out the six blank cards: empty beds invented by the manager.\n"Thirteen minus six... My shift can finally end."\nHe lowers his stethoscope and stops looking for new patients.',
   clue='Floor 3: thirteen cards minus six nameless cards.'),
 'child': dict(floor=3,room='302',name='Little Seven · The Child',pos=(20,3),evidence=(17,4),item='Drawing of the Floor Order',
   intro='The child presses an ear to the carpet.\n"They call me Seven, but I never stayed here. You should not stay either."',
   proof='A house with three floors. An arrow climbs from the bottom to the top.\n"First, the waiting downstairs. Then the farewell in the middle. Last, the names at the top."\nBelow: "Give back the six names. Never sign the seventh line."',
   resolution='The child traces the stairs.\n"Put the digits in order: Floor 1, Floor 2, Floor 3. The manager survives because we remember his rules."\n"Do not burn the names. Read the six real names aloud."',
   clue='Order: Floor 1 -> Floor 2 -> Floor 3. Restore the names and refuse to register a seventh guest.'),
}
RULES=('1. Three floors. Two residents on each floor.\n'
       '2. Inspect evidence, then show it to the resident for their story and code clues.\n'
       '3. Floor 1 is safe at first. Give Shen Yan his photographs and he will hunt you across floors.\n'
       '4. Reading, dialogue, the journal and menus pause the pursuit.\n'
       '5. Press E near the stairs at either end of a corridor to change floors.\n'
       '6. Complete your role mission and collect six testimonies before confronting the manager.\n'
       '7. Choose correctly: everyone except the mother will hunt you. Escape by elevator.\n\n'
       'E: interact / Q: skill / F: match / J: journal / B: inventory')
